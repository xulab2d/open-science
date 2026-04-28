# Project context: CWB_Yifan_D93_Run2_attodry522

Source path (data cache):
- `data/dropbox_cache/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/`

## What’s in this folder (as of 2026-03-02)

- Data hierarchy:
  - `Data/Spot 3/`
    - `v = -2, D = 0.375 Curie Weiss/` (contains `.mat` hysteresis files)
    - `v = -2, D = 0 Curie Weiss Optimized/` (contains `.mat` files)

- Acquisition / analysis scripts (MATLAB):
  - `RMCD_singlesweep_hf2.m`
  - `RMCD_Tdep_sweep_hysteresis_ethernet_hf2.m`
  - `calcgatesnD.m`

## Inferred modality (needs confirmation)

Based on script names + contents, this project appears to involve **RMCD (reflective MCD) hysteresis** measurements using:

- Zurich Instruments HF2 lock-in (`ziCreateAPISession`, device `dev1139`)
- Magnet control via GPIB (`SetFieldGPIB`, `GetFieldGPIB`, `IsSettledGPIB`)
- Gate sweeps / setpoints (calls to `sweepGatesUpdate_fast`, uses `Vtg_list_20` / `Vbg_list_20` values)
- Temperature control over ethernet (`connect(IP)`, `sample_setSetPoint`, `sample_getTemperature`)

Evidence: see `RMCD_Tdep_sweep_hysteresis_ethernet_hf2.m` and `RMCD_singlesweep_hf2.m`.

## Important parameters seen in scripts (do not assume globally)

- In `RMCD_Tdep_sweep_hysteresis_ethernet_hf2.m`:
  - `dt = 13.5` nm, `db = 11` nm (BN thicknesses). These differ from the “canonical” device BN thicknesses currently recorded elsewhere; treat as **run-/script-specific until confirmed**.
  - Temperature list: `T = [8:0.5:8.5];` (example)
  - B hysteresis range example: `Blim=0.5`, `Bsel=linspace(Blim,-Blim,2500)`

- In `calcgatesnD.m` (not yet reviewed in full): likely defines gate-to-(n,D) conversion and emits `Vtg_list_20`, `Vbg_list_20` vectors.

## Open items / questions

- Confirm measurement modality and schema for `.mat` files in the “Curie Weiss” folders.
- Define what `Vset*` and `Tset*` indices correspond to (actual gate voltages, actual temperature) for indexing.

Owner/contact:
- Yifan: <@U07R010M1DL> (provided by Isaac, 2026-03-02)
