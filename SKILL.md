---
name: evidence-bound-execution
description: Use when creating or revising an artifact, product, or implementation that must carry prior diagnosis, user corrections, named examples, research, benchmarks, or non-negotiable acceptance conditions into the actual output, especially after a rejected iteration. Converts judgment into observable execution constraints and blocks unsupported outcome claims. Skip simple factual answers and purely mechanical edits with no qualitative or evidence constraint.
---

# Evidence-Bound Execution

Turn user requirements and source evidence into delivery gates that cannot be replaced by explanations, proxy tests, or the producer's own confidence.

Read [a first-use example](references/example.md) when adopting this workflow.

## Non-negotiable rule

Reading, summarizing, citing, planning around, or remembering evidence does not count as using it. A required source is used only when its required elements are mapped to identifiable locations in the output and the matching acceptance evidence passes.

Do not claim completion from a passing build, test suite, responsive layout, polished UI, research report, or architecture unless that is the outcome the contract actually requires. Each check proves only its own layer.

## Choose the light or full gate

Use the light gate for ordinary UI, copy, product, code, or artifact revisions where the main risk is losing the current diagnosis during execution. Before the first write, state a compact execution card in commentary:

- the outcome the user will judge;
- 2–5 observable output conditions derived from the current diagnosis or correction;
- forbidden shortcuts or proxy substitutions that would repeat the failure;
- the actual artifact, render, user path, data, or reviewer evidence that can verify each condition.

This is not a plan and must not become a long restatement of the conversation. Each major edit must address a card condition. Re-read the card when the strategy changes and immediately before delivery. If a local tweak cannot satisfy the diagnosis, change the problem layer instead of oscillating between nearby parameter values. Two failures against the same condition require a layer change or a blocked report, not a third near-duplicate.

Use the full gate only when traceability is itself a requested deliverable, many evidence mappings must survive across turns, or the cost of a wrong artifact is materially high. A named reference, correction, or rejected iteration alone uses the light gate; material change must still be demonstrated at the required outcome layer.

## Momentum guard

Evidence gates steer execution; they do not justify delaying a low-risk opportunity until the process is perfect.

- Classify consequence before ceremony. New opportunities, prototypes, local drafts, reversible experiments, market tests, and work that has remained without results should normally use the light gate and move into production in the same work batch.
- A prior correction or rejected attempt alone does not require the full gate. Use the full gate only when traceability itself is part of the deliverable, many evidence mappings must survive across turns, or the cost of a wrong artifact is materially high.
- Under urgency, frustration, or a time-sensitive opportunity, compress the execution card to the few conditions that change the outcome and immediately perform the next concrete action. Do not add optional research, alternative frameworks, or proxy checks before the core attempt.
- Do not turn every uncertainty into a required input. If a reversible action can cheaply reveal the answer, run it. Stop only for a missing fact or authority that materially changes the result, or for a production, financial, privacy, permission, destructive, public, or irreversible transition.
- If the user supplies a workable tool, draft, workaround, or path, use it unless evidence shows it cannot meet a locked outcome condition. Imperfect but informative execution is valid in exploration; polish and hardening follow proof.
- Analysis, critique, documentation, new rules, and new Skills cannot satisfy an output condition unless the user explicitly asked for those artifacts. For build or change requests, the gate must culminate in the requested artifact or real user path.

## Full gate

Create a run folder at `.evidence-bound/<task-id>/` in the current project. Read [references/run-format.md](references/run-format.md) before editing run files or interpreting a gate failure.

Use `scripts/evidence_gate.py` rather than recreating the gate logic. The required sequence is:

1. Initialize the run and fill `contract.json` with the user's goal, named evidence, required output conditions, forbidden substitutions, and outcome-level acceptance checks.
2. Lock the contract. A new user correction supersedes conflicting plans or model preferences: update the contract and lock a new revision. Previous mappings and reviews then become stale automatically.
3. Before production, fill `mapping.json` and run the `preproduction` gate. Do not produce the final artifact until it passes.
4. Produce only within the locked contract. If the evidence cannot support a required condition, stop as `blocked`; do not improvise a substitute and call it evidence-based.
5. Fill `deliverables.json` and `verification.json`, then run the `delivery` gate. Do not say “complete” unless `gate-pass.json` exists for the current contract revision.

Typical commands:

```bash
python3 <skill-dir>/scripts/evidence_gate.py init .evidence-bound/<task-id> --task-id <task-id> --goal "<goal>"
python3 <skill-dir>/scripts/evidence_gate.py lock .evidence-bound/<task-id>
python3 <skill-dir>/scripts/evidence_gate.py check .evidence-bound/<task-id> --phase preproduction
python3 <skill-dir>/scripts/evidence_gate.py check .evidence-bound/<task-id> --phase delivery
```

## Contract rules

- Explicit user corrections outrank earlier plans, memories, examples, and model theory. Never silently reinterpret or retire a locked condition.
- Record specific evidence identifiers and required elements. “Market examples,” “the 400 posts,” or “best practices” is not specific enough for production.
- Record forbidden substitutions such as “layout tests do not prove attractiveness” or “an architecture report does not prove the agent completes a real task.”
- Acceptance checks must name the evidence kinds that can prove them. A check cannot pass with a different evidence kind.
- When revising a rejected output, require material-change dimensions. Rewording, recoloring, added cards, or added infrastructure cannot satisfy a structural change unless explicitly allowed.

## Mapping rules

Every required condition needs:

- one or more valid evidence IDs;
- the exact elements being preserved or applied;
- planned output locations that a reviewer can find;
- a `mapped` status.

Anything without evidence must be labeled as an experiment with its reason and risk. An experiment cannot satisfy a required condition.

## Verification rules

Use deterministic checks for measurable properties and outcome-level review for qualitative properties. Keep them separate. Associate a result with the artifact revision, environment, command or reviewer, and observed output it actually checked. Recheck after changes invalidate it; a fresh timestamp without matching inputs is not stronger evidence. Preserve still-valid evidence rather than rerunning unrelated checks merely to make a completion statement.

The producer cannot be the independent reviewer. When a separate reviewer is unavailable, leave the independent review blocked and report that boundary; do not self-review under a different label. User judgment can serve as the independent review when the user actually reviews the artifact.

For a rejected prior version, verification must show material changes in every locked dimension. If two attempts fail for the same missing constraint, stop and identify the missing mapping or evidence instead of producing another near-duplicate.

## Delivery language

Report the current gate state:

- `preproduction passed`: evidence is mapped; no outcome claim yet.
- `delivery passed`: all locked outcome checks passed for the current revision.
- `blocked`: state the exact failed condition and missing authority, evidence, or artifact.

Never upgrade `preproduction passed`, automated tests, or a producer review into “completed.”
