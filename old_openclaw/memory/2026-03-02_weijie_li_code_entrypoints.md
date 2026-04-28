Canonicalized: `memory/compactions/2026-03-02_compacted_routing_and_paths.md`

# 2026-03-02 — Weijie Li: analysis code entry points + example dataset

Source: Slack DM from Weijie Li (timestamp Mon 2026-03-02 21:16 PST).

Example dataset to start with:
- `04_05_spot5X32Y25_dualgate_linearexc_collR_300g_1100nm_5s__Bz_0p1T`

Code entry points:
- Dual-gate analysis script: `dR_dualgatesweep_peak_analysis_LF_WJ_gif_trilayer_spot1`
- Doping-dependence analysis script: `dR_dopingdep_differentRef_analysis_withpol_LF_v2`

Open questions:
- Confirm full filenames + extensions (likely `.m`) and their exact location relative to the measurement folder.
- Confirm any required dependencies/functions these scripts call.
