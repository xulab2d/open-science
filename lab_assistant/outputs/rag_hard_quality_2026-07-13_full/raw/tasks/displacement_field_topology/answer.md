**Observation**

Displacement field acts as a layer-potential control knob. In angle-aligned `MoTe2/WSe2` at `nu=1`, increasing displacement field is reported to drive consecutive transitions: frustrated Mott insulator -> ferromagnetic QAH Mott insulator -> antiferromagnetic valley-coherent Mott state. The first transition is reported without an observed charge-gap closure. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.

For twisted TMD bilayers, the supplied context also states that an applied layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions. Evidence: `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`, `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`, `lab_assistant/knowledge/papers/semiconductor_moire_foundations.md`.

Available observables in the context include compressibility and RMCD for the `MoTe2/WSe2` transition report, via excluded-but-listed graph edges `edge:promoted_2602_tpts_measured_by_compressibility` and `edge:promoted_2602_tpts_measured_by_rmcd`. For twisted `MoTe2`, the context additionally mentions optical control/readout of spin-valley and Chern order through resonant circularly polarized excitation. Evidence: `claim:promoted_2508_optical_control_chern_order`, `edge:optical_spin_valley_switching_explains_2508_control_claim`.

**Inference**

Mechanistically, displacement field likely tunes topology by changing layer polarization and moire-band inversion/geometry, thereby modifying Chern character and correlated exchange terms. In `MoTe2/WSe2`, this appears as a sequence where the same `nu=1` Mott state changes magnetic/valley order and topology as the field is swept: frustrated/trivial or non-QAH-like -> ferromagnetic Chern/QAH -> AFM valley-coherent.

Observable distinctions, using only the supplied context plus direct implications of the phase labels:

- QAH regime: ferromagnetic order plus nontrivial Chern response; should show RMCD contrast and QAH transport signatures if transport is measured. Evidence for phase identity: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- AFM valley-coherent regime: valley coherence with antiferromagnetic order; expected to differ from QAH by suppressed/no net ferromagnetic RMCD while retaining an incompressible Mott gap. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`, RMCD/compressibility edges listed in context.
- Frustrated/trivial Mott regime: incompressible Mott behavior without QAH topology; context specifically notes the first transition can occur without observed charge-gap closure, so compressibility alone may not distinguish topology. Evidence: `claim:promoted_2602_mote2_wse2_consecutive_tpts`.
- Valley/spin-Chern order in twisted `MoTe2`: circularly polarized optical response or switching of spin-valley orientation can identify Chern-order reversal at zero field. Evidence: `claim:promoted_2508_optical_control_chern_order`.

**Uncertainty**

The supplied context is not sufficient to give numeric critical displacement fields, twist angles, Hall resistance values, coercive fields, RMCD amplitudes, or detailed phase diagrams. It also does not provide a complete observable matrix for QAH vs AFM vs valley-coherent vs trivial phases; the RMCD/compressibility links are present only as excluded graph-edge summaries, and transport observables are inferred from the QAH label rather than explicitly stated in the supplied context.