# Background Cataloguing Plan

Goal:
- Give OpenScience a consistent pulse on lab data without recreating brittle OpenClaw heartbeats.
- Convert file activity into project understanding, follow-up questions, and eventually scientific leads.

Architecture:
- `daemon/run_daemon.sh` performs scheduled polling.
- `scripts/catalog_pulse.py` scans configured NAS roots and writes compact reports.
- `scripts/daily_sanity_check.py` performs a daily organizational health pass.
- `scripts/daily_reasoned_overview.py` generates the prompt for the mandatory daily Codex overview.
- `daemon/state/` stores generated snapshots.
- `daemon/reports/` stores generated Markdown/JSON deltas.
- `daemon/health/` stores generated daily sanity-check reports.
- `daemon/overviews/` stores daily Codex reasoning outputs.
- `daemon/out/` stores optional Codex review prompts.
- `skills/background-cataloguing.md` defines how Codex should interpret pulse reports.

Why polling first:
- File-change events on a NAS can be noisy, duplicated, or delayed.
- Dropbox-to-NAS backfill will create large bursts that are not new scientific activity.
- A scheduled pulse is easier to audit, cap, and tune.

Operating phases:
1. Baseline phase:
- Watch only active project roots.
- Establish snapshots without treating all existing files as new.
- Tune ignore rules and project mappings.
2. Triage phase:
- Run every 30-60 minutes.
- Flag high-value changes: notebooks, scripts, processed tables, fits, slides, summaries, plot folders.
- Suppress bulk sync-backfill noise.
2b. Daily sanity phase:
- Check that the daemon is still producing reports.
- Check NAS roots, snapshot health, report volume, and obvious error patterns.
- Write one compact health report without doing scientific interpretation.
2c. Daily overview phase:
- At 2 AM, always run Codex on a focused prompt built from recent pulse reports, daily health, project context, and cataloguing guidance.
- Ask for a concise reasoned overview: operational health, project activity, possible scientific significance, what to inspect next, and what to update in memory/skills.
- Save the result in `daemon/overviews/`; do not require an individual file-change threshold.
3. Review phase:
- Generate focused Codex review prompts only when thresholds are met.
- Inspect relevant project notes before reading files.
- Update `memory/project_pulse.md` or `knowledge/projects/` when durable understanding changes.
4. Discovery phase:
- Add project-specific analysis helpers once repeated patterns are known.
- Track scientific signals such as RMCD hysteresis, PL peak shifts/splitting, Curie-Weiss behavior, displacement-field trends, anomalous contrast, and fit-parameter changes.
- Use lab feedback to promote successful analysis patterns into skills.

Current constraints:
- The NAS is still syncing from Dropbox, so new-file bursts are not reliable evidence of new work.
- The first scanner only records metadata and does not parse raw data payloads.
- Active roots are seeded from `context/projects/active_projects.md`.

Next decisions:
- Confirm the desired daemon cadence after observing noise for a few days.
- Decide whether to add historical project roots after the NAS sync settles.
- Decide whether Codex review should run automatically or write prompts for manual review first.
- Add project-specific detectors only after there is a clear success pattern.
