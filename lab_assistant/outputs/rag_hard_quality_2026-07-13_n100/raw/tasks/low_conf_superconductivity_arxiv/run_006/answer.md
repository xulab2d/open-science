**Observation**

The supplied context contains only partial records for the superconductivity-related arXiv leads. The relevant low-confidence/discovery items appear only in the excluded list, not as readable graph nodes:

- `claim:promoted_2504_chiral_superconductivity_signatures`
- `paper:evidence_of_competing_ground_states_between_fractional_chern_insulator_and_antif`
- `paper:arxiv_2504_06972v1`

The usable surrounding context establishes that fractional Chern states in twisted MoTe2 are already connected to optical probes and local probes, but not to superconductivity as settled lab knowledge: PL/RMCD signatures near `nu = -1, -2/3, -3/5` are medium-confidence (`claim:signatures_of_fractional_quantum_anomalous_hall_states_in_twisted_mote2_bilayer_trion_pl_and_rmc`), and local probes can resolve bulk/edge FCI structure (`claim:local_probe_of_bulk_and_edge_states_in_a_fractional_chern_insulator_local_probes_can_resolve_bot`).

**Inference**

The only leads worth promotion consideration are the superconductivity-adjacent arXiv records named above, especially the “chiral superconductivity signatures” claim and the “competing ground states between fractional Chern insulator and antif…” paper record. They are worth triage because they sit near an existing lab frontier: fractional Chern states, competing orders, and local/optical observables.

They should not be promoted as lab knowledge from this context alone. At most, promote them from “low-confidence arXiv lead” to “reading queue / candidate claim” after source review.

Required source-reading before promotion:

1. Read the actual arXiv paper for `paper:arxiv_2504_06972v1` and identify the claimed superconducting observable, sample platform, filling, field/displacement conditions, and whether the evidence is transport, spectroscopy, optical, or theory.
2. Read the source behind `claim:promoted_2504_chiral_superconductivity_signatures`; verify whether “chiral superconductivity” is directly measured, inferred, or speculative.
3. Read the source behind `paper:evidence_of_competing_ground_states_between_fractional_chern_insulator_and_antif`; determine what “competing ground states” are, whether superconductivity is actually one of them, and how close the regime is to fractional Chern states.
4. Cross-check against existing medium-confidence FCI knowledge in `lab_assistant/knowledge/papers/xu_group_recent_moire_states.md` and the cited FCI optical/local probe claims before integrating into synthesis.

**Uncertainty**

The supplied context is insufficient to say which lead should be promoted definitively, because the actual low-confidence node contents and arXiv source text are not included. No numeric claims, paper conclusions, or mechanism-level superconductivity statements should be treated as lab knowledge yet. The correct action is cautious source-reading and claim rewriting with explicit provenance, not immediate promotion.