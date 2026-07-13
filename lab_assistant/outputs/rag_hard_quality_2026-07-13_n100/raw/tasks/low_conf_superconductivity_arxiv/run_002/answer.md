**Observation**

The supplied context does not include the full low-confidence arXiv records. It only exposes relevant candidate IDs in the excluded list: `claim:promoted_2504_chiral_superconductivity_signatures`, `paper:arxiv_2504_06972v1`, and `paper:evidence_of_competing_ground_states_between_fractional_chern_insulator_and_antif...`.

The graph policy is explicit: low-confidence arXiv metadata or automatic extraction are “discovery leads, not settled facts,” and promotion requires reading the source and rewriting the claim with stronger provenance (`skill:fact-graph`). Existing better-grounded context concerns fractional Chern states and probes, not superconductivity: optical probes near `nu = -1, -2/3, -3/5` (`claim:signatures_of_fractional_quantum_anomalous_hall_states_in_twisted_mote2_bilayer_trion_pl_and_rmc`) and local bulk/edge FCI probes (`paper:local_probe_of_bulk_and_edge_states_in_a_fractional_chern_insulator`).

**Inference**

The only superconductivity-related lead visibly worth promotion is `claim:promoted_2504_chiral_superconductivity_signatures` / `paper:arxiv_2504_06972v1`, but only as a priority reading target, not as lab knowledge yet. Its apparent relevance is the node name: “chiral superconductivity signatures” near the 2504 arXiv lead.

The “competing ground states” paper should be treated as secondary unless source reading confirms it directly links superconductivity to fractional Chern physics. From the supplied title fragment alone, it is about competition involving an FCI and an antiferro-… state, not necessarily superconductivity.

**Uncertainty**

Before promotion, read the full arXiv source for `paper:arxiv_2504_06972v1` and any provenance behind `claim:promoted_2504_chiral_superconductivity_signatures`. Required checks: actual material system, filling range, proximity to fractional Chern states, superconductivity evidence, exclusion of insulating/domain/percolative alternatives, magnetic-field and temperature dependence, and whether “chiral” is directly measured or inferred.

Do not treat any of these as lab knowledge until the claim is rewritten with source-level citations and confidence upgraded from metadata-derived lead to provenance-backed claim, per `skill:fact-graph`.