# SOP: Filling assignment (ν) for Zengde dot project (dot1 n–D sweeps)

Status: **draft** (2026-03-04). Needs confirmation from Zengde/Weijie.

Context
- Project folder: `tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry/`
- Data family: `data/02PL/dot1dispersion/*dot1nDsweep*Bset*.mat`
- Gate conversion script in folder: `calcgatesnD_trilayer.m` (capacitance model; eps_r≈3 and thicknesses TG/BG are parameters).

## Goal
Given dual-gate sweeps, compute density `n` and displacement field `D`, then assign filling factor `ν` robustly.

## Recommended procedure (anchor-based; avoid hard-coding)
1) **Compute n, D from (Vtg, Vbg)** using the project’s capacitance model (same thickness + dielectric assumptions used in acquisition/analysis scripts for that dataset).
   - Use the thickness values *recorded for that run* (e.g., scripts sometimes show `TG=33.5 nm`, `BG=27.4 nm`; do not mix with other devices).

2) **Pick anchor features from the data** rather than relying on remembered constants.
   - Identify prominent, reproducible features vs `n` at low B (or in B-averaged traces): e.g. kinks/dips/peaks that are known to correspond to specific integer/fractional fillings.
   - Use multiple anchors when possible (e.g., ν=-1 and ν=-2/3) and cross-check linearity.

3) **Solve for moiré density scale and n-offset**
   - Model: `ν = (n - n0) / n_m` where `n_m` is the density per moiré filling (sign convention per project).
   - If two anchors `(n_a, ν_a)` and `(n_b, ν_b)` are trusted:
     - `n_m = (n_a - n_b) / (ν_a - ν_b)`
     - `n0 = n_a - ν_a * n_m`
   - Prefer anchors taken at similar D and comparable conditions.

4) **Propagate to all data**
   - Convert each pixel/trace: `ν(n) = (n - n0) / n_m`.
   - Report the inferred `(n_m, n0)` on plots.

5) **Sanity checks**
   - Confirm expected ordering of features with B (Landau fan slopes) and symmetry where appropriate.
   - Check that ν=0 aligns with the intended neutrality (if any) and that ν=-1 occurs near the known feature.

## Common pitfalls (what likely went wrong previously)
- **Using the wrong BN thickness/eps assumptions** (mixing across samples) → shifts n scale.
- **Hard-coding ν anchors** (e.g., reusing v1/v23 values from another dataset) instead of re-extracting from current data.
- **Sign conventions**: whether ν is defined positive for electrons/holes; and whether n computed from gates matches that sign.
- **Mixing sweeps at different D** when extracting anchors → inconsistent calibration.

## Open questions to confirm (asked to Zengde)
- Which specific features are the canonical ν=-1 and ν=-2/3 anchors for dot1nDsweep (and under what conditions)?
- Exact sign convention for ν in this project.
- Whether n0 is assumed 0 or fitted.
- Whether n_m is fixed from geometry or fitted from anchors.

