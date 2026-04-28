# Hierarchical structure proposal (for fast retrieval)

Design goal: the assistant should be able to answer “what is X / where is Y / what’s the latest / what conventions apply?” with **one hop** from a stable index file, and only then drill into details.

## Level 0 (workspace entry points)
- `memory/START_HERE.md` — top-level table of contents.
- `MEMORY.md` — big-picture dataset overview (device/modality/naming) (keep concise).

## Level 1 (what I need to remember, not where files are)
- `memory/field_guide.md` — consolidated lab conventions + “things that matter repeatedly”
  - plotting/axes norms
  - calibration norms (n, D, ν)
  - slide-writing norms (academic tone, what a good slide contains)
  - interpretation caveats (what’s instrument background vs physics)
- `memory/directives.md` — high-level behavior directives from Isaac (and others)
  - each directive has: statement, date, source (Slack ts), and operational consequence

## Level 2 (project-specific truth)
Folder: `memory/projects/`
- `memory/projects/PROJECT_INDEX.md` — project → canonical note + deck + data roots.
- `memory/projects/<project_id>.md` — one canonical note per project, with fixed headings:
  - “What this project is” (1 paragraph)
  - Data roots (Dropbox path + cache path)
  - Modalities + key file types
  - Conventions (observable definitions, energy windows, sign conventions)
  - Current state (what’s known / what’s unknown)
  - Open questions (with owner)
  - Links to latest plots + running deck

## Level 3 (people + routing)
Folder: `memory/people/`
- `memory/people.md` — quick roster + roles.
- `memory/slack_expert_handles.md` — routing map (DM-first).

## Level 4 (procedures)
Folder: `memory/sops/`
- stable SOPs for sync, ingest, deck update flows.

## Principles
- Dated notes are allowed, but must be “pointed into” the hierarchy once canonicalized.
- Everything should be reachable from `memory/START_HERE.md`.
- Prefer *few canonical files* + links over many near-duplicates.

Last updated: 2026-03-12
