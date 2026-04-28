# MT48 (Shuai/CWB) — streda-like integrated PL metric

Date: 2026-03-20

## Goal
Reproduce the intent of `streda.m` (integrated PL metric in a fixed energy window, plotted vs doping density n and B) in a non-interactive pipeline.

## Background / dependencies
- Background file used by streda.m:
  - tMoTe2_Measuring/Shuai_CWB_MT48_attodry911/Data/PL/Spot 1/D = 0 Dispersion/300g_1160nmc_2s.mat

## Implementation notes (Python approximation of streda.m)
- Convert wavelength to energy: `E = 1240/w`.
- Energy window: 1.04–1.08 eV (as in streda.m).
- For each sweep point, find the max pixel inside that window and integrate intensity around it (±3 pixels).
- Normalization: attempted to mirror streda.m’s division by `min(mean(I1(range,290:300)))` using the same energy window and sweep-index slice.
- n conversion: dt=9.5 nm, db=13.5 nm (as in streda.m).

## Output
- out/plots/mt48_streda_like_metric_map_B_vs_n_stredaNorm.png

## Caveat
This still assumes cmerge(background) ≈ average of 2 channels when present; if `cmerge` is not a plain average, we should implement it explicitly.
