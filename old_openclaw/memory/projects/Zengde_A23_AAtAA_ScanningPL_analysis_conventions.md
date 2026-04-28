# Zengde A23 — ScanningPL analysis script conventions

Last updated: 2026-04-01

## pl_Dfielddep_analysis_LF.m
Source
- tMoTe2_Measuring/Zengde_A23_AAtAA_ScanningPL/pl_Dfielddep_analysis_LF.m

Observation (code-level)
- Expects a loaded struct `d` with fields: `I`, `w`, `Vt`, `Vb`.
- Energy axis: `energy = 1240./d.w` (eV).
- Background handling is currently a constant:
  - `dbkg = 300; I = d.I - dbkg; bkg = mean(I(1:50,:)); I = I - bkg;`
  - So: subtract 300 counts, then subtract the mean of the first 50 pixels as an additional offset.
- Gate→(D,n) conversion uses fixed thicknesses:
  - `dt = 43 nm`, `db = 30 nm`
  - `Dfield = 3/2*(Vt/dt - Vb/db)` (units intended V/nm)
  - `nn = 16.573*(Vt/dt + Vb/db) - n0` with `n0=0` and comment claims units: 10^-12 cm^-2.
- Plotting: pcolor(energy, Dfield, I') with linear colorscale; example title hard-codes a specific n.

Open questions / risks
- `16.573` prefactor: likely (eps0*epsr/e)*something; worth confirming if this constant is device-specific.
- Background strategy (300 + first-50-px mean) may depend strongly on spectrometer settings; could bias integrated intensity.

## gatedep_nopol_LF_multisweep.m
Source
- tMoTe2_Measuring/Zengde_A23_AAtAA_ScanningPL/gatedep_nopol_LF_multisweep.m

Observation (measurement script)
- Uses LightField acquisition (LF.acquire) and constructs `dstruct` with fields:
  - `I` (1340 x N), `Vt`, `Vb`, `spectime`, `w`
- Uses the standard gate conversion with eps0 and dielectric factor 3:
  - `cbg = 3*eps0/(db*1e-9)`, `ctg = 3*eps0/(dt*1e-9)`
  - `a,b,c,d` derived and then:
    - `Vb=(c*n - a*D)/(b*c - a*d)`
    - `Vt=(d*n - b*D)/(a*d - b*c)`
- This script sets:
  - `dt=43 nm`, `db=30 nm`
  - sweep example: `nn{1} = 1e12*linspace(-4,4,200)`; `D{1}=0`
- Safe gate ranges:
  - `VtSafeRange = [-5.5, 6.5]`, `VbSafeRange = [-7.5, 5.5]`

Open questions / risks
- Potential bug: range-check print uses `Vt{n}(N)` before `N` is defined in that block.
- It assumes DAQ channel mapping [1,3] for TG/BG in sweepGatesUpdate_fast.
