**Observation**

In angle-aligned MoTe2/WSe2 at `nu=1`, increasing displacement field is reported to drive consecutive topological phase transitions: geometrically frustrated Mott insulator → ferromagnetic QAH Mott insulator → antiferromagnetic valley-coherent Mott state (`claim:promoted_2602_mote2_wse2_consecutive_tpts`). The first transition is reported without an observed charge-gap closure (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

More generally, an applied layer potential difference can tune moiré band topology, Mott gaps, spin-orbit terms, and effective Dzyaloshinskii-Moriya interactions in twisted TMD bilayers (`claim:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interaction_in_twisted_bi`; `paper:band_topology_hubbard_model_heisenberg_model_and_dzyaloshinskii_moriya_interacti`; `lab_assistant/knowledge/papers/semiconductor_moire_foundations.md`).

The supplied graph also flags compressibility and RMCD as measurement channels for the MoTe2/WSe2 displacement-field transitions (`edge:promoted_2602_tpts_measured_by_compressibility`; `edge:promoted_2602_tpts_measured_by_rmcd`).

**Inference**

Displacement field tunes topology by changing the layer polarization/hybridization landscape of the moiré bands, which changes the effective band topology and exchange interactions. In correlated fillings, that shifts the balance among frustrated Mott physics, spin-valley-polarized Chern order, and inter-valley coherent antiferromagnetism.

Observable distinctions:

- QAH regime: ferromagnetic/topological order should be identified by anomalous Hall response at zero field, hysteretic magnetic contrast, and RMCD signal consistent with spin-valley polarization; in a fully developed QAH state one expects quantized Hall conductance, though the supplied context does not give a numeric value.
- AFM valley-coherent regime: should lack net ferromagnetic RMCD expected for QAH, but retain an insulating/compressibility signature and show evidence for valley coherence or antiferromagnetic order.
- Valley-coherent but non-QAH regime: distinguished from QAH by loss of net Chern/ferromagnetic Hall signature while retaining coherence-sensitive signatures; the context specifically supports RMCD/compressibility as relevant but does not specify a direct valley-coherence probe.
- Trivial/frustrated Mott regime: insulating in compressibility/charge response but without QAH Hall topology or the RMCD pattern of ferromagnetic Chern order; in the cited MoTe2/WSe2 sequence this is the low-displacement-field starting phase (`claim:promoted_2602_mote2_wse2_consecutive_tpts`).

**Uncertainty**

The supplied context does not provide raw transport traces, Hall quantization values, RMCD sign conventions, capacitance/compressibility line shapes, or detailed valley-coherence diagnostics. It also does not specify whether the same exact displacement-field sequence applies to all twisted MoTe2 systems versus the cited angle-aligned MoTe2/WSe2 case.