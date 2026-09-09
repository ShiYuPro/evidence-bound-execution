# A light-gate example

User request: “The mobile purchase button is hidden until I scroll. Keep it visible
at 390 px wide, without covering the terms or changing the price.”

Before editing, state three observable conditions: button visible initially at the
requested viewport, terms accessible and unobscured, displayed price unchanged.
Use the actual rendered page and purchase interaction as evidence. A passing build
only proves compilation. Do not create full-gate JSON files for this small change.

For a full traceability workflow, `python3 scripts/evidence_gate.py --help` lists
commands; [run-format.md](run-format.md) defines the actual JSON contract.
The script validates recorded mappings and evidence types, not whether a screenshot
or a review claim is truthful. An independent reviewer is required only when the
chosen contract requires one; never impersonate a reviewer to pass a gate.
