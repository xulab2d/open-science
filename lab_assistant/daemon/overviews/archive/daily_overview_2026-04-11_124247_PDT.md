Research updates
- D93 Run2 is the only project with a real research signal in the last 24h window. The activity is a coherent RMCD dual-gate/hysteresis analysis bundle, not broad cross-project churn.
- The newly visible D93 material includes dual-gate RMCD datasets across Spots 1-3, fine sweeps near named filling regimes including `v_n2`, `v_n1`, and `v_n52`, plus a larger `03_12_hysteresis_v_n1_4T_1113nmc_100nW_Vset1.mat` hysteresis dataset.
- Paper-facing D93 figures are now present for `D = 0`, `D = 0.25`, and `D = 0.375`: each has a hysteresis PDF, and matching Curie-Weiss-style `1/@` vs temperature panels. The hysteresis PDFs are RMCD vs field, spanning roughly ±100 mT with ±0.2% RMCD scale.
- The D93 script `plot_rmcd_dualgate_diff.m` compares two RMCD maps directly, converts top/bottom gates into carrier density and displacement field using BN thicknesses of 13.5 nm and 11 nm, and remaps the result onto filling factor. This points to a displacement-field and filling-resolved RMCD contrast comparison, not just single-trace plotting.
- No high-signal scientific changes appeared for Shuai MT43, A5 dot, B79, C7, or D88 after the D93 pulses.

Interpretation
- Scientifically, D93 Run2 appears to be moving from raw RMCD sweeps into figure-ready comparison of magnetic response versus displacement field, filling, temperature, and hysteresis.
- The strongest current signal is “organized magneto-optical analysis exists for D-dependent hysteresis and Curie-Weiss-style behavior,” rather than a confirmed new physical conclusion from the data alone.
- The file modification times matter: most `.mat` data are from February 2026, while the paper-figure PDFs are from April 8-9, 2026. So this is likely newly catalog-visible analysis/backfill, not necessarily new measurements taken this morning.
- The RMCD-difference script makes an explicit subtraction between maps; interpretation will depend on which two conditions are being differenced and whether the grids are truly identical, as the script assumes.

Recommended next actions
- Ask Christiano/Yi-Fan whether the D93 `D = 0`, `0.25`, and `0.375` hysteresis/Curie-Weiss panels are intended for a paper figure or an internal comparison.
- For D93 follow-up, prioritize reviewing the three D-dependent hysteresis PDFs side by side with the matching Curie-Weiss-style panels: the key question is whether displacement field systematically shifts coercivity, RMCD amplitude, or inferred magnetic temperature scale.
- Confirm the filling calibration used in `plot_rmcd_dualgate_diff.m` (`v1 = -5.1`, `v23 = -3.67`) before using its filling-axis maps for scientific claims.
- If a discussion figure is needed, generate a compact D93 quicklook: RMCD hysteresis at each D, corresponding inverse-susceptibility trend, and one dual-gate/filling map with the same color limits.

Operational note
- Catalog health is clean: all watched roots readable, 47 pulse reports in 24h, zero current warnings.
- The morning D93 pulses crossed review threshold; later pulses were quiet. Given NAS backfill context, treat the D93 signal as “newly surfaced organized analysis” unless project owners confirm new acquisition.

Memory/skill updates
- None.