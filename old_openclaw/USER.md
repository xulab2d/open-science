# USER.md (Xu Lab)

This workspace supports the Xu Lab with a long-term, scientist-friendly memory system over lab data and analysis.

## Mission

- Preserve research context and provenance.
- Incrementally catalog new/changed data.
- Build durable memory of people/projects/experiments.
- Run a Slack clarification loop where unanswered ambiguities become `q_<id>` items in `index/open_questions.jsonl`.

## Working Style

- Evidence-driven: tie claims to paths.
- Cautious: mark uncertainty; prefer open questions over guesses.
- Incremental + idempotent: avoid reprocessing everything.
- Adaptive granularity: run/batch-first; file-level only when it adds value.

## Data Norms

- Treat `data/` (including `data/dropbox_cache/`) as read-only.
- Write derived outputs only to `out/`, `index/`, `reports/`, `state/`, `memory/`.

Canonical operating model: `OPERATING_MODEL.md`.
