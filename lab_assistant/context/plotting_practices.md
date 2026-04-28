# Plotting Practices

Purpose:
- Make OpenScience plots clean on the first pass: readable, physics-forward, and close to paper/deck ready.
- Capture defaults inferred from Xu Lab summary decks and plotting scripts without freezing project-specific choices.

Reference material sampled:
- Summary decks in `/Volumes/Xu Lab/OpenScience/Summaries/PPT`.
- Active-project and historical plotting scripts under `/Volumes/Xu Lab/tMoTe2_Measuring`.
- Examples include Shuai MT43 hysteresis panels, A5 dot filling-vs-field maps, C7 reflectance/dR maps, RMCD dual-gate maps, PL gate sweeps, and CrI3/RMCD paper-era outputs.

First principle:
- A good plot highlights the physical feature, not the plotting pipeline. Choose limits, observables, and aspect ratios to make the regime boundary, hysteresis, dispersion, peak shift, or contrast visible without exaggerating artifacts.

Default figure style:
- White background, black axes, no chartjunk.
- Axis labels with units on every standalone panel.
- Tick direction out; avoid top/right spines for simple line plots, but boxed heatmaps are acceptable.
- Use larger text than Matplotlib defaults: roughly 8-9 pt for paper panels, 12-16 pt for Slack/deck quicklooks.
- Prefer 300 dpi PNG for Slack/deck review and PDF/SVG for paper-facing figures.
- Avoid titles in final paper panels unless the title carries an experimental condition; use panel labels and captions instead.

Color and bounds:
- Sequential intensity maps: use perceptually uniform maps (`viridis`, `magma`, `inferno`, or project-established equivalent), with robust percentile bounds rather than raw min/max.
- Diverging signed maps such as RMCD, dR/R, contrast, difference, residual, or slope: use a zero-centered diverging map (`RdBu_r`/`coolwarm`) with symmetric limits unless there is a project-specific reason not to.
- Never use a rainbow colormap for quantitative maps.
- For noisy spectra/maps, clip color bounds to reveal persistent structure while noting the clipping; do not let a single hot pixel set the scale.
- If the relevant feature is a weak contrast on a large background, subtract or normalize using the project’s existing convention before plotting.

Common unit conventions:
- Photon energy: `Energy (eV)` or `Photon energy (eV)`.
- Magnetic field: `B (T)`.
- Displacement field: `D (V/nm)`.
- Carrier density: `n (10^12 cm^-2)` unless the project explicitly uses `cm^-2`.
- Moire filling: `nu` or `moire filling nu`; use the Greek symbol in rendered labels when supported.
- RMCD: `RMCD (%)`.
- Reflectance contrast: `dR/R` or the project’s exact script convention.
- PL intensity: `PL intensity (a.u.)` or `Integrated PL (a.u.)`.

Map conventions:
- Use `pcolormesh`/`imshow` with correct axis extent and `origin="lower"` semantics; do not silently flip axes.
- For irregular n-D grids, use scatter or triangulation rather than implying a rectangular grid.
- Preserve physically meaningful aspect ratios when comparing n and D; otherwise use aspect that maximizes readability without distorting interpretation.
- For filling maps, show integer/fractional filling ticks when they are the physics.
- For hysteresis sweeps, overlay up/down traces with consistent colors and label sweep direction; do not average away coercive behavior.

Line and marker conventions:
- Use direct, high-contrast colors and modest line widths.
- For paired sweeps: blue/orange or blue/red is acceptable, but label direction explicitly.
- Use markers only when discrete sampling matters; avoid giant markers that hide scatter density.
- Show error bars or fit uncertainty when the claim depends on them.

Analysis-before-style checks:
- Confirm the project’s trusted observable from scripts or prior summaries before plotting.
- Confirm whether the axis should be voltage, density, displacement field, or filling factor.
- Confirm whether background subtraction, offset subtraction, sym/antisym conversion, or reference normalization is part of the project convention.
- For peak tracking, prefer continuity-aware fits/tracks over independent broad-window maxima when features are close or hopping is plausible.

Quicklook vs paper:
- Quicklook plots may use titles with full conditions and slightly larger fonts.
- Paper/deck-ready plots should move conditions into annotations/captions and keep the visual clean.
- A plot is not ready if the colorbar lacks units, the axis convention is ambiguous, or the main feature is only visible after verbal explanation.
