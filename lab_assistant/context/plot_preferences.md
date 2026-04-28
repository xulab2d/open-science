# Plot Preferences

Primary plotting canon:
- Use `context/plotting_practices.md` and `skills/plot-generation.md` before generating new analysis figures.
- Use `tools/plotting/openscience_plot_style.py` for Python/Matplotlib plots when possible.

Default plotting preferences inferred from legacy feedback:
- Use the project’s established observable when one exists.
- Label axes and units clearly.
- Keep figures readable in Slack and decks without requiring zoom.
- Prefer a small number of strong figures over dense multi-panel grids unless the grid itself tells the story.
- Use consistent scales and colormaps across directly comparable panels.
- Show the condition that matters: field, temperature, gate regime, polarization, or sweep direction.

What to avoid:
- Arbitrary styling rules detached from project norms.
- Tiny text and crowded layouts.
- plots that foreground pipeline mechanics instead of the scientific signal
- relying on speaker notes to carry the main point

Project-specific reminders from legacy notes:
- Reflectance and related optical metrics can be highly convention-dependent; anchor to the project’s own scripts.
- Broad-window peak picking can hop features; continuity-aware tracking or fitting is often preferable.
- Some “background” files should not be averaged across frames without checking project practice.
