# MEMORY.md - Long-Term Memory

## 2026-02-24: First cataloging session

### Dataset Overview
- **Location**: `/data` with 3741 files (3695 .mat, 31 .m scripts, 5 .asv, misc)
- **Single device**: alternating-twist trilayer MoTe₂, twist angle ~3.9°
  - hBN-encapsulated, dt=14nm top BN, db=15nm bottom BN (8/10nm in one old script is wrong)
  - All-optical measurements (no transport) — PL, reflectance, RMCD
  - n0 = 0 (no charge-neutrality offset)
  - Filling calibration: v1 = -5.5, v23 = -3.88 (but should be determined from data features)
  - "Spots 1-5" = different beam positions on same device, same cooldown unless different "run"
  - "Runs" = separate cooldowns (PL, PL_run2, PL_run3; Reflectance through run4)
  - "Spot 3 After Crash" = computer crashed, lost beam position, re-found the spot
  - RMCD offsets (-0.3, -0.7) are instrumental background subtraction
  - Data is exploratory (not published, no manuscript)
  - **Key physics**: FQAH states, magnetic order
    - FCI states observed from D ≈ -0.20 to -0.55 V/nm, peak hysteresis ~D = -0.40 V/nm
    - RMCD hysteresis at fractional fillings (v = -1, -2/3, -1/2, -3/5, -2/5)
    - Streda analysis → Chern number extraction
    - Curie-Weiss fits (1/χ vs T) at v = -1, -2/3, -1/3 from reflectance Tdep data
    - Tdep of magnetic hysteresis at D = -0.33 V/nm

### Three measurement modalities:
1. **PL (Photoluminescence)**: 188 files (run1) + 6 (run2) + 41 (run3)
   - .mat vars: `I` (spectra), `w` (wavelength), `Vt`, `Vb`, optionally `dat`, `currentBfield`
   - Dual-gate sweeps, doping dependence, B-field dispersion, spatial scans
   - Integration around ~1.04-1.13 eV (trion/exciton features)
   
2. **Reflectance**: 25 (run1) + 22 (run2) + 128 (run3) + 2472 (run4)
   - .mat vars: `datR`, `datL` (R/L circular polarization), `w`, `Vt`, `Vb`, optionally `currentBfield`
   - Differential reflectance (dR/R), MCD (magnetic circular dichroism)
   - Run4 is massive: Curie-Weiss temperature dependence, B-field sweeps
   
3. **RMCD (Reflective MCD)**: 858 files
   - .mat vars: `RMCD_down`, `RMCD_up` (hysteresis), `Bsel`, `Vtset`, `Vbset`
   - Magnetic hysteresis loops at various doping/D-field
   - Multiple spots (1-5), temperature dependence, D-sweep hysteresis

### Naming conventions:
- `XX_YY_description_power_time_grating_wavelength_parameter.mat`
- XX = experiment day/session number, YY = measurement sequence
- Parameters encoded: D (displacement field), v (filling), Bset (B-field index), Vset (voltage index), Tset (temperature index)
- Negative values: `n` prefix (e.g., `n0p34` = -0.34)
- Spots identified by position (X, Y coordinates) or number

### Key physical quantities:
- Carrier density n (10¹² cm⁻²)
- Displacement field D (V/nm)
- Magnetic field B (T)
- Temperature T (K)
- Filling factor v (integer fractions of moiré unit cell)
