**Observation**

In angle-aligned MoTe2/WSe2 at `nu=1`, increasing displacement field is reported to drive consecutive phase transitions: geometrically frustrated Mott insulator -> ferromagnetic QAH Mott insulator -> antiferromagnetic valley-coherent Mott state (`claim:promoted_2602_mote2_wse2_consecutive_tpts`). The first transition reportedly occurs without an observed charge-gap closure, so the topology/order change is not simply a single-particle gap-closing transition in the available summary (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

Theory context from twisted TMD homobilayers says an applied layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions (`claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`; `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`). In twisted MoTe2, Chern order is tied to spin-valley order and can be switched optically at zero field (`claim:promoted_2508_optical_control_chern_order`; `edge:optical_spin_valley_switching_explains_2508_control_claim`).

The supplied graph also points to compressibility and RMCD as measurements associated with the MoTe2/WSe2 transition report (`edge:promoted_2602_tpts_measured_by_compressibility`; `edge:promoted_2602_tpts_measured_by_rmcd`).

**Inference**

Displacement field tunes topology by changing layer polarization and moire-band character, which in turn changes the effective Chern band, interaction scale, spin-orbit anisotropy, and magnetic exchange terms. In MoTe2/WSe2 this moves the system through competing correlated insulating orders: a frustrated/topologically trivial or non-QAH Mott state, a ferromagnetic valley-polarized QAH Mott state, and then an AFM valley-coherent Mott state (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`).

Observable distinctions, from the supplied context plus direct inference from phase labels:

- QAH regime: ferromagnetic order plus Chern response; expect RMCD signal from spin/valley polarization and anomalous Hall/QAH transport as the defining topology marker (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `claim:promoted_2508_optical_control_chern_order`).
- AFM valley-coherent regime: insulating state with valley coherence but no net ferromagnetic RMCD-like moment expected; distinguish from QAH by loss of net ferromagnetic/Chern response while retaining a charge gap in compressibility (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `edge:promoted_2602_tpts_measured_by_compressibility`; `edge:promoted_2602_tpts_measured_by_rmcd`).
- Valley-coherent order: inferred from the reported “antiferromagnetic valley-coherent Mott state”; experimentally it should be separated from simple valley polarization by probes sensitive to coherence/order rather than only net RMCD (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).
- Trivial/frustrated Mott regime: insulating compressibility gap without QAH/Chern response and without the ferromagnetic QAH signature; the context names it geometrically frustrated rather than giving a full observable fingerprint (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

**Uncertainty**

The supplied context does not provide numeric displacement-field values, Hall conductance values, RMCD line shapes, compressibility traces, or direct criteria for “trivial” versus “frustrated” regimes. It also does not give a full experimental observable set for valley coherence beyond the phase assignment, so any detailed prescription such as specific optical selection rules, nonlocal transport, or domain behavior would require source text not included here.