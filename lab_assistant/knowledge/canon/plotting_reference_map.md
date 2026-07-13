# Plotting Reference Map

Purpose:
- Track where OpenScience should look when improving plot style and project-specific visualization conventions.
- Keep this as a reference map, not a bulky image archive.

Machine-readable code index:
- `knowledge/canon/plot_code_index.md`
- `knowledge/canon/plot_code_index.json`
- Refresh with `python3 scripts/index_plot_code.py` after adding reusable plotting scripts.

Primary reference decks:
- `/Volumes/Xu Lab/OpenScience/Summaries/PPT/Shuai_MT43_DR911/Overnight_Shuai_MT43_DR911_SweepB_2026-03-04.pptx`
- `/Volumes/Xu Lab/OpenScience/Summaries/PPT/Zengde_A5_dot1dispersion/ZDS_spot3dotdispersion_scan1_OpenScience_v4_5x2.pptx`
- `/Volumes/Xu Lab/OpenScience/Summaries/PPT/WJL_C7_Attodry911/WJL_C7_Attodry911_04_Ref_redo_summary_2026-03-02.pptx`
- `/Volumes/Xu Lab/OpenScience/Summaries/PPT/CWB_D88_attodry911/OpenScience_benchmark_CWB_D88_attodry911.pptx`

Useful script families:
- RMCD/filling maps: `plot_rmcd_dualgatedep_WJ_filling.m`, `Plot_RMCD_multisweep_WJ.m`, `Plot_RMCD_singlesweep.m`
- PL gate sweeps: `plot_dualGateDep_nsweep_PL_unpol_offsetsub_WJ.m`, `pl_dualgatesweep_analysis_LF*.m`
- Reflectance/dR maps: `plot_dualGateDep_*reflectance*_WJ*.m`, `dR_*analysis_withpol*.m`
- Doping/displacement conversion: `Plot_displacementdopingconv.m`, project-specific `calcgatesnD*.m`
- Legacy style helper: `posterCPlotAxes.m`

Observed conventions to preserve:
- Optical maps often use energy vs `n`, `D`, or filling with robust sequential bounds.
- RMCD/dR/contrast maps should usually use diverging, zero-centered bounds.
- Filling-factor plots often need integer tick marks and explicit conversion provenance.
- Hysteresis panels should preserve up/down sweep traces and show `B (T)` clearly.
- Project scripts encode important reference subtraction and background choices; inspect them before changing observables.

Maintenance:
- Add a new reference only when it changes default plotting behavior.
- Promote concrete behavior changes to `context/plotting_practices.md` or `tools/plotting/openscience_plot_style.py`.
