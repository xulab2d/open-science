# Candidate Self-Improvement Archive

Purpose:
- Preserve candidate changes, lineage, eval evidence, and promotion/rejection decisions.
- Prevent durable memory, skill, graph, or retrieval-policy edits from being treated as unmeasured self-edits.

Workflow:
1. Create a candidate with `python3 -m lab_assistant.runtime.mutation propose --name <name> --from-trajectory <id>`.
2. Run evals and attach results with `python3 -m lab_assistant.runtime.mutation validate --candidate <id> --suite all`.
3. Promote or reject with an explicit reason using `python3 -m lab_assistant.runtime.mutation decide`.

Archive directories:
- `candidates/`: proposed changes under evaluation.
- `promoted/`: accepted changes with eval evidence.
- `rejected/`: retained failures and regressions.
