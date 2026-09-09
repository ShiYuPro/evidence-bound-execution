# Run format

The gate owns five JSON files inside one run directory. Paths in `deliverables.json` are resolved relative to that directory unless absolute.

## `contract.json`

```json
{
  "schema_version": 1,
  "task_id": "sample-task",
  "goal": "The outcome the user will judge",
  "producer": "codex-main",
  "required_evidence": [{
    "id": "sample-001",
    "source": "A stable file path, URL, note ID, or record ID",
    "why_required": "Why this source constrains production",
    "required_elements": ["title mechanism", "page order"]
  }],
  "requirements": [{
    "id": "req-structure",
    "text": "Preserve the observed page order",
    "required": true
  }],
  "forbidden_substitutions": [{
    "id": "no-proxy",
    "text": "Responsive layout does not prove content attractiveness"
  }],
  "acceptance_checks": [{
    "id": "accept-structure",
    "text": "A reviewer can trace the output page order to the named sample",
    "required_evidence_kinds": ["sample_mapping", "independent_review"]
  }],
  "material_change": {
    "required": true,
    "dimensions": ["title mechanism", "page order"]
  }
}
```

Use stable, concrete evidence IDs. `required_elements` must describe observable parts of the source, not abstract praise such as “good style.”

## `mapping.json`

`contract_revision` must equal the current lock revision.

```json
{
  "contract_revision": 1,
  "mappings": [{
    "requirement_id": "req-structure",
    "evidence_ids": ["sample-001"],
    "preserved_elements": ["question first, explanation second"],
    "output_locations": ["draft.md sections 1-2"],
    "status": "mapped"
  }],
  "experiments": [{
    "id": "exp-001",
    "description": "An unsupported optional variation",
    "reason": "Why it is being tried",
    "risk": "What could fail"
  }]
}
```

Each required evidence item must appear in at least one mapping. Experiments cannot be used as evidence IDs.

## `deliverables.json`

```json
{
  "contract_revision": 1,
  "artifacts": [{
    "id": "draft",
    "path": "artifacts/draft.md",
    "description": "Final draft",
    "status": "ready"
  }],
  "rejected_version_comparison": {
    "status": "materially_changed",
    "changes": [{
      "dimension": "page order",
      "evidence": "Old 1-2-3 became sample-backed 1-3-2"
    }]
  }
}
```

When `material_change.required` is false, the comparison may use `{"status":"not_required","changes":[]}`.

## `verification.json`

```json
{
  "contract_revision": 1,
  "acceptance_results": [{
    "acceptance_id": "accept-structure",
    "evidence_kind": "sample_mapping",
    "status": "pass",
    "evidence": "Mapping row and artifact locations checked"
  }, {
    "acceptance_id": "accept-structure",
    "evidence_kind": "independent_review",
    "status": "pass",
    "evidence": "Reviewer traced both sections to sample-001"
  }],
  "forbidden_substitution_results": [{
    "forbidden_id": "no-proxy",
    "status": "pass",
    "evidence": "Attractiveness was not inferred from layout checks"
  }],
  "independent_review": {
    "reviewer": "user-or-independent-reviewer",
    "status": "pass",
    "findings": ["The required structure is visibly present"]
  },
  "outcome_status": "pass"
}
```

The independent reviewer name must differ from `contract.json`'s `producer`.

## Generated gate files

- `gate-lock.json`: current contract revision and hash.
- `locks/contract-rN.json`: contract snapshots for auditing revisions.
- `gate-status.json`: latest pass/fail details.
- `gate-pass.json`: created only when the requested phase passes. A failed or stale check removes it.

Do not edit generated gate files by hand.
