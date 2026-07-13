**Observation**  
The supplied context says project-specific questions should first load that project’s `context/projects/` and `knowledge/projects/` notes, and use NAS project roots as primary lab-file context (`lab_assistant/core/directives.md`; `lab_assistant/context/projects/active_projects.md`).  

No B79-specific entry, root path, project note, or measurement summary is present in the supplied context.

**Inference**  
Before answering RMCD/PL questions for B79, consult the B79 local project context first, not generic RMCD/PL optical-project notes:  
- B79 entry/root in `lab_assistant/context/projects/active_projects.md`, if present in the full file.  
- B79 project-facing notes in `lab_assistant/knowledge/projects/`.  
- Any B79-specific NAS folders/files referenced by those notes.  

Measurement observables to check should include RMCD/PL-relevant signals plus project-status observables named in the cataloguing guidance: hysteresis, RMCD/PL features, displacement-field trends, peak splitting, anomalous contrast, and contradictions with prior project understanding (`skill:background-cataloguing`).

**Uncertainty**  
The context is insufficient to identify B79’s actual device structure, NAS root, owners, dates, or specific RMCD/PL datasets. Any B79-specific answer would require the missing B79 project notes or file paths.