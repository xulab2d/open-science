# A5 AAtA Dot

Status: active project summary. Owners: Zengde She and Weijie Li.

## Broad Overview

A5 is an AAtA-dot tMoTe2 PL/PLE spectroscopy project on the old Attodry. The main physics target is localized or dot-like optical structure that evolves with filling, displacement field, magnetic field, polarization, excitation wavelength, and power.

The project should be treated as both a spectroscopy problem and a provenance problem: peak tracking, background subtraction, gate/filling conversion, and spot labels can change the apparent story.

## Recent Developments

June 2026 NAS evidence is strong. The active deck `ZDS_WJL_A5_AAtA_dotPLE_and_optical_control_measure.pptx` was modified on 2026-06-15, and recent files include PLE, power dependence, wavelength-dependent optical control, lifetime, and PL dual-gate analysis.

The current scientific thread is dot PL/PLE features around integer and fractional fillings, especially near `nu = -1` and `nu = -2/3`. Intermediate spectral branches are being tested with polarization, power, wavelength, and optical-control-style measurements; treat any fractional-charge or bound-state language as a working interpretation until calibrated linecuts confirm it.

## Watchpoints

- Keep dot1, dot3, spot, and branch labels separate unless a project deck or script ties them together.
- Use project scripts for gate/filling conversion.
- Do not promote peak-tracking branches to physical states without raw/processed linecut checks.

## Scientific aim

A5 is a tMoTe2 AAtA-dot project on the old Attodry, centered on PL spectroscopy of dot-like or localized optical features. The working question is whether the observed spectral structures track real filling-, field-, or displacement-field-dependent physics, or whether some apparent structure is produced by peak-tracking, background subtraction, or calibration choices.

The project is most useful to approach as a spectroscopy-and-provenance problem:

- identify which PL features are reproducible across B, n, and D sweeps
- track peak energy and intensity without confusing Zeeman-split shoulders for new branches
- keep the gate-to-density and filling-factor conversion visible on every derived plot
- separate dot1, dot3, and other spot labels until their physical relationship is confirmed

## Current browser-facing example

![A5 dot3 peak intensity stacked by magnetic field](/Users/xulab/openscience/old_openclaw/out/plots/a5_dot3_peakIntensity_script_stacked_B_offset150_with4T.png)

This plot is an OpenScience-generated reproduction of Zengde's dot3 peak-intensity workflow. It stacks smoothed PL peak intensity versus doping density for datasets from approximately 0.01 T to 8 T, using the project script logic as closely as possible.

Interpret it as a processing and visualization checkpoint, not a final physical conclusion.

## Data families

Known active families from legacy notes and generated artifacts:

- `data/01PL/spot3dot1 dispersion/`
- `data/02PL/dot1dispersion/`
- `data/02PL/dot3dispersion_pol/`
- dot1 n-D sweeps with `Bset*` naming
- dot3 n-sweeps at nominal fields 0.01 T, 1 T, 2 T, 3 T, 4 T, 5 T, 6 T, 7 T, and 8 T

Canonical NAS root:

`/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`

## Analysis conventions to preserve

Gate conversion should use the project acquisition/analysis scripts, not generic defaults. Notes recovered from legacy scripts indicate:

- top-gate thickness near `TG = 33.5 nm`
- bottom-gate thickness near `BG = 27.4 nm`
- capacitance conversion based on an assumed BN dielectric constant near epsilon_r = 3
- density reported in units of `10^12 cm^-2` in several helper workflows

For filling-factor assignment, keep the affine model explicit:

`nu = (n - n0) / n_m`

Do not hard-code `n0` or `n_m` from another device. When possible, determine them from trusted anchor features in the same data family and report the anchors used.

## Peak tracking notes

The dot3 peak-intensity workflow used:

- background subtraction from a matching background file
- dark-region bias correction using high-pixel-index regions
- wavelength-to-energy conversion using `E = 1240 / lambda`
- continuity-aware peak search across sweep points
- Savitzky-Golay smoothing with window 9 and order 3

For dot1 and n-D sweeps, be especially careful around low doping and finite B. Legacy notes warn that Zeeman splitting can introduce extra peaks; those should not automatically be promoted to separate physical branches without spot checks.

## What is known

- The project intent was to search for dot-like PL features in another AAtA sample.
- Prior summary slides focused on integrated intensity versus B and n, integrated intensity versus B and filling factor, and tracked peak energy versus B and filling factor.
- A Streda-style comparison was attempted, but legacy notes say measured slopes were smaller than a simple formula, possibly because dielectric assumptions or calibration offsets need refinement.
- There were candidate multi-branch features near fractional fillings such as -1/3 and -2/5, but these still need confirmation from fine linecuts and consistent calibration.

## Open questions

- What is the physical identity of dot1 and dot3: the same localized potential, different positions, or different measurement families?
- Which features are the canonical anchors for `nu = -1` and `nu = -2/3` in dot1 n-D sweeps?
- Is the density offset `n0` assumed zero, fitted, or inherited from a run-specific calibration?
- Which BN thickness and dielectric assumptions should be treated as canonical for each dataset?
- Which generated plot or deck should be the source of truth for PI-facing summaries?

## Useful local anchors

- Project context: `/Users/xulab/openscience/lab_assistant/context/projects/a5_dot.md`
- Filling assignment SOP draft: `/Users/xulab/openscience/old_openclaw/memory/sops/filling_assignment_dot_project.md`
- Dot3 peak-intensity note: `/Users/xulab/openscience/old_openclaw/memory/projects/a5_dot3dispersion_pol_peak_intensity_plots.md`
- Old project context: `/Users/xulab/openscience/old_openclaw/memory/projects/zengde_weijie_a5_aatA_dot_oldattodry.md`

## Next useful work

- Pick one representative dot1 n-D sweep and produce a compact calibration panel showing raw PL, background-subtracted PL, tracked peaks, and selected filling anchors.
- Link Bset indices to actual B fields from the `.mat` metadata.
- Promote one canonical plot set into a stable summary folder once Zengde or Weijie confirms the calibration convention.
