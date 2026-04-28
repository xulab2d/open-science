# Project context: Sample B79 (Attodry 911)

Source path (data cache):
- `data/dropbox_cache/tMoTe2_Measuring/WJL_Zengde_B79_Attodry911/`

People (from folder + prior notes):
- Weijie (WJL), Zengde

Platform / technique:
- tMoTe₂ device “B79” on Attodry 911
- Low-temperature optical measurements (PL in `01_PL/`), plus extensive MATLAB control/analysis utilities.

What changed recently (2026-03-03 delta):
- Many MATLAB scripts updated/added, including:
  - Magnet GPIB control utilities (`magnet_GPIB_control_singlez/*`)
  - Gate-to-(n,D) conversions (`calcgatesnD.m`, `directgatetonD.m`, etc.)
  - Dual-gate acquisition scripts (`sweepGatesUpdate_fast.m`, etc.)
  - PL plotting scripts and background references (`01_PL/bg_*`, plot scripts)
  - Summary slides: `WJL_Zengde_B79_Attodry911.pptx`

Summary slides (high-level, extracted titles only):
- Slide 1: “Sample B79 Attodry 911”
- Slide 5: “Gate test”

Open questions / what I need from owners:
- Which device stack / twist angle is B79?
- What is the intended primary observable (PL peak energy? integrated intensity? polarization)?
- What’s the current experimental objective (mapping a phase boundary, locating clean spots, etc.)?

Provenance:
- Slide titles extracted from `.../WJL_Zengde_B79_Attodry911.pptx` (2026-03-03).
