# A13 AABB

Status: active project summary. Owners inferred from the project root: Zengde She and Weijie Li.

## Broad Overview

A13 is a tMoTe2 AABB/twisted-AA/twisted-BB optical project on the old Attodry. The core measurement family is reflectance and polarized reflectance under dual-gate control, with scripts for `n`, `D`, peak analysis, R-L contrast, and region-specific maps.

The scientific question is whether weak polarization or FM-like optical features in selected AABB/twisted regions are real sample physics or artifacts of alignment, references, polarizer state, and region assignment.

Canonical NAS root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A13_AABB_oldattodry`

## Recent Developments

June 2026 evidence includes `Zengde_Weijie_A13_AABB_oldattodry_measure.pptx`, dual-gate reflectance maps, polarized reflectance analysis, and scripts such as `dR_dualgatesweep_peak_analysis_LF_WJ_gif_trilayer.m`.

The recent deck language is tentative: it reports weak FM or polarization features but also flags bad early data from alignment or polarizer problems. Current work appears focused on checking whether R-L features near selected spots and displacement fields survive better controls.

## Watchpoints

- Preserve the "maybe FM" status until alignment and reference choices are pinned down.
- Keep AABB, twisted-AA, twisted-BB, and spacer/broad-peak spot labels separate.
- Use the project `calcgatesnD`/trilayer scripts rather than generic gate conversion.
