**Observation**

The supplied context contains only discovery-level references to the superconductivity lead: `claim:promoted_2504_chiral_superconductivity_signatures`, `paper:evidence_of_competing_ground_states_between_fractional_chern_insulator_and_antif`, and `paper:arxiv_2504_06972v1`, all listed under “Excluded” because of budget. No abstract, claims, data, methods, or source text are provided for these nodes.

The stronger in-context baseline is about fractional Chern states and probes, not superconductivity: optical PL/RMCD signatures near `nu = -1, -2/3, -3/5` are medium-confidence for twisted MoTe2 (`claim:signatures_of_fractional_quantum_anomalous_hall_states_in_twisted_mote2_bilayer_trion_pl_and_rmc`), and local probes can resolve bulk/edge structure in a fractional Chern insulator (`paper:local_probe_of_bulk_and_edge_states_in_a_fractional_chern_insulator`; `claim:local_probe_of_bulk_and_edge_states_in_a_fractional_chern_insulator_local_probes_can_resolve_bot`).

**Inference**

The only superconductivity-near-fractional-Chern lead worth promotion from this context is the `2504` arXiv cluster, especially `paper:arxiv_2504_06972v1` / `claim:promoted_2504_chiral_superconductivity_signatures`, because it is the only supplied lead explicitly pointing to chiral superconductivity signatures near competing fractional-Chern/antiferromagnetic ground states.

Promotion should be limited to “priority for source reading,” not “lab knowledge.” Before promotion, read the actual arXiv paper/source for: sample system and filling range, whether superconductivity is directly measured or inferred, transport signatures used, exclusion of trivial metallic/percolative explanations, relation to fractional Chern states versus adjacent competing phases, and whether “chiral” is evidenced or only proposed.

**Uncertainty**

The context is insufficient to state that superconductivity was observed, that it is near a specific fractional Chern filling, or that the claim is reliable. The relevant nodes are explicitly low-context/excluded, so treating them as settled lab knowledge would violate the graph policy: low-confidence arXiv/metadata records are discovery leads until the source is read and rewritten with stronger provenance (`skill:fact-graph`).