# Plot Code Index

Purpose:
- Retrieve prior plotting implementations as precise context for future figure generation.
- Source code remains the ground truth; this file is a compact navigation layer.

Indexed records: 5

## Tags

- `a5`: 3
- `density`: 4
- `displacement`: 2
- `energy`: 5
- `filling`: 3
- `gate_map`: 4
- `hysteresis`: 1
- `magnetic_field`: 4
- `pl`: 5
- `reflectance`: 1
- `rmcd`: 2

## Records

### `scripts/fact_graph_daily_summary.py`
- language: `py`
- tags: `displacement`, `energy`, `gate_map`, `pl`, `rmcd`
- functions: `arxiv_year_counts`, `load_jsonl`, `main`, `medium_curated_arxiv`, `parse_args`, `render_figures`, `render_markdown`, `theme_counts`
- plot calls: `plot`
- labels: `Evidence`; `displacement field`; `rmcd`
- notes: signed magnetic/contrast observable; check whether zero-centered diverging bounds are appropriate

### `scripts/plot_a5_dot1_b_vs_n.py`
- language: `py`
- tags: `a5`, `density`, `energy`, `gate_map`, `magnetic_field`, `pl`
- functions: `load_band_rows`, `main`, `plot_map`, `smooth_along_n`
- plot calls: `imshow`, `savefig`
- colormaps: `magma`, `viridis`
- labels: `02PL`; `B (T)`; `Band-summed PL (a.u.)`; `eV`; `n ($10^{12}$ cm$^{-2}$)`; `plots`
- data/source hints: `*allrange_Bset*.mat`; `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`; `1140c_20s.mat`; `data`
- output hints: `.pdf`; `.png`; `out`; `plots`
- notes: script emits reusable figure artifacts

### `scripts/quicklook_a5_dot1_raw_B_vs_nu.m`
- language: `m`
- tags: `a5`, `density`, `energy`, `filling`, `gate_map`, `magnetic_field`, `pl`
- plot calls: `imagesc`, `exportgraphics`
- colormaps: `turbo`
- labels: `02PL`; `A5 dot1 raw band sum, %.3f-%.3f eV`; `B (T)`; `Band-summed PL (a.u.)`; `\nu`; `plots`
- data/source hints: `*Bset*.mat`; `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`; `1140c_20s.mat`; `data`
- output hints: `a5_dot1_raw_band_sum_B_vs_nu.png`; `out`; `plots`
- notes: uses rainbow-like colormap; treat as legacy unless project convention requires it; contains filling-axis logic; inspect conversion constants before reuse; script emits reusable figure artifacts

### `scripts/quicklook_a5_dot1_raw_B_vs_nu.py`
- language: `py`
- tags: `a5`, `density`, `energy`, `filling`, `gate_map`, `magnetic_field`, `pl`
- functions: `main`
- plot calls: `imshow`, `savefig`
- colormaps: `magma`
- labels: `$\nu$`; `02PL`; `B (T)`; `Band-summed PL (a.u.)`; `eV`; `plots`
- data/source hints: `*Bset*.mat`; `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`; `1140c_20s.mat`; `data`
- output hints: `a5_dot1_raw_band_sum_B_vs_nu_python.pdf`; `a5_dot1_raw_band_sum_B_vs_nu_python.png`; `out`; `plots`
- notes: contains filling-axis logic; inspect conversion constants before reuse; script emits reusable figure artifacts

### `tools/plotting/openscience_plot_style.py`
- language: `py`
- tags: `density`, `displacement`, `energy`, `filling`, `hysteresis`, `magnetic_field`, `pl`, `reflectance`, `rmcd`
- functions: `apply_style`, `axis_label`, `default_cmap`, `figure_size`, `infer_map_kind`, `plot_heatmap`, `plot_hysteresis`, `robust_limits`, `save_figure`, `style_axes`
- plot calls: `pcolormesh`, `plot`, `scatter`, `savefig`
- colormaps: `RdBu_r`, `viridis`
- labels: `$D$ (V/nm)`; `$n$ ($10^{12}$ cm$^{-2}$)`; `Apply compact Xu Lab-oriented Matplotlib defaults.`; `Apply standard axis spine/tick treatment.`; `Energy (eV)`; `Integrated PL (a.u.)`; `PL intensity (a.u.)`; `Photon energy (eV)`
- output hints: `out`
- notes: contains filling-axis logic; inspect conversion constants before reuse; hysteresis-related plot; preserve sweep direction rather than averaging; signed magnetic/contrast observable; check whether zero-centered diverging bounds are appropriate; script emits reusable figure artifacts
