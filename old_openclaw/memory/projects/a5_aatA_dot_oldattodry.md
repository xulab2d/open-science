# Project context: A5 AAtA “dot” (Old Attodry) — dot dispersion / n–D sweeps

Source path (data cache):
- `data/dropbox_cache/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry/`

People:
- Zengde, Weijie

Platform / technique:
- tMoTe₂ “A5 AAtA dot” device on the old Attodry
- Photoluminescence (PL) spectroscopy focused on quantum-dot-like features.

What changed recently (2026-03-03 delta):
- New/updated PL datasets in `data/02PL/dot1dispersion/` including:
  - `02_07_dot1nDsweep_6p8T_..._Bset6` through `Bset10` (allrange and smallrange/fine)
- Updated/added analysis scripts:
  - `streda.m` and `plot_nsweep_intreda.m`
  - updated PL plotting script `plot_dualGateDep_nsweep_PL_unpol_offsetsub_WJ_newref.m`
- Summary slides present (OpenScience-generated):
  - `OpenScience/ZDS_spot3dotdispersion_scan1_OpenScience_v3_3x2.pptx`

What the summary slides cover (3 slides):
1) Integrated intensity vs B and n
2) Integrated intensity vs B and filling factor ν
3) Tracked peak energy vs B and filling factor ν

Open questions for the owners:
- Confirm gate calibration used to compute ν (what n0 / v1 / moiré density assumption for this device?)
- What is “dot1” physically (localized potential? strain site?), and what is the intended signature vs B and ν?

Provenance:
- Slide titles extracted from `.../OpenScience/ZDS_spot3dotdispersion_scan1_OpenScience_v3_3x2.pptx` (2026-03-03).
