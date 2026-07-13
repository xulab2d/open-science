**Observation**

At `nu=1` in angle-aligned `MoTe2/WSe2`, increasing displacement field is reported to drive two topological phase transitions: frustrated Mott insulator → ferromagnetic QAH Mott insulator → antiferromagnetic valley-coherent Mott state (`claim:promoted_2602_mote2_wse2_consecutive_tpts`). The same claim says the first transition occurs without an observed charge-gap closure (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

The supplied graph also supports the broader mechanism that an applied layer potential difference can tune band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions in twisted TMD bilayers, specifically twisted bilayer WSe2 (`claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`; `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`). For twisted MoTe2, the supplied context additionally notes field-driven Chern behavior in the second moiré band, with unusual magnetotransport around `2.2-2.7` holes per moiré cell (`paper:interplay_between_topology_and_correlations_in_the_second_moire_band_of_twisted`).

Observable evidence explicitly present in the context includes compressibility and RMCD as probes of the `MoTe2/WSe2` displacement-field transitions, from excluded but listed graph edges: `edge:promoted_2602_tpts_measured_by_compressibility`, `edge:promoted_2602_tpts_measured_by_rmCD` / `edge:promoted_2602_tpts_measured_by_rmcd`.

**Inference**

The displacement field likely tunes topology by changing the layer polarization and effective moiré-band parameters: band topology, interaction-driven Mott gap, spin-orbit coupling, and anisotropic magnetic exchange/DM terms. In `MoTe2/WSe2`, this moves the system among competing insulating orders rather than simply closing and reopening a single-particle gap (`claim:promoted_2602_mote2_wse2_consecutive_tpts`; `claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`).

A practical observable map, constrained by the supplied context, is:

- QAH regime: ferromagnetic order plus nontrivial Chern topology; expect RMCD signal consistent with spin/valley polarization and transport signatures of Chern order. The QAH label itself is in `claim:promoted_2602_mote2_wse2_consecutive_tpts`, but quantized Hall data are not explicitly supplied here.
- AFM valley-coherent regime: reduced or compensated net RMCD compared with ferromagnetic QAH, while remaining insulating in compressibility; identified in the context as an “antiferromagnetic valley-coherent Mott state” (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).
- Valley-coherent order: should be distinguished from ordinary spin/valley-polarized ferromagnetism by RMCD/compressibility trends across the second transition, but the specific phase-sensitive observable is not given in the supplied context.
- Trivial/frustrated Mott regime: insulating compressibility without QAH Chern response; context labels the low-field state as a geometrically frustrated Mott insulator (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

**Uncertainty**

The context is sufficient for the qualitative phase sequence and mechanism, but insufficient for a complete experimental discriminator table. It does not provide numeric displacement fields, Hall resistance values, Chern numbers, RMCD signs, compressibility traces, or a direct phase-sensitive valley-coherence measurement. Therefore, any sharper distinction among QAH, AFM, valley-coherent, and trivial regimes would require the underlying paper/source beyond the supplied context.