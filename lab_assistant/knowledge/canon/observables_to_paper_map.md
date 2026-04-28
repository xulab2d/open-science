# Observables And Literature Anchors

Purpose:
- Secondary reference note for matching a lab-style observation to a small cluster of useful papers.
- Use after `syntheses/` when a request needs a tighter literature anchor.

## Chunk 1: Trion PL and exciton sensing

If the observation is:
- trion energy shifts at specific fillings
- PL intensity suppression at correlated states
- optical sensitivity to fractional fillings

Pull first:
- Cai et al., Nature 2023
  - link: https://www.nature.com/articles/s41586-023-06289-w
  - why: establishes trion PL plus RMCD as a sensor of `nu = -1, -2/3, -3/5` topological states in twisted MoTe2
- Li et al., Nature 2026
  - link: https://www.nature.com/articles/s41586-026-10101-w
  - why: uses new anyon-trion peaks to access fractional charge directly inside FCI states
- Wang et al., Nature 2025
  - link: https://www.nature.com/articles/s41586-025-08954-8
  - why: shows pump-probe optical spectroscopy can expose hidden states that static PL and transport miss

Use when:
- deciding whether an optical anomaly is just a correlated gap marker or could contain information about topology or fractional charge

## Chunk 2: RMCD, MOKE, and magnetic signatures

If the observation is:
- hysteresis at integer or fractional fillings
- field-induced onset of a state
- magneto-optical signal that may reflect ferromagnetism or competing order

Pull first:
- Cai et al., Nature 2023
  - why: connects RMCD ferromagnetism with Streda-dispersing topological states
- Zeng et al., Nature 2023
  - link: https://www.nature.com/articles/s41586-023-06452-3
  - why: combines magneto-optics with compressibility for bulk evidence of integer and fractional Chern insulators
- Redekop et al., Nature 2024
  - link: https://www.nature.com/articles/s41586-024-08153-x
  - why: magnetic imaging gives a direct view of orbital magnetization and disorder in FCI states
- "Evidence of competing ground states between fractional Chern insulator and antiferromagnetism in moire MoTe2" (Nature Communications 2026)
  - link: https://www.nature.com/articles/s41467-026-71479-9
  - why: use when a weak or absent zero-field signal may indicate antiferromagnetism or near-degenerate competing phases rather than a failed device

Use when:
- the main issue is whether magnetism is present, what kind of magnetism it is, and whether it tracks topology

## Chunk 3: Displacement-field sensitivity and topological switching

If the observation is:
- strong dependence on displacement field
- abrupt sign change or disappearance of a state with electric field
- apparent switching between magnetic/topological regimes

Pull first:
- Cai et al., Nature 2023
  - why: explicitly shows electric-field-driven transitions from topological to trivial states
- Zeng et al., Nature 2023
  - why: gives thermodynamic support for electric-field-tuned topological transitions
- Xu et al., Nature Physics 2025
  - link: https://www.nature.com/articles/s41567-025-02803-1
  - why: second-band transport shows electric-field-tuned quantum phase transitions
- Fan, Xiao, Yao, Nature Communications 2024
  - link: https://www.nature.com/articles/s41467-024-52314-5
  - why: useful for magnetoelectric interpretation and contact-free signatures of topological transitions

Use when:
- a gate map is telling you more about phase competition than about a single fixed state

## Chunk 4: Higher-band anomalies

If the observation is:
- robust features away from the first moiré band
- ferromagnetism above the canonical `nu = -1` regime
- unusual negative magnetoresistance or `1/T`-type transport scaling

Pull first:
- Xu et al., Nature Physics 2025
  - why: first systematic second-band transport map with magnetic and topological signatures
- An et al., Nature Communications 2025
  - link: https://www.nature.com/articles/s41467-025-59691-5
  - why: independent evidence for second-band ferromagnetism and displacement-field suppression
- Kang et al., Nature 2024
  - link: https://www.nature.com/articles/s41586-024-07214-5
  - why: use when the higher-band conversation turns toward quantum spin Hall or fractional-QSH physics

Use when:
- it would be a mistake to force everything into first-band FQAH language

## Chunk 5: Microscopic and structural interpretation

If the observation is:
- spatial inhomogeneity across a device
- local probe questions
- suspicion that structural disorder, moiré-area variation, or local layer polarization is driving the behavior

Pull first:
- Redekop et al., Nature 2024
  - why: directly quantifies disorder sources in twisted MoTe2 FCIs
- Thompson et al., Nature Physics 2025
  - link: https://www.nature.com/articles/s41567-025-02877-x
  - why: local STM/STS view of topological wavefunction texture and layer polarization
- Li et al., Nature Materials 2019
  - link: https://www.nature.com/articles/s41563-019-0506-1
  - why: for the older but still useful principle that stacking/structure can control magnetic ground state

Use when:
- the right interpretation depends on local structure rather than only on nominal filling

## Chunk 6: Retrieval rule

Default order:
1. start with a synthesis note when one exists
2. pull the smallest paper set that matches the observable class
3. prefer papers that use the same measurement modality as the current request
4. add one orthogonal paper only when it sharpens interpretation
