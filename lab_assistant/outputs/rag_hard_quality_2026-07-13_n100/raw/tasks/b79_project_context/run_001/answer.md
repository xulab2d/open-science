**Observation**

The supplied context does not include a B79-specific project note, root path, or graph node. It does say that project-tied questions should first load the project’s `context/projects/` and `knowledge/projects/` notes, and use `context/projects/active_projects.md` plus `knowledge/projects/current_projects_2026_07_07.md` to map canonical roots and evidence details (`lab_assistant/core/directives.md`, `lab_assistant/context/projects/active_projects.md`, `lab_assistant/knowledge/projects/README.md`).

**Inference**

Before answering B79 RMCD/PL questions, consult the B79 local project context first, not generic optical-keyword context: B79’s project page or registry entry, its canonical NAS root if present, recent notebooks/scripts/processed plots/slides, and any current-project snapshot entry (`lab_assistant/context/projects/active_projects.md`; `lab_assistant/knowledge/projects/README.md`; `skill:background-cataloguing`).

Measurement observables to check should include RMCD and PL features, hysteresis, displacement-field or gate trends, peak splitting, anomalous contrast, polarization dependence, and any contradictions with prior project understanding (`skill:background-cataloguing`).

**Uncertainty**

The supplied context is insufficient to identify what B79 specifically is, who owns it, where its NAS folder lives, or what RMCD/PL results already exist. Any B79-specific claim would require the missing B79 project note or local file context.