# Memory structure (OpenScience corpus)

Goal: maintain a robust, evolving map of **where knowledge lives** (files, indices, state) so the assistant can reliably locate data and context when asked.

## Canonical data + cache

- Source data (read-only): `data/` (incl. `data/dropbox_cache/`)
- Dropbox sync state + scope of daily changes:
  - `state/dropbox_cursor_state.json`
  - `state/delta_manifest.json`

## Derived corpus (query + provenance)

- Batch/run-level corpus index (durable): `index/`
  - Batches (large): `index/batches.jsonl` (query via jq/grep; do not read whole file)
  - Open questions (large): `index/open_questions.jsonl`
  - Any routing rules / aliases created by ingest live under `index/` (see `out/` digests for references)

- Ingestion state (large): `state/ingestion_state.json` (query via jq/grep)

## Human-facing outputs

- Daily digests / audits:
  - `reports/daily_digest_YYYY-MM-DD.md` (tool-generated ingest summaries)
  - `out/daily_digest_YYYY-MM-DD.md` (LLM science-forward narrative when produced)

- Clarification artifacts:
  - `out/slack_questions_to_ask.md` (generated prompts)
  - `out/questions_routed_YYYY-MM-DD.md` (what was asked + where)

## Expert routing

- Slack handle mapping (for DM routing): `memory/slack_expert_handles.md`
- Fallback channel for unowned questions: <#C0AH4A1A2JZ>

## Project-level context notes

When the assistant is dropped into the middle of ongoing projects, create/update lightweight project summaries:

- `memory/projects/*.md`
  - what the folder contains
  - inferred modality (with evidence)
  - key scripts + parameters
  - open questions + owner

## Ongoing improvement checklist

On “big updating” heartbeats (or weekly):

- Review whether `watched_roots` still match the real hierarchy.
- Check whether directory naming conventions are consistent enough for indexing.
- Identify missing READMEs (add derived notes under `memory/` rather than modifying raw data).
- Capture key semantics (what files mean, calibrations, axes/units) in `memory/` and/or via `apply_clarification.py` into `index/open_questions.jsonl`.

Last updated: 2026-03-02
