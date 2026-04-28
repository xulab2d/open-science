# Project context: Zengde_Weijie_A5_AAtA_dot_oldattodry

Source path (data cache):
- `data/dropbox_cache/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry/`

## What’s in this folder (as of 2026-03-02)

- Data hierarchy (PL):
  - `data/01PL/spot3dot1 dispersion/` (contains `.mat` files)
  - `data/02PL/dot1dispersion/` (contains `.mat` files)
  - `data/spot3dot1 dispersion/` (contains `.mat` files)

- MATLAB scripts (gate conversion + acquisition + analysis):
  - `calcgatesnD_trilayer.m`
  - `dualGateDep_Keithley_dopingEfield_nonpol_Bfield_oneframe_ZDS.m`
  - `dualGateDep_Keithley_dopingEfield_customgates_nonpol_Trilayer.m`
  - `data/02PL/plot_dualGateDep_nsweep_PL_unpol_offsetsub_WJ_newref.m`
  - `data/02PL/pl_dualgatesweep_peak_analysis_LF_WJ_gif_trilayer.m`

- Presentation:
  - `ZDS_WJL_A5_AAtA_and_dot_oleattoddry (Xu Lab 的冲突副本 2026-02-19).pptx`
    - skim notes: `out/pptx_skim_ZDS_WJL_A5_AAtA_dot_oldattodry_2026-02-19.md`

## Inferred modality (needs confirmation)

This appears to be **dual-gated PL mapping/dispersion** work on a trilayer sample, with:

- Gate control via Keithley (`keithley_setVoltage_TG`, `keithley_setVoltage_BG`)
- Magnet control via GPIB (`SetFieldGPIB`, `IsSettledGPIB`)
- Spectrometer/CCD acquisition via `getLF()` object (likely LightField) with `set_exposure`, `set_frames`.

Evidence: `dualGateDep_Keithley_dopingEfield_nonpol_Bfield_oneframe_ZDS.m`.

## Key parameters + naming hints seen in scripts

From `dualGateDep_Keithley_dopingEfield_nonpol_Bfield_oneframe_ZDS.m`:

- Gate limits:
  - `tglimit = [-9.6 9.3]`, `bglimit = [-6.4 7.7]`
- Gate dielectric thickness variables:
  - `TG = 33.5` , `BG = 27.4` (units appear to be nm; used later in struct as `TG`,`BG`)
- Example B-field loop:
  - `Bfield = [6:-0.2:6];` (as written this is a constant 6T; might be placeholder)
- Two gate sweeps (`nsweeps=2`) with two resolutions (`nameend={'allrange','fine'}`)
- Saved filename pattern includes `..._Bset{index}` where index is `p+4` in the example code.

From `calcgatesnD_trilayer.m`:

- Converts between (Vtg, Vbg) and (n, D) using capacitance model:
  - `ctg = 3*eps0/(33.5 nm)`, `cbg = 3*eps0/(27.4 nm)`
  - derives coefficients a,b,c,d and computes VTG/VBG from nvals,Dvals.
- Contains comments describing nonuniform spacing in filling / density sampling.

## Owner/contact

- Zengde: <@U09CPJBHCUA>
- Weijie: <@U05DLUMMDST>

## Context from PPTX (2026-02-19 conflict copy)

From skim of the project PPTX (see `out/pptx_skim_ZDS_WJL_A5_AAtA_dot_oldattodry_2026-02-19.md`):

- Project intent: “Try another AAtA sample and search for dots” (scanning PL → identify spots/dots).
- Gate test / scan ranges explicitly listed:
  - Tg approx -8:8 (limits also shown Tg –9.6:9.3)
  - Bg approx 5:6 (limits also shown Bg –6.4:7.7)
  - thickness notes: 27.4 nm and ~35 nm (likely BN thicknesses; match script variables BG/TG).
- Physics/analysis notes:
  - “Check FE of the dot: no clear FE in dualgate” and “No offset seen in the FM”.
  - Streda comparison: measured slope smaller than formula; maybe dielectric constant of BN (currently assumed eps_r≈3) needs adjustment.
  - Peak-finding pitfall: Zeeman splitting introduces extra peak at low doping; suggests higher B-field data is needed for precise feature/Chern identification.
  - n–D / filling–D maps show possible multi-branch behavior near -1/3 and -2/5 that they plan to confirm with fine linecuts.

## Open items / questions

- Define exactly what “dot1dispersion”, “spot3dot1 dispersion”, and “nD sweep” mean (axes/units; what ‘dot1’ refers to; relation to x/y coordinates).
- Confirm the mapping from `Bset*` indices to actual B field values in the saved `.mat` files.
- Confirm which thicknesses/dielectric assumptions are canonical for this project vs placeholders.
