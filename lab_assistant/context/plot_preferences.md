# Plot Preferences

Primary plotting canon:
- Use `context/plotting_practices.md` and `skills/plot-generation.md` before generating new analysis figures.
- Use `tools/plotting/openscience_plot_style.py` for Python/Matplotlib plots when possible.

Preference learning loop:
- Treat plot refinement conversations as durable preference data, not one-off edits.
- The first time a project/person asks for a plot style, it is acceptable to iterate.
- The second time, recover the prior project/person convention before plotting and start close to the accepted style.
- Store stable preferences at the narrowest useful scope:
  - global plotting defaults in this file or `context/plotting_practices.md`
  - project-specific observables, normalizations, and figure conventions in `context/projects/` or `knowledge/projects/`
  - individual presentation preferences in the relevant people/project context when known
- When sending plots or figures, provide robust artifacts rather than only inline descriptions: at minimum a review PNG and the generating code/path; include PDF/SVG or source data when reuse is likely.
- For experimental runs, prioritize plots that expose the physical feature or decision point, not plots that merely prove the pipeline ran.

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
