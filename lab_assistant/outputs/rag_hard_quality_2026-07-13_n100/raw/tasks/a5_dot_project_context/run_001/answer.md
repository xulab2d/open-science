**Observation**

For A5, the active project registry identifies the local project as “Zengde/Weijie A5 AAtA dot” covering dot PL, PLE, filling-dependent branches, polarization, power/wavelength dependence, and optical-control-style measurements. Root: `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry` (`lab_assistant/context/projects/active_projects.md`).

The lab directive says that for project-tied questions, the assistant should load that project’s `context/projects/` and `knowledge/projects/` notes first (`lab_assistant/core/directives.md`). The project knowledge README also names the dashboard/context label convention: `A5 - AAtA dot PL/PLE` (`lab_assistant/knowledge/projects/README.md`).

**Inference**

Before interpreting A5 PL dispersion or peak-tracking analysis, load the A5-specific local context first:

1. `lab_assistant/context/projects/active_projects.md` entry for A5.
2. The corresponding project knowledge page/snapshot under `lab_assistant/knowledge/projects/`, especially `current_projects_2026_07_07.md` if available from the project snapshot convention.
3. The local NAS project root: `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`, prioritizing analysis notes, processed tables, fit outputs, notebooks/scripts, named plot folders, and existing PL/PLE/peak-tracking figures.

This should precede broad moire-literature retrieval, because the evaluation target is project-context retrieval and the directives say “Project context first” (`lab_assistant/core/directives.md`).

**Uncertainty**

The supplied context does not include the actual A5 project knowledge page contents, PL dispersion files, peak-tracking scripts, or figure paths. It only identifies the project root and the rule that local project context should be loaded first.