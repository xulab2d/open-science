**Observation**

The supplied context says project-specific questions should first load the project’s local `context/projects/` and `knowledge/projects/` notes before answering from generic optical keywords (`lab_assistant/core/directives.md`; `lab_assistant/knowledge/projects/README.md`). The active-project registry is the available routing source, but the visible excerpt does not include a B79-specific entry or root path (`lab_assistant/context/projects/active_projects.md`).

For RMCD/PL-style questions, the relevant local observables to check include PL, PLE, polarized reflectance/dR, RMCD/MCD, domain/linecut data, hysteresis, displacement-field or gate dependence, peak splitting, anomalous contrast, and filling-dependent branches (`lab_assistant/context/projects/active_projects.md`; `skill:background-cataloguing`).

**Inference**

Before answering B79 RMCD/PL questions, route through B79’s own project page/root if present in `context/projects/` or `knowledge/projects/`, then inspect the B79-local measurement records for PL/RMCD observables rather than jumping to generic RMCD or PL literature. The expected evidence should come from local plots, notebooks, processed tables, fit outputs, slides, or named plot folders (`skill:background-cataloguing`).

**Uncertainty**

The provided context is insufficient to identify B79’s specific project root, personnel, device geometry, or confirmed observables. I can only state the routing rule and observable classes to consult, not B79-specific results.