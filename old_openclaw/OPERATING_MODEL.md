# OPERATING_MODEL.md (Canonical)

OpenScience in this workspace follows a two-stage daily loop:

1) Deterministic daily cron (no LLM)
- Pull Dropbox changes via Dropbox cursor delta (fast; no full tree walk).
- Download only changed files into `data/dropbox_cache/` (local cache).
- Write:
  - `state/delta_manifest.json`
  - `state/dropbox_cursor_state.json`

2) LLM-driven HEARTBEAT (runs periodically, but 1 pulse/day)
- Gate: if today's pulse already ran (tracked in `state/heartbeat_state.json`), do nothing beyond minimal checks.
- Primary scope: `state/delta_manifest.json`.
- Cataloging: adaptive granularity (run/batch-first; file-level only when it adds value).
- Provenance: all claims link to paths; uncertainty is explicit; open questions are recorded/routed.
- Optional context fetch (bounded): fetch extra Dropbox paths only when needed:
  - Write paths to `out/extra_context_paths.txt` (one per line)
  - Run: `python3 tools/dropbox_sync.py --paths-only --paths-file out/extra_context_paths.txt`
- Deterministic indexing: `python3 tools/ingest_daily.py --delta-manifest state/delta_manifest.json ...`
- Outputs:
  - `out/daily_digest_YYYY-MM-DD.md` (LLM narrative + decisions)
  - `index/*.jsonl` (idempotent memory)
  - Slack post: `out/slack_daily_update.md` via `openclaw message send` (Python helper optional)

Safety and scope rules:
- Source data is read-only (treat `data/` as immutable).
- Derived outputs go to `out/`, `index/`, `reports/`, `state/`, `memory/`.
- Slack: respond when mentioned; after a mention starts a thread, continue in-thread without requiring repeated @ when feasible (document limitations).
- Avoid new scripts; prefer policies + small deterministic utilities only.
