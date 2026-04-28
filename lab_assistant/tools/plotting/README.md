# Plotting Toolkit

Purpose:
- Provide small, reusable helpers for paper/deck-ready Xu Lab plots.
- Keep plotting choices explicit, repeatable, and easy to tune from lab feedback.

Files:
- `openscience_plot_style.py`: Matplotlib style helpers, robust color limits, labels, and heatmap defaults.

Use:
```python
from openscience_plot_style import (
    apply_style,
    plot_heatmap,
    robust_limits,
    save_figure,
)

apply_style(context="deck")
fig, ax = plt.subplots()
mesh = plot_heatmap(ax, x, y, z, observable="rmcd", xlabel="moire filling $\\nu$", ylabel="D (V/nm)")
save_figure(fig, "figure_name", formats=("png", "pdf"))
```

Rules:
- Import this toolkit for new Python plots unless a project already has a better established script.
- Treat the helper as defaults, not law. Override explicitly when the project demands it.
- If a repeated override improves figures, update this toolkit and `context/plotting_practices.md`.
