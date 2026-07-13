**Observation**  
The supplied context does not include a B79-specific project note, NAS root, graph node, owner, or prior result. The available routing guidance says project-specific questions should first use `context/projects/` and `knowledge/projects/` notes, especially `lab_assistant/context/projects/active_projects.md` and `lab_assistant/knowledge/projects/current_projects_2026_07_07.md` when available (`lab_assistant/core/directives.md`; `lab_assistant/knowledge/projects/README.md`).  

For optical/magnetic questions, the cataloguing skill lists relevant observables to inspect: hysteresis, RMCD, PL features, displacement-field trends, peak splitting, anomalous contrast, and contradictions with prior project understanding (`skill:background-cataloguing`).  

**Inference**  
Before answering B79 RMCD/PL questions, the assistant should route by device/project identity first, not by generic optical keywords. It should consult the local B79 project context in `context/projects/` and `knowledge/projects/`, then inspect B79-specific measurement outputs for RMCD/PL observables: spectra/maps, polarization contrast, hysteresis or field dependence, gate/displacement-field dependence, peak shifts/splitting, and anomalous contrast.  

**Uncertainty**  
The supplied context is insufficient to identify what B79 is, where its project folder lives, who owns it, or what B79-specific RMCD/PL results exist. I cannot make factual claims about B79 beyond the consultation route and observable categories supported by the provided context.