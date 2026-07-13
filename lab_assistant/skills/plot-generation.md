# Skill: Plot Generation

Use when:
- Creating a new plot, quicklook, figure panel, deck figure, or paper-facing visualization.
- Translating MATLAB/lab plotting conventions into Python.
- Reviewing whether a generated figure is publication-ready.

Procedure:
1. Identify the project and observable before plotting.
2. Recover prior plotting conventions before making a figure:
- read the relevant project note and nearby project scripts
- check `context/plot_preferences.md` and `context/plotting_practices.md`
- check `knowledge/canon/plot_code_index.md` for prior plotting implementations with matching project, observable, axis, or output style
- if the requester or project has known preferences, use those before inventing a style
3. If the observable, axis convention, background subtraction, or color scale is unclear, infer from project scripts, indexed plot code, and prior accepted figures before asking.
4. Apply `context/plotting_practices.md` and `context/plot_preferences.md`.
5. Use `tools/plotting/openscience_plot_style.py` for Matplotlib defaults when possible.
6. Choose axes that match the physics:
- optical gate maps: energy vs `n`, `D`, or filling
- RMCD/magnetic maps: `B`, `n`, `D`, or filling, with signed contrast centered at zero
- transport maps: filling, density, field, temperature, or displacement field as appropriate
7. Choose color bounds deliberately:
- sequential intensity: robust percentile limits, usually not raw min/max
- signed contrast/difference: symmetric zero-centered limits
- weak features: subtract/normalize first using project convention, then choose limits
8. Add the minimum annotations needed to make the figure interpretable without narration.
9. Export robust artifacts:
- review PNG for quick inspection
- PDF/SVG for reusable figures when appropriate
- script/notebook path or generated code path
- source/processed data path when it affects interpretation
10. If the user refines the style, labels, observable, normalization, or presentation, capture the stable lesson in the narrowest appropriate canonical context so the next similar plot starts from that convention.

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
