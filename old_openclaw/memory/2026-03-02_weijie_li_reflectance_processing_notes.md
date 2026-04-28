Canonicalized: `memory/compactions/2026-03-02_compacted_routing_and_paths.md`

# 2026-03-02 — Weijie Li: reflectance processing + dual-gate signal definition

Source: Slack DM from Weijie Li (timestamp Mon 2026-03-02 21:14 PST).

Key notes:
- Reflectance spectra definition: `(signal - reference) ./ reference` (i.e., differential reflectance / normalized contrast).
- Additional processing: take a derivative to enhance the signal.
- Dual-gate analysis: use the **minimum of the derivative** as the scalar signal vs sweep axis, or vs converted (density, electric field).
- Instruction: "use the code in the folder and understand the code" (code alongside the measurement folder).

Open questions to resolve for reproducibility:
- Which derivative: d/dw (wavelength/energy) or derivative vs gate? What order and sign conventions?
- Any smoothing / filtering parameters prior to derivative?
- Exact conversion formulas/parameters for dual-gate → (n, D) used in this dataset.
- Code entry point: which .m script is the canonical pipeline.
