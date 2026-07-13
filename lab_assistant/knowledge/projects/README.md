# Project Knowledge

Purpose:
- Hold project-facing knowledge pages that connect active Xu Lab work to the broader field notes.

Style:
- concise
- current-project-centered
- cross-link to syntheses and papers rather than repeating them

Expected contents:
- what the project appears to be probing
- the main observables and modalities
- nearby domain notes to consult
- nearby paper shelves to consult
- key local canon/context files

Current snapshot:
- `current_projects.md`: dashboard-facing overview organized around broad current portfolio and recent developments.
- `current_projects_2026_07_07.md`: NAS-backed refresh of active projects after the documentation hiatus, including evidence strength and inferred current personnel.

Dashboard convention:
- Dashboard display names should follow `Device or area - short role`, with the device ID first when one exists. Examples: `A5 - AAtA dot PL/PLE`, `D88 Coil - domain/MCD linecuts`, `AFM/Fab - provenance and devices`.
- Each configured dashboard project should carry a `leads` array in `daemon/config.json`. Use full names for filtering; leave the array empty only when ownership is genuinely unclear.
- Project pages should open with `Broad Overview` and `Recent Developments`.
- Keep detailed caveats in `Watchpoints` so the dashboard stays useful without overstating tentative physics.
