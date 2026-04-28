# Xu Lab Codex Assistant Workspace

This workspace is a clean Codex-native replacement for the legacy `old_openclaw` system.

Design goals:
- Keep the assistant easy to parse, audit, and extend.
- Store durable lab knowledge in small canonical files.
- Push behavior into modular skills instead of one giant prompt.
- Treat the lab NAS as the primary source of files and context.
- Keep channel-specific integration separate from core assistant behavior.

Directory map:
- `core/`: small canonical directives and workflow rules.
- `core/preferences.md`: explicit lab preferences that should shape outputs.
- `context/`: lab facts, conventions, people, projects, NAS guidance.
- `graph/`: provenance-backed subject-matter fact graph for claims, mechanisms, observables, and evidence.
- `skills/`: reusable behavioral modules for common lab tasks.
- `tools/`: deterministic helper-script guidance and future wrappers.
- `daemon/`: background catalog pulse scanner for NAS project activity.
- `memory/`: lightweight durable notes created through ongoing use.
- `plans/`: integration plans and future-facing design notes.
- `migration/`: what was learned from the legacy system and how it was reinterpreted.

Working rule:
- Prefer updating an existing canonical file over creating a new ad hoc note.
- Before producing summaries, plots, or decks, check `core/preferences.md` and the relevant files under `context/`.
