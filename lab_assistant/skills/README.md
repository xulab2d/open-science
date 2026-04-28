# Skills

Skills are the preferred place for reusable lab-assistant behavior.

Skill design rules:
- Keep each skill focused on one job.
- Prefer checklists and decision rules over long prose.
- Reference canonical context files instead of duplicating them.
- Update skills when a behavior recurs; avoid bloating core directives.

Initial skill set:
- `file-location.md`
- `activity-summary.md`
- `request-triage.md`
- `project-brief.md`
- `plot-review.md`
- `plot-generation.md`
- `capture-feedback.md`
- `knowledge-maintenance.md`
- `reference-retrieval.md`

Capability notes:
- Not every durable behavior needs a full skill. Small, cross-cutting interface facts can live in `context/`.
- Current examples include rendered math and file-backed image handling in the OpenScience UI.
