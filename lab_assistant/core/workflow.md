# Core Workflow

Default workflow for lab-assistant tasks:

1. Orient
- Identify the request type: locate, summarize, analyze, explain, triage, or prepare communication.
- Check the relevant canonical context file before digging into raw folders.
- If scientific background is needed, start from `knowledge/INDEX.md` and enter by project or domain.
- For any presentation-facing task, check `core/preferences.md`, `context/plot_preferences.md`, and `context/interesting_features.md`.

2. Gather evidence
- Use NAS paths, project notes, scripts, and recent artifacts as primary context.
- Prefer representative files and summary materials over bulk reads.

3. Act
- Complete the concrete task directly when possible.
- Use deterministic scripts for repetitive or exact operations.
- Keep provenance available for any nontrivial conclusion.
- Prefer a short, explicit workflow over an open-ended exploration loop.

4. Preserve what matters
- Record durable conventions, project facts, and repeated user preferences in canonical files.
- Put ephemeral work notes in `memory/notes/`.
- If the interaction exposed a success pattern, failure pattern, or new repeated need, update the appropriate file before considering the task complete.

5. Close the learning loop
- For corrected behavior, use `skills/capture-feedback.md`.
- For a new recurring capability, add or update a skill.
- For project-specific lessons, update `context/projects/` or `knowledge/projects/`.
- For scientific understanding that should persist, update `knowledge/syntheses/` or `knowledge/papers/`.
- For recurring wins, misses, or unresolved weak spots, append a short note to `memory/review_log.md`.

6. Prepare channel output
- Keep core reasoning channel-agnostic.
- Apply Slack-specific formatting or routing only at the final communication layer.

Default token-savvy rules:
- Search narrow before searching broad.
- Prefer project roots, summary decks, scripts, and representative files over deep folder walks.
- Record stable preferences once, then reuse them.
- If a task recurs and the right way to do it is now known, promote it into a skill.
- Treat repeated success and repeated failure as equally important inputs to workspace maintenance.

Operational roots currently confirmed:
- Primary project data root: `/Volumes/Xu Lab/tMoTe2_Measuring`
- Assistant summary root: `/Volumes/Xu Lab/OpenScience/Summaries/PPT`

When to create a new skill:
- A task recurs.
- The steps are specific enough to name.
- The behavior would benefit from a short reusable checklist.
