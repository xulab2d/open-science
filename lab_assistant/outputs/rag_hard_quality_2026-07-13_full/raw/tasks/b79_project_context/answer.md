**Observation**

The supplied context says project-tied questions should load the project’s `context/projects/` and `knowledge/projects/` notes first, before generic domain routing (`lab_assistant/core/directives.md`). The project knowledge convention is to record what a project probes, main observables/modalities, nearby domain notes, paper shelves, and canon/context files (`lab_assistant/knowledge/projects/README.md`). The active project registry is the operational map for current projects (`lab_assistant/context/projects/active_projects.md`).

For measurement observables, the background-cataloguing skill flags scientifically meaningful optical/project signals including RMCD, PL features, hysteresis, displacement-field trends, peak splitting, anomalous contrast, and contradictions with prior project understanding (`skill:background-cataloguing`).

**Inference**

For B79 RMCD/PL questions, route first to B79-specific local project context, not to generic RMCD/PL optics notes. Consult the B79 entries/files under `lab_assistant/context/projects/` and `lab_assistant/knowledge/projects/`, using `lab_assistant/context/projects/active_projects.md` as the project registry if B79 is listed there.

The observables to check before answering are: RMCD contrast/sign and field dependence, PL spectra/features, hysteresis, gate or displacement-field dependence if present, peak shifts/splitting, spatial/domain contrast, and any mismatch with previous B79 project understanding. This follows the project-status/background-cataloguing routing guidance rather than an optics-keyword-only route (`skill:background-cataloguing`; `lab_assistant/core/directives.md`).

**Uncertainty**

The supplied context does not include a visible B79-specific project summary, NAS root, owner, device stack, or actual B79 data products. I therefore cannot name exact B79 files, numeric observables, results, or conclusions from this context alone.