# Skill: Plot Generation

Use when:
- Creating a new plot, quicklook, figure panel, deck figure, or paper-facing visualization.
- Translating MATLAB/lab plotting conventions into Python.
- Reviewing whether a generated figure is publication-ready.

Procedure:
1. Identify the project and observable before plotting.
2. Read the relevant project note and nearby project scripts if the observable, axis convention, background subtraction, or color scale is unclear.
3. Apply `context/plotting_practices.md` and `context/plot_preferences.md`.
4. Use `tools/plotting/openscience_plot_style.py` for Matplotlib defaults when possible.
5. Choose axes that match the physics:
- optical gate maps: energy vs `n`, `D`, or filling
- RMCD/magnetic maps: `B`, `n`, `D`, or filling, with signed contrast centered at zero
- transport maps: filling, density, field, temperature, or displacement field as appropriate
6. Choose color bounds deliberately:
- sequential intensity: robust percentile limits, usually not raw min/max
- signed contrast/difference: symmetric zero-centered limits
- weak features: subtract/normalize first using project convention, then choose limits
7. Add the minimum annotations needed to make the figure interpretable without narration.
8. Export both editable/vector and review/raster formats when the plot may be reused.

Default quality bar:
- Clear labels and units.
- Readable in Slack without zoom.
- Colorbar label includes observable and units.
- Main phenomenon is visible without misleading saturation.
- Project-specific conventions outrank global defaults.

Do not:
- Use rainbow colormaps.
- Let outliers set heatmap bounds.
- Hide the scientific takeaway in a title or speaker note.
- Invent a fill-factor conversion when project scripts already define one.
- Average or smooth away hysteresis, splitting, or contrast before checking whether it is the signal.
