# Tools

This directory is reserved for deterministic helpers that remain useful in a Codex-based workflow.

Principles:
- Keep tools small and understandable.
- Prefer wrappers around stable local operations.
- Avoid rebuilding the old OpenClaw automation stack by default.

Candidate future helpers:
- NAS path inventory or mount check.
- Recent-file summarizer for a project root.
- Project note scaffold generator.
- Slack payload formatter once integration is implemented.

Current helpers:
- `check_nas_mounts.sh`
- `find_project_roots.sh`
- `../scripts/catalog_pulse.py`: deterministic NAS project pulse scanner used by `../daemon/`
- `plotting/openscience_plot_style.py`: Python/Matplotlib plotting defaults for lab figures

Legacy tooling note:
- `old_openclaw/tools/` contains ideas and some reusable code, but most of it is tied to Dropbox sync, OpenClaw orchestration, or specialized experiments. Reuse selectively.
