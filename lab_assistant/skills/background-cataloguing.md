# Skill: Background Cataloguing

Use when:
- Reviewing catalog pulse reports.
- Reviewing daily daemon health reports.
- Updating project memory from NAS changes.
- Deciding whether file changes deserve deeper scientific analysis.
- Improving the daemon or its scoring rules.

Procedure:
1. Start from the newest compact report in `daemon/reports/`, not from a full NAS crawl.
2. Map changes to the project note in `knowledge/projects/` and the canonical root in `context/projects/active_projects.md`.
3. Treat bulk, scattered changes as sync backfill unless there is a project-specific reason to believe they are new experiment activity.
4. Inspect only high-signal files or summaries first: notebooks, scripts, processed tables, fit outputs, slides, analysis notes, and named plot folders.
5. When new data or new analysis exists, prefer plot-first review: reuse existing informative plots first, or generate quick plots from processed data when safe and bounded. PI-facing daily summaries usually benefit from seeing the data directly before reading interpretation.
6. Look for scientifically meaningful events: new sweeps, fit parameter changes, emergent hysteresis/RMCD/PL features, displacement-field trends, peak splitting, anomalous contrast, or contradictions with prior project understanding.
7. If interpretation depends on owner knowledge, send a narrow Slack clarification using `lab_assistant/integrations/slack/post_clarification.py`.
- For a project-specific question, DM the mapped owner(s) first.
- Use `#open-science` only for broad lab-benefit questions, unclear ownership, or explicit share-with-lab cases.
- Prefer one specific question with enough context and a link/path to the relevant figure or file.
8. Record durable lessons in the smallest canonical place:
- `memory/project_pulse.md` for short operational lessons
- `knowledge/projects/` for project-specific scientific understanding
- `knowledge/syntheses/` for cross-project patterns
- `context/interesting_features.md` or `context/plot_preferences.md` for reusable preferences
9. If a report is noisy, update `daemon/config.json` scoring or ignore rules rather than accepting recurring clutter.
10. If a daily health report shows missing roots, stale pulses, repeated errors, or runaway report volume, fix the operational issue before adding scientific automation.

Defaults:
- Prefer scheduled polling over file-event triggers.
- Prefer compact deltas over raw file inventories.
- Prefer conservative triage during NAS backfill.
- Keep deterministic daily sanity checks operational, not interpretive.
- Keep Codex daily overviews forward-facing and scientifically inclined: explain research-relevant changes first, then give operational status.
- Strongly favor figures in daily overviews when data has been collected or reanalyzed. The summary should read like a concise lab note: embed figures inline as Markdown images near the claims they support, then explain the takeaway and caveat in text. Avoid detached figure-link sections unless no preview image can be produced safely.
- Clarification questions are part of the loop, not an afterthought: use Slack when owner input would materially improve interpretation, then promote the answer into durable project knowledge.
- Channel choice is part of scientific hygiene: default to owner DMs for project-specific questions and reserve `#open-science` for intentionally shared clarifications.
- For daily overviews, bounded NAS inspection is allowed when high-signal reports point to specific files or folders; avoid broad crawls and large raw files.
- Never mutate raw NAS data from a catalog pulse.
- Ask a targeted question when interpretation depends on missing experimental context.

Goal:
- Turn lab file activity into a steadily improving scientific map, not just a timestamped activity log.
