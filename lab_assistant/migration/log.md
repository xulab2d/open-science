# Migration Log

Date: 2026-04-08

Created:
- a new `lab_assistant/` workspace with separated `core/`, `context/`, `skills/`, `tools/`, `memory/`, `plans/`, and `migration/`
- a compact core directive set
- an explicit preference layer for plots, interesting features, and work style
- NAS-first guidance
- an initial modular skill set
- a Slack integration placeholder that keeps channel specifics out of core behavior

Migrated by reinterpretation:
- provenance-first reasoning
- active-project awareness
- project-owner and maintainer routing concepts
- science-forward summary style
- small-canon memory philosophy

Intentionally not migrated:
- Dropbox cursor-sync architecture
- OpenClaw CLI messaging assumptions
- cron and heartbeat orchestration as the core model
- large generated output trees
- redundant root instruction files
- framework state and session data

Compressed or restructured:
- many overlapping behavioral directives into `core/directives.md` and `core/workflow.md`
- scattered memory guidance into `context/` plus reusable `skills/`
- Slack behavior into a future integration plan instead of primary instructions

Open questions:
- Slack user-id mapping for the current lab members
- which project notes should be canonicalized next
- which legacy helper scripts are still worth salvaging as deterministic Codex tools

Date: 2026-04-10

Created:
- `daemon/` as a clean replacement for OpenClaw-style heartbeat monitoring
- `scripts/catalog_pulse.py` for deterministic NAS metadata snapshots and compact deltas
- `skills/background-cataloguing.md` to keep catalog review behavior modular
- `memory/project_pulse.md` for durable lessons from background data monitoring

Migrated by reinterpretation:
- heartbeat logging became compact pulse reports and daily log lines
- "researcher-mode heartbeat" became report-triggered scientific review
- full ingest gating became baseline-first scanning plus sync-backfill detection
- token hygiene rules became compact project-linked deltas rather than raw inventories

Intentionally not migrated:
- Dropbox cursor logic
- OpenClaw heartbeat prompt stack
- automatic broad data ingestion on every run
- cleanup/delete behavior
- monolithic state files as assistant context

Current stance:
- During NAS Dropbox backfill, pulses should be conservative and treat bulk changes as likely sync noise.
- Codex review should be triggered by high-value deltas, not by every file event.
