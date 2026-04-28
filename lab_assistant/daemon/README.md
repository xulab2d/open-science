# OpenScience Catalog Daemon

Purpose:
- Maintain a compact, project-linked pulse of lab data changes on the NAS.
- Separate deterministic file cataloguing from expensive scientific interpretation.
- Give Codex a stable trail of what changed, where it belongs, and what deserves attention.

Current stance:
- Polling beats file-event watching for now. The NAS is still receiving Dropbox backfill, so file events are too noisy and too easy to overinterpret.
- First run should baseline only. Later pulses should focus on deltas.
- A pulse is not a full data analysis. It is a triage layer that decides whether deeper review is worth running.

Files:
- `config.json`: watched roots, project IDs, ignore rules, scoring hints, and trigger thresholds.
- `run_pulse.sh`: one deterministic scan and digest.
- `run_daemon.sh`: simple interval loop for local testing or launchd supervision.
- `install_launchd.sh`: installs and starts the launchd service for the current user.
- `run_daily_check.sh`: one deterministic sanity check of daemon health and organization.
- `run_daily_overview.sh`: daily sanity check plus mandatory Codex reasoned overview.
- `install_daily_overview_launchd.sh`: installs the 2 AM daily Codex overview launchd service.
- `state/`: generated snapshots and scanner state. Do not hand-edit.
- `reports/`: generated JSON and Markdown pulse reports.
- `health/`: generated daily operational health reports.
- `overviews/`: generated Codex daily reasoned overviews.
- `overviews/daily_summary_latest.md`: copy of the latest daily overview for the browser UI.
- `out/`: optional generated Codex review prompts.
- `launchd/`: macOS launchd templates.

Recommended startup:
1. Confirm the NAS is mounted at `/Volumes/Xu Lab`.
2. Run `./lab_assistant/daemon/run_pulse.sh --baseline-only`.
3. Run normal pulses with `./lab_assistant/daemon/run_pulse.sh`.
4. After the Dropbox-to-NAS backfill settles, consider lowering thresholds or adding broader roots.

Run continuously:
- Local foreground test: `OPENSCIENCE_PULSE_INTERVAL_MINUTES=30 ./lab_assistant/daemon/run_daemon.sh`
- launchd install/start: `./lab_assistant/daemon/install_launchd.sh`
- launchd stop/remove: `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.xulab.openscience.catalog.plist`

macOS NAS permission note:
- If launchd reports `Operation not permitted` on `/Volumes/Xu Lab`, the scanner now preserves the previous good state and marks the pulse as failed.
- Interactive Terminal scans may still work because Terminal and launchd jobs can have different privacy/NAS permissions.
- The daemon prefers `/opt/homebrew/bin/python3`; grant Full Disk Access to that executable and `/bin/bash`.
- If this repeats, run the daemon from a supervised terminal session until permissions are fixed.

Run the daily sanity check:
- One-off check: `./lab_assistant/daemon/run_daily_check.sh`

Run the daily Codex overview:
- One-off overview: `./lab_assistant/daemon/run_daily_overview.sh`
- launchd install/start at 2 AM: `./lab_assistant/daemon/install_daily_overview_launchd.sh`
- launchd stop/remove: `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.xulab.openscience.daily-overview.plist`
- The browser UI reads the latest overview as the daily summary tab; keep the output concise and PI-readable.
- If `/tmp/openscience-daily-overview.err.log` says `env: node: No such file or directory`, launchd cannot see Homebrew's PATH. `run_daily_overview.sh` exports `/opt/homebrew/bin` explicitly so Codex can find `node`.
- The overview is forward-facing: lead with research updates and keep operational status secondary.
- The spawned Codex may inspect the NAS, but it should stay bounded: read relevant scripts, small notes, processed figure names, summary decks, and local listings rather than broad crawls or large raw `.mat` files.
- `run_daily_overview.sh` wraps Codex with `OPENSCIENCE_CODEX_TIMEOUT_SECONDS` so a stuck run cannot persist overnight.
- The daily overview now runs Codex with `--sandbox danger-full-access` so overnight reviews can reach Slack and other networked resources when needed.

Design rules:
- Do not delete, rename, or mutate NAS data.
- Do not read large raw data files during the pulse.
- Treat bulk changes across many folders as likely sync backfill until proven otherwise.
- Promote only stable scientific lessons into `knowledge/`, `context/`, or `memory/`.
- Keep browser-facing project pages in Markdown: active projects under `knowledge/projects/`, past projects under `knowledge/past_projects/`.
- Keep reports compact enough to paste into Codex context without dragging raw file listings.

Future escalation:
- The scanner can write a focused Codex review prompt with `--write-codex-prompt`.
- A separate supervised job can later run `codex exec` on those prompts, but that should be gated by report scores and lab feedback.
- The daily overview is different: it always invokes Codex at 2 AM for a reasoned organizational/scientific overview, even if no individual pulse crossed the review threshold.
