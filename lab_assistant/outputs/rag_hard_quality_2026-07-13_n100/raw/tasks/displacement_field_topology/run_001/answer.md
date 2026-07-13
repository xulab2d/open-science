**Observation**

MoTe2/WSe2 at `nu=1` is reported to undergo two displacement-field-driven topological phase transitions: frustrated Mott insulator → ferromagnetic QAH Mott insulator → antiferromagnetic valley-coherent Mott state (`claim:promoted_2602_mote2_wse2_consecutive_tpts`). The same claim notes that the first transition occurs without an observed charge-gap closure, so topology/order changes can be field-tuned without a simple single-particle gap-closing signature.

For twisted TMD systems, an applied layer potential difference/displacement field can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions (`claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`; `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`). In twisted MoTe2, spin-valley/Chern order can also be switched optically at zero field, indicating that the relevant topological order parameter is tied to spin-valley polarization (`claim:promoted_2508_optical_control_chern_order`; `edge:optical_spin_valley_switching_explains_2508_control_claim`).

Supplied context identifies compressibility and RMCD as measurements associated with the MoTe2/WSe2 transition report (`edge:promoted_2602_tpts_measured_by_compressibility`; `edge:promoted_2602_tpts_measured_by_rmcd`, listed in context as excluded-by-budget nodes).

**Inference**

Displacement field likely tunes topology by changing the layer-resolved potential landscape, which reshapes moire-band topology and interaction-derived magnetic terms. In MoTe2/WSe2 this moves the system between competing correlated insulators: a frustrated/trivial-or-ambiguous Mott regime, a ferromagnetic QAH Mott regime, and an AFM valley-coherent regime (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`).

Observable separation from the supplied context is:

- QAH regime: ferromagnetic Chern order/QAH-Mott character; should be associated with spin-valley polarization and Chern order (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `claim:promoted_2508_optical_control_chern_order`).
- AFM valley-coherent regime: antiferromagnetic order plus valley coherence, distinct from ferromagnetic QAH order (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).
- Frustrated/trivial Mott regime: insulating/compressibility feature without the QAH or AFM valley-coherent order assignment; first transition reportedly lacks observed charge-gap closure (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).
- RMCD is the most directly indicated magnetic/valley-sensitive optical observable, while compressibility tracks insulating gaps/phase boundaries (`edge:promoted_2602_tpts_measured_by_rmCD`; `edge:promoted_2602_tpts_measured_by_compressibility`, as supplied context labels).

**Uncertainty**

The supplied context is insufficient to state specific numerical displacement fields, Hall resistance values, RMCD sign patterns, compressibility traces, or exact criteria for “trivial” versus “frustrated” beyond the phase labels. It also does not provide enough factual detail to fully distinguish QAH, AFM, valley-coherent, and trivial regimes by a complete experimental decision table; transport signatures such as quantized Hall response are not explicitly stated in the provided nodes.