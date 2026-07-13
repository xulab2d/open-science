**Observation**  
The supplied context does not include a B79-specific project entry or root path. The active-project registry shown lists other tMoTe2 optical/RMCD/PL projects, but no visible B79 entry (`lab_assistant/context/projects/active_projects.md`). Core directives say project-tied questions should first load that project’s `context/projects/` and `knowledge/projects/` notes (`lab_assistant/core/directives.md`; `lab_assistant/knowledge/projects/README.md`).

**Inference**  
Before answering RMCD/PL questions for B79, route by device/project ID first, not by generic optical keywords. Consult the B79 local project page/snapshot in `context/projects/` and `knowledge/projects/` if available, plus its canonical NAS project root from `active_projects.md`. Then inspect high-signal observables: RMCD hysteresis/field dependence, PL spectra/maps, gate or displacement-field trends, polarization contrast, peak splitting, anomalous contrast, and any processed plots or fit outputs (`skill:background-cataloguing`).

**Uncertainty**  
The provided context is insufficient to identify B79’s exact local path, owner, sample structure, or existing measurements. I would not answer B79-specific RMCD/PL physics until the B79 project note or NAS root is supplied.