# Field guide (OpenScience)

Purpose: a compact “how to interpret + how to present” reference that I can consult quickly when generating plots, answering questions, or updating decks.

## 1) North stars (how we work)

- **Corpus-first, people for confirmation**: infer conventions from older decks/scripts/data before waiting on replies; DM owners to validate story + record corrections. (Isaac directive)
- **Academic slides**: claims + evidence + uncertainty; avoid corporate language (e.g., “hero plot”). (Isaac directive)
- **Interesting + literature-linked**: each analysis block should try to elevate at least one concrete “interesting” observation and attach a brief literature analog (often best in speaker notes). (Isaac directive)

## 2) Dataset overview (tMoTe2 / moiré)

- System: **alternating-twist trilayer MoTe₂**, twist angle ~3.9°, hBN encapsulated.
- Typical device parameters (as currently believed): **dt ≈ 14 nm**, **db ≈ 15 nm** (older scripts may contain incorrect 8/10 nm).
- Modalities present in the corpus:
  - **PL** (spectra vs gate/B/position)
  - **Reflectance** (dR/R, MCD; R/L channels)
  - **RMCD** (hysteresis loops vs gate/D/B/T)

## 3) Common variables / file semantics

### PL
- Typical `.mat` vars: `I` or `dat` (spectra), `w` (wavelength), `Vt`, `Vb`, optional `currentBfield`.
- Often meaningful derived quantities:
  - integrated intensity in a chosen window (commonly ~1.04–1.13 eV)
  - peak energy / linewidth from single- or multi-peak fits (preferred over argmax when features overlap)

### Reflectance
- Typical `.mat` vars: `datR`, `datL`, `w`, `Vt`, `Vb`.
- Conventions differ by person/run; *must anchor to the project’s existing script*.
  - Example (WJL-style B79): use reference-normalized `(I-ref)/ref`, smooth, take `d/dE`, then track **most-negative minimum** in a specified energy window (e.g. 1.08–1.108 eV).

### RMCD
- Typical `.mat` vars: `RMCD_down`, `RMCD_up`, `Bsel`, `Vtset`, `Vbset`.
- Offsets like -0.3, -0.7 are often **instrumental background subtraction**, not physics.

## 4) Coordinates + calibrations (n, D, ν)

- Many analyses require converting `(Vt, Vb)` → `(n, D)`.
- **Do not assume one global convention**; prefer the project’s calibration code (e.g. `calcgatesnD.m`) and record:
  - dielectric constants assumed
  - gate distances (dt, db)
  - sign conventions for D and n
- Filling calibration (historical, may need re-derived from features): `v1 ≈ -5.5`, `v23 ≈ -3.88`.

## 5) Naming conventions (recurring patterns)

- Filenames often encode session + sequence + parameters:
  - `XX_YY_description_power_time_grating_wavelength_parameter.mat`
- Negative values may use an `n` prefix (e.g., `n0p34` = -0.34).
- “Spot 1–5” denote different beam positions on the *same device* (unless labeled as different run/cooldown).

## 6) Deck conventions (practical)

- Follow lab-member deck norms:
  - avoid placeholder divider slides that look blank/unused
  - section headers should typically be integrated into content slides
- A good PI-facing slide typically has:
  - **What is plotted** (axes + units + conditions: T, B, D/ν window)
  - **1-sentence takeaway** (what changed / what’s surprising)
  - **1–2 “tests next” bullets** (how to validate)
  - provenance goes in notes (file paths/scripts)

## 7) Known “gotchas”

- Apparent sign flips can be caused by **feature crossing / intensity transfer** at fixed-energy slices—verify by fitting peaks and tracking multiple branches.
- Broad-window argmax trackers can **hop features**; prefer continuity constraints or peak fits.

Last updated: 2026-03-13
