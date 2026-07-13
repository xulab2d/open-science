**Observation**

For A5, the active project registry identifies the relevant local project as “Zengde/Weijie A5 AAtA dot,” covering dot PL, PLE, filling-dependent branches, polarization, power/wavelength dependence, and optical-control-style measurements. Canonical root: `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry` (`lab_assistant/context/projects/active_projects.md`).

The workspace directive says that for a selected project, the assistant should load that project’s `context/projects/` and `knowledge/projects/` notes into initial working context before interpretation (`lab_assistant/core/directives.md`). The project knowledge README also points to `knowledge/projects/current_projects_2026_07_07.md` as the evidence-backed active-project snapshot (`lab_assistant/knowledge/projects/README.md`).

**Inference**

Before interpreting A5 PL dispersion or peak-tracking outputs, load:

1. `lab_assistant/context/projects/active_projects.md` for the canonical A5 identity, scope, and NAS root.
2. The A5-relevant section of `lab_assistant/knowledge/projects/current_projects_2026_07_07.md`, because it is described as the NAS-backed evidence snapshot.
3. Local files under `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`, prioritizing processed plots, notebooks/scripts, peak-tracking outputs, fit tables, slides, and analysis notes, consistent with the background-cataloguing procedure (`skill:background-cataloguing`).

This should happen before pulling in broad moire/global literature context, because the question is project-specific and the directives say “Project context first” (`lab_assistant/core/directives.md`).

**Uncertainty**

The supplied context does not include the actual A5 project note contents or specific peak-tracking/PL-dispersion filenames, so I cannot name the exact analysis files to load beyond the canonical project root and the local-context categories above.