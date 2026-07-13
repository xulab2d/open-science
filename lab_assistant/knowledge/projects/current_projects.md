# Current Projects Overview

Status: active dashboard summary. Last refreshed from NAS/project notes on 2026-07-07.

## Broad Overview

The current lab portfolio is dominated by moire tMoTe2 optical and magneto-optical work, with several devices probing filling-dependent PL, reflectance, RMCD, hysteresis, and scanning-PL signatures. The active tMoTe2 set includes Zengde/Weijie A-series BAAB/AABB/AAtA-dot devices, Shuai/Christiano/Weijie MT48 helical trilayer work, Courtney/Christiano/Yue D88 and D135 helical/AAA optical-magnetism projects, Christiano D24/D25 scanning-PL work, and Julian AHS3 RMCD/PL/dR work.

Outside the main `tMoTe2_Measuring` tree, there are active signals in MnTe Opticool/RMCD/birefringence, SHG sample surveys and polarization measurements, and AFM/fabrication folders for Zengde, Weijie, and James. Those roots are important for provenance and sample flow, but the scientific summaries should usually be tied back to shared measurement/project folders when possible.

Storage convention matters: personal folders usually carry flakes, AFM, assembly photos, KLayout/EBL design files, and sometimes early measurements. Shared roots such as `tMoTe2_Measuring` carry the more complete measurement and result history.

## Recent Developments

June 2026 NAS evidence shows a strong current push on Zengde/Weijie A-series optical devices. A5 is focused on AAtA-dot PL/PLE, filling-dependent branches near integer and fractional fillings, polarization, power dependence, wavelength dependence, and optical-control-style checks. A13 and A18 extend this into AABB/BAAB/twisted-region reflectance, polarized dual-gate maps, weak R-L or FM-like features, and resonance assignment caveats. A22 is an early BAAB scanning-PL/spatial-map project.

MT48 has June-active PL/dR dual-gate work on a 4-degree helical 1+1+1 tMoTe2 device, connecting optical features to filling assignments such as `nu = -1`, `nu = -4/3`, and broader insulating/fractional-looking regimes. D88 remains a benchmark family: the original D88 root, D88 run2, and Yue's coil-measurement root now cover RMCD/PL/dE-dn-style optical fans, domain identification, and pulsed/modulated coil-MCD linecuts. D135 is a 5-degree helical project with PL/dR dispersion and topology-oriented field dependence, but filling labels remain uncertain in places.

Christiano's D24/D25 roots are scanning-PL and dual-gate optical projects; D25 appears across multiple roots and should be treated as one project family until naming is reconciled. Julian AHS3 has Attodry911 RMCD, hysteresis, dual-gate, PL, and dR evidence, with a separate scanning-PL root carrying April PL/dR gatedep work.

The daemon/dashboard had been watching only the older seed set: MT43, A5, D93, B79, C7, and one D88 root. The dashboard configuration has now been expanded with the current roots while keeping broad/non-project overview entries inactive for scanning.

## Watchpoints

- Treat the 2026-07-07 catalog pulse as a visibility/backfill pointer, not proof of same-day acquisition.
- Do not infer current lab membership from NAS folder names; use the lab roster and user correction.
- Keep device-family naming clean: A5, A13, A18, A22, MT48, D88, D135, D24/D25, and AHS3 should not be merged just because the same scripts or people recur.
- For optical/magnetic claims, prefer project decks, processed plots, and scripts over raw filename inference.
