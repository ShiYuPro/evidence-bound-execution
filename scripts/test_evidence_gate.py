#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


GATE = Path(__file__).with_name("evidence_gate.py")


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name) / "run"
        result = self.call("init", str(self.run_dir), "--task-id", "xhs-rework", "--goal", "Produce a sample-backed post")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write("contract.json", self.valid_contract())

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args):
        return subprocess.run(
            [sys.executable, str(GATE), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def read(self, name):
        return json.loads((self.run_dir / name).read_text(encoding="utf-8"))

    def write(self, name, value):
        path = self.run_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def valid_contract():
        return {
            "schema_version": 1,
            "task_id": "xhs-rework",
            "goal": "Produce a sample-backed post",
            "producer": "codex-main",
            "required_evidence": [{
                "id": "note-001",
                "source": "sample-library/note-001.md",
                "why_required": "The user required a concrete high-performing source",
                "required_elements": ["title mechanism", "page order"],
            }],
            "requirements": [{
                "id": "req-structure",
                "text": "Preserve title mechanism and page order",
                "required": True,
            }],
            "forbidden_substitutions": [{
                "id": "no-layout-proxy",
                "text": "No-overflow checks do not prove attractiveness",
            }],
            "acceptance_checks": [{
                "id": "accept-structure",
                "text": "The draft is traceable to note-001",
                "required_evidence_kinds": ["sample_mapping", "independent_review"],
            }],
            "material_change": {
                "required": True,
                "dimensions": ["title mechanism", "page order"],
            },
        }

    @staticmethod
    def valid_mapping(revision=1):
        return {
            "contract_revision": revision,
            "mappings": [{
                "requirement_id": "req-structure",
                "evidence_ids": ["note-001"],
                "preserved_elements": ["question title", "problem then explanation"],
                "output_locations": ["artifacts/draft.md title and sections 1-2"],
                "status": "mapped",
            }],
            "experiments": [],
        }

    @staticmethod
    def valid_deliverables(revision=1):
        return {
            "contract_revision": revision,
            "artifacts": [{
                "id": "draft",
                "path": "artifacts/draft.md",
                "description": "Final sample-backed draft",
                "status": "ready",
            }],
            "rejected_version_comparison": {
                "status": "materially_changed",
                "changes": [
                    {"dimension": "title mechanism", "evidence": "Generic claim replaced with the sample's question mechanism"},
                    {"dimension": "page order", "evidence": "Feature-first order replaced with problem then explanation"},
                ],
            },
        }

    @staticmethod
    def valid_verification(revision=1):
        return {
            "contract_revision": revision,
            "acceptance_results": [
                {
                    "acceptance_id": "accept-structure",
                    "evidence_kind": "sample_mapping",
                    "status": "pass",
                    "evidence": "Mapped title and page order were found in the artifact",
                },
                {
                    "acceptance_id": "accept-structure",
                    "evidence_kind": "independent_review",
                    "status": "pass",
                    "evidence": "Reviewer traced both required elements to note-001",
                },
            ],
            "forbidden_substitution_results": [{
                "forbidden_id": "no-layout-proxy",
                "status": "pass",
                "evidence": "The acceptance decision used mapping and review, not layout tests",
            }],
            "independent_review": {
                "reviewer": "reviewer-02",
                "status": "pass",
                "findings": ["Both material-change dimensions are visible"],
            },
            "outcome_status": "pass",
        }

    def lock_and_prepare_valid_run(self):
        result = self.call("lock", str(self.run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write("mapping.json", self.valid_mapping())
        artifact = self.run_dir / "artifacts" / "draft.md"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("Question title\n\nProblem, then explanation.\n", encoding="utf-8")
        self.write("deliverables.json", self.valid_deliverables())
        self.write("verification.json", self.valid_verification())

    def test_valid_run_passes_both_gates(self):
        self.lock_and_prepare_valid_run()
        pre = self.call("check", str(self.run_dir), "--phase", "preproduction")
        delivery = self.call("check", str(self.run_dir), "--phase", "delivery")
        self.assertEqual(pre.returncode, 0, pre.stderr)
        self.assertEqual(delivery.returncode, 0, delivery.stderr)
        self.assertTrue((self.run_dir / "gate-pass.json").exists())

    def test_missing_sample_mapping_is_blocked(self):
        self.assertEqual(self.call("lock", str(self.run_dir)).returncode, 0)
        self.write("mapping.json", {"contract_revision": 1, "mappings": [], "experiments": []})
        result = self.call("check", str(self.run_dir), "--phase", "preproduction")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unused required evidence", result.stderr)
        self.assertFalse((self.run_dir / "gate-pass.json").exists())

    def test_silent_contract_change_is_blocked(self):
        self.lock_and_prepare_valid_run()
        contract = self.read("contract.json")
        contract["goal"] = "A silently reframed goal"
        self.write("contract.json", contract)
        result = self.call("check", str(self.run_dir), "--phase", "preproduction")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed after lock", result.stderr)

    def test_user_correction_makes_old_mapping_stale(self):
        self.lock_and_prepare_valid_run()
        contract = self.read("contract.json")
        contract["requirements"][0]["text"] = "User correction: preserve exact five-page order"
        self.write("contract.json", contract)
        self.assertEqual(self.call("lock", str(self.run_dir)).returncode, 0)
        result = self.call("check", str(self.run_dir), "--phase", "preproduction")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mapping.json is stale", result.stderr)

    def test_proxy_evidence_kind_cannot_replace_required_kind(self):
        self.lock_and_prepare_valid_run()
        verification = self.valid_verification()
        verification["acceptance_results"] = [{
            "acceptance_id": "accept-structure",
            "evidence_kind": "responsive_layout",
            "status": "pass",
            "evidence": "No overflow at three sizes",
        }]
        self.write("verification.json", verification)
        result = self.call("check", str(self.run_dir), "--phase", "delivery")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("accept-structure/sample_mapping", result.stderr)
        self.assertIn("accept-structure/independent_review", result.stderr)

    def test_producer_cannot_self_certify(self):
        self.lock_and_prepare_valid_run()
        verification = self.valid_verification()
        verification["independent_review"]["reviewer"] = "codex-main"
        self.write("verification.json", verification)
        result = self.call("check", str(self.run_dir), "--phase", "delivery")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("differ from the producer", result.stderr)


if __name__ == "__main__":
    unittest.main()
