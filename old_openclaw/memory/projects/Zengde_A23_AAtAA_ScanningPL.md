# Zengde A23 — ScanningPL (notes)

Last updated: 2026-03-31

## Quick conventions inferred from xyscananalyzer_scanningPL.m

Source
- tMoTe2_Measuring/Zengde_A23_AAtAA_ScanningPL/xyscananalyzer_scanningPL.m

Observation (code-level)
- Uses `B = I` (so expects loaded variable `I` with shape ~ (wavelength_px, x_index, y_index)).
- Energy axis: `energy = 1240./w` (eV, with w in nm).
- Hard-coded spatial axes (not read from file):
  - `x = linspace(1,28,55)`
  - `y = linspace(0,30,61)`
- Integrated-intensity map:
  - Integration window: `intlim = [1.07 1.17]` eV
  - Pixel range computed via `findPixel(energy, intlim(2/1))` (assumes a `findPixel` helper exists)
  - Background: constant `bkg = 580` counts
  - `It(i,j) = sum(B(range,j,i) - bkg)`
- Peak-energy map:
  - Peak defined as argmax within the same energy window: `peak(i,j) = energy(range(p))`
  - Mask/threshold: set peak to NaN unless `abs(It(i,j)) > addlimit` with `addlimit = 5600`
  - Peak-energy color scale used: `caxis([1.1, 1.17])`

Implications / open questions
- The spatial axis (x,y) is currently assumed from scan settings rather than read from metadata; if the scan grid changes, the map axes will be wrong.
- The constant background (580) and It-threshold (5600) are baked in; may need to confirm if these are stable across sessions or should be estimated per dataset.
