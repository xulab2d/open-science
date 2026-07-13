# Current Project Snapshot, 2026-07-07

Purpose:
- Recover project context after the documentation hiatus.
- Use NAS evidence to refresh the lab-assistant view of current work.
- Keep observations, inferences, and uncertainty separate.

Evidence posture:
- Primary evidence is NAS metadata and project artifacts visible on 2026-07-07.
- Strong evidence means recent high-value files such as `.mat`, `.m`, `.ipynb`, `.pptx`, or analysis figures, plus deck text or script names that identify the measurement.
- Directory mtimes alone are weak evidence.
- The 2026-07-07 13:11 catalog pulse was useful as a pointer but marked sync backfill, so same-day "new file" status should not be interpreted as same-day acquisition.

## Strong Current tMoTe2 Projects

### A5 AAtA Dot

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`

People inferred:
- Zengde She
- Weijie Li

Recent evidence:
- 156 high-value files modified since 2026-06-01.
- `ZDS_WJL_A5_AAtA_dotPLE_and_optical_control_measure.pptx` modified 2026-06-15.
- Recent files include PLE, power dependence, wavelength-dependent optical control, lifetime, and PL dual-gate analysis scripts/data.

Scientific read:
- Active work is on dot PL/PLE features around fractional or integer fillings, especially near `nu = -1` and `nu = -2/3`.
- The deck frames intermediate spectral branches as possible bound fractional-charge-like states, but this is still interpretation rather than settled fact.
- Polarization, power dependence, wavelength dependence, and optical-control-style measurements are being used to test which branches are robust.

Watchouts:
- Keep dot labels and spot labels separate.
- Use project scripts for gate and filling conversion.
- Do not promote peak-tracking branches to physical states without linecut and calibration checks.

### A13 AABB

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A13_AABB_oldattodry`

People inferred:
- Zengde She
- Weijie Li

Recent evidence:
- 111 high-value files modified since 2026-06-01.
- `Zengde_Weijie_A13_AABB_oldattodry_measure.pptx` modified 2026-06-24.
- Recent files include dual-gate reflectance maps, polarization reflectance, `dR_dualgatesweep_peak_analysis_LF_WJ_gif_trilayer.m`, and resonance tests.

Scientific read:
- A13 is focused on AABB/twisted-AA/twisted-BB optical response.
- Deck text reports weak FM or polarization features, but also notes early bad data from alignment/polarizer issues.
- Current emphasis is verifying whether weak R-L features around selected spots and D fields are real.

Watchouts:
- Treat the "maybe FM" language as tentative.
- Track alignment and reference choices when comparing early and later reflectance maps.

### A18 BAAB

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A18_BAAB_oldattodry`

People inferred:
- Zengde She
- Weijie Li

Recent evidence:
- 126 high-value files modified since 2026-06-01.
- `Zengde_Weijie_A18_BAAB_oldattodry_measure.pptx` modified 2026-06-19.
- Recent files include polarized dual-gate maps, reflectance filter-difference scripts, resonance scans, and BAAB/BAB region maps.

Scientific read:
- A18 is probing BAAB and related four-layer/twisted-region resonances.
- Deck text identifies weak resonances near 1.118 eV, 1.08 eV, and 1.057 eV, with polarized dual-gate checks at B = 0.2 T.
- A possible polarization feature appears on the 1.06 eV resonance; the deck also notes dual-gate asymmetry and possible AA-interface relaxation.

Watchouts:
- Reference choice matters; the deck notes that bare-hBN versus dense-doping references can change the result.
- Region assignment among ABA bilayer, BB bilayer, BAAB, tBB, and BAB is central.

### A22 BAAB Scanning PL

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_A22_baab_ScanningPL`

People inferred:
- Zengde She

Recent evidence:
- `Zengde_A22_BAAB_ScanningPL.pptx` and `00_SPATIALMAP_5s_vbn1.mat` modified 2026-06-24.
- The root contains scanning-PL and gate-analysis scripts including `xyscananalyzer_scanningPL.m`, `pl_dualgatesweep_analysis_LF.m`, and `calcgatesnD.m`.

Scientific read:
- This appears to be an early-stage BAAB scanning-PL project.
- Current evidence is setup/spatial mapping rather than a mature interpretation.

### MT48 Helical 1+1+1

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Shuai_CWB_MT48_attodry911`

People inferred:
- Shuai Yuan
- Weijie Li
- Christiano Wang Beach

Recent evidence:
- 67 high-value files modified since 2026-06-01.
- `Shuai_WJL_MT48_attodry911_run2.pptx` modified 2026-06-15.
- Recent data are PL dual-gate maps at 0 T and 0.1 T, plus dR/R and PL maps.

Scientific read:
- MT48 is a 4-degree helical 1+1+1 tMoTe2 project.
- Deck text reports polarized regions at zero field and finite-B-induced polarization in another region.
- The deck connects optical features to transport-like filling assignments, including `nu = -1`, `nu = -4/3`, a large insulating state around D = 0 and n = -6, and possible lower-doping fractional features.

Watchouts:
- Filling assignment is explicitly tied to transport interpretation; check the transport calibration before reusing labels.

### D88 Family

Roots:
- `/Volumes/Xu Lab/tMoTe2_Measuring/courtney_christiano_D88_1+1+1_AAA_4deg_attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/courtney_christiano_D88_run2_AAA_attodry522`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Yue_D88_1+1+1_AAA_4deg_Attodry522_coilmeasurement`

People inferred:
- Courtney
- Christiano Wang Beach
- Yue

Recent evidence:
- Main D88 root has high-value files modified 2026-06-03 and 2026-06-15.
- D88 run2 has extensive April-May high-value files.
- Yue coil-measurement root has 162 high-value files modified since 2026-06-01, including `Domain_identification.ipynb`, `Field_dependence.ipynb`, and linecut `.mat` files through 2026-06-21.
- `Yue_D88_1+1+1_AAA_4_attodry522.pptx` identifies fab as Courtney and measurement as Yue.

Scientific read:
- D88 remains an active benchmark and comparison project for optical/RMCD signatures in 1+1+1 AAA tMoTe2.
- Main D88 deck text emphasizes RMCD hysteresis at `nu = -1` and `nu = -2/3`, optical fan diagrams, and using `dE/dn` to track kink-like correlated-state signatures when PL intensity dips are subtle.
- Yue's coil-measurement deck contrasts modulation and pulsing modes and reports linecut measurements aimed at separating trivial magnetic-boundary MCD from possible nontrivial/topological MCD.

Watchouts:
- Coil-mode data have different resolution/broadening tradeoffs; do not compare modulation maps and pulsing linecuts as equivalent observables.
- For D88 optical fans, energy-derivative features may be more informative than intensity dips.

### D135 5-Degree Helical

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/courtney_christiano_D135_1+1+1_5deg_helical_attodry911`

People inferred:
- Courtney
- Christiano Wang Beach

Recent evidence:
- `courtney_christiano_D135_5deg_helical_attodry911.pptx` modified 2026-06-10.

Scientific read:
- D135 is a 5-degree 1+1+1 helical tMoTe2 optical project.
- Deck text frames the problem around PL/dR dual-gate features, field dispersion, slope/topology, and possible fragility of a state at high B.
- There is uncertainty in filling assignment; one slide says a feature assigned as `nu = -2` could be `nu = -1`.

Watchouts:
- Preserve the deck's uncertainty around filling labels and high-field topology before making summary claims.

### D24 and D25 Scanning PL

Roots:
- `/Volumes/Xu Lab/tMoTe2_Measuring/CWB_D24_ScanningPL`
- `/Volumes/Xu Lab/tMoTe2_Measuring/CWB_D25_ScanningPL`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Christiano_WJL_Attodry911`

People inferred:
- Christiano Wang Beach
- Weijie Li

Recent evidence:
- D24 has 15 high-value files modified since 2026-06-01 and a deck saved 2026-06-21.
- D25 has 15 high-value files modified since 2026-06-01.
- `Christiano_WJL_Attodry911` has 34 high-value files modified since 2026-06-01, including PL dual-gate analysis and sample D25 deck text.

Scientific read:
- D24 is labeled "3 Alternating Trilayer tMoTe2" with gate-dependent scanning-PL style measurements.
- D25 is labeled "Helical AAA 6 tMoTe2 Scanning PL (4K)".
- The Christiano/WJL Attodry911 root appears tied to Sample D25 and contains PL dual-gate maps at 1160 nm center.

Watchouts:
- D25 appears in multiple roots; avoid treating those as independent projects until naming is reconciled.

### Julian AHS3

Roots:
- `/Volumes/Xu Lab/tMoTe2_Measuring/Julian_AHS3_Attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Julian_AHS3_ScanningPL`

People inferred:
- Julian

Recent evidence:
- Attodry911 root has 217 high-value files modified since 2026-05-01 and 2 since 2026-06-01.
- `Julian_AHS3_Attodry911_measure.pptx` describes AHS3 RMCD, PL, dual-gate, and hysteresis measurements.
- ScanningPL root has April 2026 PL/dR gatedep files and a scanning-PL measurement deck.

Scientific read:
- AHS3 is an optical and magnetic project involving RMCD spatial maps, RMCD dual-gate maps, B-sweep hysteresis, PL, and dR.
- Deck text reports clear FM hysteresis at `nu = -1`, coercive fields around 100 mT near one doping, and persistent features at 0 T and 10 mT.
- There is also a faint feature near `nu = -2` at negative D that the deck marks as potentially interesting but not settled.

Watchouts:
- Electrical-interference notes appear in the deck; treat early faint features carefully.

## May or Quieter Current Signals

### D93 Run2

Root:
- `/Volumes/Xu Lab/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522`

People inferred:
- Christiano Wang Beach
- Yi-Fan Zhao

Evidence:
- Latest high-value NAS mtimes are late April 2026, including Curie-Weiss and hysteresis PDF/script outputs.

Scientific read:
- Still relevant to RMCD, Curie-Weiss, and magnetism-comparison logic, but not a June-active root by file mtime.

### MT50 and MT52 Transport-Style Roots

Roots:
- `/Volumes/Xu Lab/tMoTe2_Measuring/260504-PPMS-MT50`
- `/Volumes/Xu Lab/tMoTe2_Measuring/260508-MRI-MT52`

Evidence:
- MT50 has May 2026 dual-gate processed data and PPMS/CSV files.
- MT52 has May 2026 analysis notebooks and gate-test images.

Scientific read:
- These appear to be transport or magnet/PPMS/MRI-style device work.
- Owner labels are not obvious from the root names, so avoid assigning a person without more context.

### B79, C7, and MT43

Roots:
- `/Volumes/Xu Lab/tMoTe2_Measuring/WJL_Zengde_B79_Attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_WJL_C7_Attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Shuai-MT43-DR911`

Evidence:
- These are still useful context projects, but the July 2026 NAS mtime scan did not show recent high-value activity.

Scientific read:
- Keep their conventions available for interpreting newer Weijie/Zengde or Shuai work, but do not call them June-active without new evidence.

## Active Signals Outside tMoTe2_Measuring

### MnTe

Root:
- `/Volumes/Xu Lab/MnTe`

Evidence:
- Recent files under `2604_Opticool/RMCD/` include Cr-doped birefringence/RMCD-style `.mat` files across sample temperature, field, phase, and focus conditions.

Scientific read:
- Active MnTe work appears to involve Opticool magneto-optical/birefringence measurements on Cr-doped samples.

### SHG

Root:
- `/Volumes/Xu Lab/SHG`

Evidence:
- Recent `.mat` and image files include WSe2, MoTe2, TaS2, lithium-niobate, co/cross-polarized measurements, and sample images.

Scientific read:
- SHG capability and sample survey work are active, spanning transition-metal dichalcogenides and lithium-niobate/MoTe2 interference tests.

### AFM and Fabrication

Roots:
- `/Volumes/Xu Lab/Zengde AFM`
- `/Volumes/Xu Lab/Weijie_AFM`
- `/Volumes/Xu Lab/James Zhang`

Evidence:
- Zengde AFM has June cut/clean records and BG44/BG47 AFM image files.
- Weijie_AFM has recent backgate and sample AFM records, including Bg132-Bg135 and B88/B89/B91/S2-style folders.
- James Zhang has recent Bruker/Icon AFM and D-series device-fabrication records, including D04 and D10-D17 style folders.

Scientific read:
- Fabrication/sample-prep support is active and likely feeding the tMoTe2 optical program and related device work.

## Operational Follow-Ups

- The daemon still watches only the old seed roots: MT43, A5, D93, B79, C7, and one D88 root.
- Add at least A13, A18, A22, MT48, Yue D88 coil, D135, D24, D25, Christiano_WJL, and Julian AHS3 Attodry911 to monitoring if recurring daily summaries should reflect current activity.
- Consider separate daemon treatment for large roots such as D88 run2 or Yue B20 coil measurements to avoid noisy scans.
