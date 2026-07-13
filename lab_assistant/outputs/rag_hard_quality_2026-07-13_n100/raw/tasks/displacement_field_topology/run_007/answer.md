**Observation**

MoTe2/WSe2 at `nu=1` is reported to undergo two displacement-field-driven topological phase transitions: frustrated Mott insulator -> ferromagnetic QAH Mott insulator -> antiferromagnetic valley-coherent Mott state as displacement field increases (`claim:promoted_2602_mote2_wse2_consecutive_tpts`). The same claim says the first transition occurs without an observed charge-gap closure.

For related twisted TMD systems, an applied layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions (`claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`; `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`, provenance `lab_assistant/knowledge/papers/semiconductor_moire_foundations.md`).

The supplied graph context explicitly lists compressibility and RMCD as measurements connected to the MoTe2/WSe2 topological-transition claim, but the detailed node text is excluded from the context budget.

**Inference**

Displacement field appears to tune topology by changing layer-polarized moire band structure and interaction parameters: it can alter band topology and Mott-gap energetics, while also changing spin-orbit/DM terms that select magnetic or valley order. In MoTe2/WSe2 this produces a sequence where topology and spin/valley order are reorganized without necessarily closing the charge gap at the first transition (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`).

Observable separation, using only supplied context plus direct implications of phase names:

- QAH regime: ferromagnetic topological Mott state; should be identified by anomalous Hall/Chern response together with magnetic contrast, but the supplied context does not give explicit Hall data.
- AFM valley-coherent regime: antiferromagnetic and valley-coherent order; RMCD/compressibility are indicated as relevant probes, but the supplied context does not state the detailed RMCD signature.
- Frustrated/trivial Mott regime: insulating/compressibility gap without QAH topology or valley-coherent AFM assignment.
- Transition boundaries: compressibility tracks charge-gap behavior; RMCD tracks magnetic/valley polarization changes. The first MoTe2/WSe2 transition is notable because no charge-gap closure was observed (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

**Uncertainty**

The context is insufficient to state the exact experimental observables that distinguish QAH, AFM, valley-coherent, and trivial regimes, such as Hall resistance values, hysteresis, RMCD sign patterns, optical selection rules, or compressibility line shapes. It only supports the phase sequence, the role of displacement/layer potential in tuning topology and interactions, and that compressibility/RMCD are relevant probes.