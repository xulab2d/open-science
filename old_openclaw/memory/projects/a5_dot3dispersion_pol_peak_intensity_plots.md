# A5 dot3dispersion_pol — peak intensity vs n stacked-by-B plots

Date: 2026-03-20
Owner/contact: Zengde She (Slack <@U05DLUMMDST>)

## Task
Generate stacked curves of "smoothed peak intensity" vs doping density n for multiple B-field datasets (0.01T→8T), plus a normalized version, following Zengde’s MATLAB script `plot_nsweep_intreda.m`.

## Input datasets (Slack-provided mats)
Stored locally under:
- out/inbound_zengde_2026-03-20/
  - 02_21_dot3nDsweep_0p01T.mat
  - 02_21_dot3nDsweep_1T.mat
  - 02_21_dot3nDsweep_2T.mat
  - 02_21_dot3nDsweep_3T.mat
  - 02_21_dot3nDsweep_4T.mat
  - 02_21_dot3nDsweep_5T.mat
  - 02_21_dot3nDsweep_6T.mat
  - 02_21_dot3nDsweep_7T.mat
  - 02_21_dot3nDsweep_8T.mat

## Processing (matched to `plot_nsweep_intreda.m`)
- Background subtract using:
  - data/dropbox_cache/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry/data/02PL/dot3dispersion_pol/Fine/1140c_30s_DLC.mat
  - script behavior approximated as: `PL = dat - bcgfinal`, where `bcgfinal = dbkg.dat'`.
- Dark-region bias correction: subtract mean over pixels 990:1000 (Matlab 1-indexed) per spectrum.
- Pixel “hotspot” tweaks: multiply pixels 535, 541, 542, 514 by 1.1 (if in-bounds).
- Convert wavelength to energy: `ev = 1240./w`.
- Convert gates to doping: uses TG=33.5nm, BG=27.4nm (from the .mat fields), and
  - `nn = ((ctg*Vt + cbg*Vb)/e/1e4) * 1e-12` in units of 1e12 cm^-2.
- Peak intensity tracking:
  - dynamic energy-range search per sweep point (seed + continuity window) as in script.
- Smoothing: Savitzky–Golay on the peakIntensity sequence:
  - window=9, order=3.

## Final delivered plots (0.01T bottom → 8T top)
Raw (stacked, offset=150):
- out/plots/a5_dot3_peakIntensity_script_stacked_B_offset150_with4T.png

Normalized (each trace divided by its mean; stacked, offset=0.2):
- out/plots/a5_dot3_peakIntensity_script_norm_stacked_B_offset0p2_with4T.png

Notes:
- Titles were kept minimal per request (quantity vs n/B) and offsets are not stated in the title.
- Legend shows B in Tesla (from `currentBfield` in each .mat).
