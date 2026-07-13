**Observation**

The supplied context contains only discovery-level pointers, not enough source content to treat any superconductivity claim as lab knowledge. The relevant low-confidence/promotion candidates appear only in the excluded list: `claim:promoted_2504_chiral_superconductivity_signatures`, `paper:arxiv_2504_06972v1`, and `paper:evidence_of_competing_ground_states_between_fractional_chern_insulator_and_antif`.

The stable neighboring lab context is about fractional Chern states and probes, not superconductivity: optical PL/RMCD signatures near fractional Chern fillings are medium-confidence (`claim:signatures_of_fractional_quantum_anomalous_hall_states_in_twisted_mote2_bilayer_trion_pl_and_rmc`), local probes of FCI bulk/edge structure are medium-confidence (`paper:local_probe_of_bulk_and_edge_states_in_a_fractional_chern_insulator`; `claim:local_probe_of_bulk_and_edge_states_in_a_fractional_chern_insulator_local_probes_can_resolve_bot`), and optical pumping as a control knob is medium-confidence (`claim:optical_control_of_integer_and_fractional_chern_insulators_optical_pumping_is_now_being_used_as`).

**Inference**

Worth promoting first: `paper:arxiv_2504_06972v1` / `claim:promoted_2504_chiral_superconductivity_signatures`, because the node names directly indicate superconductivity signatures near the relevant fractional Chern landscape. Second priority: `paper:evidence_of_competing_ground_states_between_fractional_chern_insulator_and_antif`, because competing ground states around FCI phases could affect whether a superconducting interpretation is real, adjacent, or a misassigned nearby phase.

Before promotion, read the original arXiv source for `paper:arxiv_2504_06972v1`, extract the actual reported observables, sample system, filling/displacement-field range, temperature/field dependence if present, and whether the paper claims superconductivity, chiral superconductivity, or only suggestive signatures. Then compare those claims against established FCI probe context from `lab_assistant/knowledge/papers/xu_group_recent_moire_states.md`, especially the optical and local-probe FCI claims cited above.

**Uncertainty**

I would not yet promote either lead into lab knowledge from this context alone. The context gives node IDs and provenance routes but not the arXiv abstract, figures, measurements, or author claims. Promotion requires source-reading of the arXiv paper itself plus any linked paper-shelf note; otherwise the correct status is “low-confidence discovery lead,” not “known superconductivity near fractional Chern states.”