#!/usr/bin/env python3
"""Deterministic gate for evidence-bound production runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing file: {path.name}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def ids(items: Any, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        errors.append(f"{label} must be an array")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not nonempty(item.get("id")):
            errors.append(f"{label}[{index}] needs a non-empty id")
            continue
        item_id = item["id"]
        if item_id in result:
            errors.append(f"duplicate {label} id: {item_id}")
        result[item_id] = item
    return result


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    for field in ("task_id", "goal", "producer"):
        if not nonempty(contract.get(field)):
            errors.append(f"contract.{field} must be non-empty")

    evidence = ids(contract.get("required_evidence"), "required_evidence", errors)
    requirements = ids(contract.get("requirements"), "requirements", errors)
    ids(contract.get("forbidden_substitutions", []), "forbidden_substitutions", errors)
    acceptance = ids(contract.get("acceptance_checks"), "acceptance_checks", errors)
    if not evidence:
        errors.append("at least one required_evidence item is required")
    if not requirements:
        errors.append("at least one requirement is required")
    if not acceptance:
        errors.append("at least one acceptance_check is required")

    for item_id, item in evidence.items():
        if not nonempty(item.get("source")) or not nonempty(item.get("why_required")):
            errors.append(f"required_evidence {item_id} needs source and why_required")
        elements = item.get("required_elements")
        if not isinstance(elements, list) or not all(nonempty(v) for v in elements) or not elements:
            errors.append(f"required_evidence {item_id} needs required_elements")
    for item_id, item in requirements.items():
        if not nonempty(item.get("text")):
            errors.append(f"requirement {item_id} needs text")
    for item_id, item in acceptance.items():
        kinds = item.get("required_evidence_kinds")
        if not nonempty(item.get("text")):
            errors.append(f"acceptance_check {item_id} needs text")
        if not isinstance(kinds, list) or not kinds or not all(nonempty(v) for v in kinds):
            errors.append(f"acceptance_check {item_id} needs required_evidence_kinds")

    change = contract.get("material_change", {"required": False, "dimensions": []})
    if not isinstance(change, dict) or not isinstance(change.get("required"), bool):
        errors.append("material_change needs a boolean required field")
    elif change.get("required"):
        dimensions = change.get("dimensions")
        if not isinstance(dimensions, list) or not dimensions or not all(nonempty(v) for v in dimensions):
            errors.append("material_change.dimensions is required when material change is required")
    return errors


def load_locked(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    contract = read_json(run_dir / "contract.json")
    lock = read_json(run_dir / "gate-lock.json")
    errors.extend(validate_contract(contract))
    if lock.get("contract_hash") != canonical_hash(contract):
        errors.append("contract changed after lock; lock a new revision before continuing")
    if not isinstance(lock.get("revision"), int) or lock.get("revision", 0) < 1:
        errors.append("gate-lock.json has no valid revision")
    return contract, lock, errors


def check_preproduction(run_dir: Path, contract: dict[str, Any], revision: int) -> list[str]:
    errors: list[str] = []
    mapping = read_json(run_dir / "mapping.json")
    if mapping.get("contract_revision") != revision:
        errors.append("mapping.json is stale for the current contract revision")

    evidence = ids(contract.get("required_evidence"), "required_evidence", errors)
    requirements = {
        key: value for key, value in ids(contract.get("requirements"), "requirements", errors).items()
        if value.get("required", True)
    }
    rows = mapping.get("mappings")
    if not isinstance(rows, list):
        return errors + ["mapping.mappings must be an array"]

    mapped_requirements: set[str] = set()
    used_evidence: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"mapping row {index} must be an object")
            continue
        requirement_id = row.get("requirement_id")
        if requirement_id not in requirements:
            errors.append(f"mapping row {index} has unknown or optional requirement_id: {requirement_id}")
        else:
            mapped_requirements.add(requirement_id)
        evidence_ids = row.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            errors.append(f"mapping row {index} needs evidence_ids")
        else:
            for evidence_id in evidence_ids:
                if evidence_id not in evidence:
                    errors.append(f"mapping row {index} uses unknown evidence_id: {evidence_id}")
                else:
                    used_evidence.add(evidence_id)
        for field in ("preserved_elements", "output_locations"):
            value = row.get(field)
            if not isinstance(value, list) or not value or not all(nonempty(v) for v in value):
                errors.append(f"mapping row {index} needs non-empty {field}")
        if row.get("status") != "mapped":
            errors.append(f"mapping row {index} status must be mapped")

    missing_requirements = sorted(set(requirements) - mapped_requirements)
    missing_evidence = sorted(set(evidence) - used_evidence)
    if missing_requirements:
        errors.append("unmapped required requirements: " + ", ".join(missing_requirements))
    if missing_evidence:
        errors.append("unused required evidence: " + ", ".join(missing_evidence))

    experiments = mapping.get("experiments", [])
    if not isinstance(experiments, list):
        errors.append("mapping.experiments must be an array")
    else:
        for index, experiment in enumerate(experiments):
            fields = ("id", "description", "reason", "risk")
            if not isinstance(experiment, dict) or not all(nonempty(experiment.get(k)) for k in fields):
                errors.append(f"experiment {index} needs id, description, reason, and risk")
    return errors


def check_delivery(run_dir: Path, contract: dict[str, Any], revision: int) -> list[str]:
    errors = check_preproduction(run_dir, contract, revision)
    deliverables = read_json(run_dir / "deliverables.json")
    verification = read_json(run_dir / "verification.json")
    if deliverables.get("contract_revision") != revision:
        errors.append("deliverables.json is stale for the current contract revision")
    if verification.get("contract_revision") != revision:
        errors.append("verification.json is stale for the current contract revision")

    artifacts = deliverables.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("deliverables.artifacts needs at least one artifact")
    else:
        for index, artifact in enumerate(artifacts):
            fields = ("id", "path", "description")
            if not isinstance(artifact, dict) or not all(nonempty(artifact.get(k)) for k in fields):
                errors.append(f"artifact {index} needs id, path, and description")
                continue
            if artifact.get("status") != "ready":
                errors.append(f"artifact {artifact.get('id', index)} status must be ready")
            path = Path(artifact["path"])
            if not path.is_absolute():
                path = run_dir / path
            if not path.exists() or not path.is_file():
                errors.append(f"artifact does not exist: {artifact['path']}")

    change = contract.get("material_change", {"required": False, "dimensions": []})
    comparison = deliverables.get("rejected_version_comparison", {})
    if change.get("required"):
        if comparison.get("status") != "materially_changed":
            errors.append("rejected version comparison must be materially_changed")
        changes = comparison.get("changes")
        covered: set[str] = set()
        if isinstance(changes, list):
            for item in changes:
                if isinstance(item, dict) and nonempty(item.get("dimension")) and nonempty(item.get("evidence")):
                    covered.add(item["dimension"])
        missing = sorted(set(change.get("dimensions", [])) - covered)
        if missing:
            errors.append("material-change dimensions without evidence: " + ", ".join(missing))

    acceptance = ids(contract.get("acceptance_checks"), "acceptance_checks", errors)
    results = verification.get("acceptance_results")
    passed_pairs: set[tuple[str, str]] = set()
    if not isinstance(results, list):
        errors.append("verification.acceptance_results must be an array")
    else:
        for index, result in enumerate(results):
            if not isinstance(result, dict):
                errors.append(f"acceptance result {index} must be an object")
                continue
            pair = (result.get("acceptance_id"), result.get("evidence_kind"))
            if pair[0] not in acceptance:
                errors.append(f"acceptance result {index} has unknown acceptance_id: {pair[0]}")
            if result.get("status") == "pass" and nonempty(result.get("evidence")):
                passed_pairs.add(pair)
            else:
                errors.append(f"acceptance result {index} must pass with evidence")
    for acceptance_id, item in acceptance.items():
        for kind in item.get("required_evidence_kinds", []):
            if (acceptance_id, kind) not in passed_pairs:
                errors.append(f"missing passing acceptance evidence: {acceptance_id}/{kind}")

    forbidden = ids(contract.get("forbidden_substitutions", []), "forbidden_substitutions", errors)
    forbidden_results = verification.get("forbidden_substitution_results", [])
    passed_forbidden: set[str] = set()
    if not isinstance(forbidden_results, list):
        errors.append("verification.forbidden_substitution_results must be an array")
    else:
        for index, result in enumerate(forbidden_results):
            if not isinstance(result, dict) or result.get("forbidden_id") not in forbidden:
                errors.append(f"forbidden substitution result {index} has an unknown forbidden_id")
            elif result.get("status") == "pass" and nonempty(result.get("evidence")):
                passed_forbidden.add(result["forbidden_id"])
            else:
                errors.append(f"forbidden substitution result {index} must pass with evidence")
    missing_forbidden = sorted(set(forbidden) - passed_forbidden)
    if missing_forbidden:
        errors.append("missing forbidden-substitution checks: " + ", ".join(missing_forbidden))

    review = verification.get("independent_review")
    if not isinstance(review, dict):
        errors.append("verification.independent_review is required")
    else:
        if review.get("status") != "pass":
            errors.append("independent review has not passed")
        if not nonempty(review.get("reviewer")) or review.get("reviewer") == contract.get("producer"):
            errors.append("independent reviewer must be named and differ from the producer")
        findings = review.get("findings")
        if not isinstance(findings, list) or not findings or not all(nonempty(v) for v in findings):
            errors.append("independent review needs non-empty findings")
    if verification.get("outcome_status") != "pass":
        errors.append("verification.outcome_status must be pass")
    return errors


def scaffold(task_id: str, goal: str) -> dict[str, dict[str, Any]]:
    return {
        "contract.json": {
            "schema_version": SCHEMA_VERSION,
            "task_id": task_id,
            "goal": goal,
            "producer": "codex-main",
            "required_evidence": [],
            "requirements": [],
            "forbidden_substitutions": [],
            "acceptance_checks": [],
            "material_change": {"required": False, "dimensions": []},
        },
        "mapping.json": {"contract_revision": 0, "mappings": [], "experiments": []},
        "deliverables.json": {
            "contract_revision": 0,
            "artifacts": [],
            "rejected_version_comparison": {"status": "not_required", "changes": []},
        },
        "verification.json": {
            "contract_revision": 0,
            "acceptance_results": [],
            "forbidden_substitution_results": [],
            "independent_review": {"reviewer": "", "status": "blocked", "findings": []},
            "outcome_status": "blocked",
        },
    }


def command_init(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    files = scaffold(args.task_id, args.goal)
    existing = [name for name in files if (run_dir / name).exists()]
    if existing:
        print("BLOCKED existing run files: " + ", ".join(existing), file=sys.stderr)
        return 2
    for name, value in files.items():
        write_json(run_dir / name, value)
    print(f"INITIALIZED {run_dir}")
    return 0


def command_lock(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    try:
        contract = read_json(run_dir / "contract.json")
        errors = validate_contract(contract)
    except ValueError as exc:
        errors = [str(exc)]
        contract = {}
    if errors:
        print("BLOCKED contract cannot be locked", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    lock_path = run_dir / "gate-lock.json"
    revision = 1
    if lock_path.exists():
        try:
            revision = int(read_json(lock_path).get("revision", 0)) + 1
        except ValueError:
            revision = 1
    lock = {
        "schema_version": SCHEMA_VERSION,
        "revision": revision,
        "contract_hash": canonical_hash(contract),
        "locked_at": now(),
    }
    write_json(lock_path, lock)
    write_json(run_dir / "locks" / f"contract-r{revision}.json", contract)
    for stale in ("gate-pass.json", "gate-status.json"):
        path = run_dir / stale
        if path.exists():
            path.unlink()
    print(f"LOCKED revision {revision} {lock['contract_hash']}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve()
    pass_path = run_dir / "gate-pass.json"
    if pass_path.exists():
        pass_path.unlink()
    try:
        contract, lock, errors = load_locked(run_dir)
        if not errors:
            checker = check_preproduction if args.phase == "preproduction" else check_delivery
            errors.extend(checker(run_dir, contract, lock["revision"]))
    except ValueError as exc:
        lock, errors = {}, [str(exc)]
    status = {
        "schema_version": SCHEMA_VERSION,
        "phase": args.phase,
        "status": "fail" if errors else "pass",
        "contract_revision": lock.get("revision"),
        "contract_hash": lock.get("contract_hash"),
        "checked_at": now(),
        "errors": errors,
    }
    write_json(run_dir / "gate-status.json", status)
    if errors:
        print(f"BLOCKED {args.phase}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    write_json(pass_path, status)
    print(f"PASSED {args.phase} revision {lock['revision']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Lock evidence and block unsupported delivery claims.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("run_dir")
    init_parser.add_argument("--task-id", required=True)
    init_parser.add_argument("--goal", required=True)
    init_parser.set_defaults(func=command_init)
    lock_parser = subparsers.add_parser("lock")
    lock_parser.add_argument("run_dir")
    lock_parser.set_defaults(func=command_lock)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("run_dir")
    check_parser.add_argument("--phase", required=True, choices=("preproduction", "delivery"))
    check_parser.set_defaults(func=command_check)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
