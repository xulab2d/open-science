# NAS Guide

Primary assumption:
- The Synology NAS is now the main source of lab files.

Verified on this machine:
- Primary mounted share: `/Volumes/Xu Lab`
- Main project-data root confirmed: `/Volumes/Xu Lab/tMoTe2_Measuring`
- Main assistant-summary root confirmed: `/Volumes/Xu Lab/OpenScience/Summaries/PPT`

Implications:
- File discovery skills should start from NAS-mounted paths.
- Project notes should record canonical NAS roots when known.
- Local caches, exports, and generated artifacts are secondary context, not source of truth.

Guidelines:
- Prefer documenting stable NAS root patterns over one-off absolute paths when possible.
- When a task depends on a specific mounted volume or share name, record it here or in the relevant project note.
- If legacy notes mention Dropbox paths, translate them into project identity and folder-pattern knowledge rather than preserving the path itself.

Open items:
- Confirm the main project-specific roots within `/Volumes/Xu Lab`.
- Record additional mounted shares if the lab uses more than one NAS volume.
