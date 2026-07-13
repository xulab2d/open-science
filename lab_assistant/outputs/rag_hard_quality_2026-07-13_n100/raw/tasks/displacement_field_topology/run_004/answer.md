**Observation**

In angle-aligned `MoTe2/WSe2` at `nu=1`, increasing displacement field is reported to drive consecutive phases: geometrically frustrated Mott insulator -> ferromagnetic QAH Mott insulator -> antiferromagnetic valley-coherent Mott state. The first transition occurs without an observed charge-gap closure. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`; excluded graph edges note compressibility and RMCD as measured observables.

More generally, an applied layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions in twisted TMD moire systems. Evidence: `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`, `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`, `lab_assistant/knowledge/papers/semiconductor_moire_foundations.md`.

For twisted `MoTe2`, the supplied context supports correlated Chern behavior and magnetotransport in higher bands, plus optical switching of spin-valley/Chern order, but does not give a direct displacement-field phase diagram. Evidence: `paper:interplay_between_topology_and_correlations_in_the_second_moire_band_of_twisted`, `claim:promoted_2508_optical_control_chern_order`.

**Inference**

Displacement field tunes topology by changing the layer-polarized moire band structure: it can alter band topology and correlated exchange terms, which then changes the preferred spin/valley order. In `MoTe2/WSe2`, that tuning appears to move the system between a topologically trivial or frustrated Mott regime, a ferromagnetic Chern/QAH Mott regime, and an antiferromagnetic valley-coherent Mott regime.

Observable distinctions, based on the supplied evidence:

- QAH / ferromagnetic Chern regime: anomalous Hall/Chern transport is the key topology diagnostic; RMCD should track net spin-valley polarization. Evidence/inference from `claim:promoted_2602_mote2_wse2_consecutive_tpts`, `paper:interplay_between_topology_and_correlations_in_the_second_moire_band_of_twisted`.
- AFM valley-coherent regime: compressibility can show it remains insulating; RMCD should differ from the ferromagnetic QAH state because AFM order has reduced or canceled net magnetization. Valley coherence itself would require a phase-sensitive or optical valley probe, but the specific probe is not supplied.
- Frustrated/trivial Mott regime: insulating compressibility without QAH/Chern transport; RMCD may show weak, absent, or non-ferromagnetic magnetic response. This is an inference from the phase labels in `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- Charge-gap behavior: compressibility distinguishes whether transitions involve charge-gap closure; the first reported transition does not show one. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.

**Uncertainty**

The context is insufficient to give numeric displacement-field ranges, exact Hall values, RMCD line shapes, or definitive valley-coherence observables. It also does not provide a direct displacement-field tuning mechanism specifically for twisted `MoTe2`; the strongest displacement-field evidence here is for `MoTe2/WSe2` and twisted `WSe2`-type theory.