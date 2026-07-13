**Observation**  
Before answering B79 RMCD/PL questions, the routing context says to load the selected project’s local notes first: `context/projects/` and `knowledge/projects/` (`lab_assistant/core/directives.md`). The active project registry is `lab_assistant/context/projects/active_projects.md`, with project knowledge conventions in `lab_assistant/knowledge/projects/README.md`.

For measurement evidence, the background-cataloguing skill says to inspect high-signal project files first: notebooks, scripts, processed tables, fit outputs, slides, analysis notes, and named plot folders (`skill:background-cataloguing`). It specifically flags meaningful observables such as new sweeps, hysteresis, RMCD/PL features, displacement-field trends, peak splitting, anomalous contrast, and contradictions with prior project understanding (`skill:background-cataloguing`).

**Inference**  
For B79, do not answer from generic RMCD/PL knowledge alone. First consult the B79-specific local project context in `context/projects/` and `knowledge/projects/`, then the canonical NAS/project root if identified in `active_projects.md`. The relevant observables to check are RMCD contrast/sign, PL peak positions/intensities/splitting, gate or displacement-field dependence, hysteresis, linecuts/maps, and any processed fits or plots tied to B79.

**Uncertainty**  
The supplied context does not include a B79-specific project entry, NAS path, owner, graph node ID, or actual B79 measurement results. Therefore I can identify the correct local-context routing and observable classes, but not make B79-specific scientific claims.