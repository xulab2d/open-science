Canonicalized: `memory/compactions/2026-03-02_compacted_routing_and_paths.md`

# 2026-03-02 — Cleanup heartbeat policy (Isaac)

Source: Slack DM from Isaac V (timestamp Mon 2026-03-02 21:29 PST).

Decisions:
- Cleanup heartbeat is **report-only** for now (no deletions without explicit approval).
- Cleanup scope: **workspace only** (`/Users/isaacvanorman/.openclaw/workspace`), not Dropbox cache/data.
- Schedule: nightly at **2:00 AM** local, as part of a standard hourly heartbeat cadence.

Implementation notes:
- Produce `reports/cleanup_audit_YYYY-MM-DD.md` with candidate vestigial/outdated files and confidence levels.
