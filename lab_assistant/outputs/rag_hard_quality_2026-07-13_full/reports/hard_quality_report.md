# Hard RAG Quality Benchmark

Generated: 2026-07-13T05:12:54

## What This Measures
- Retrieval ranking: recall@10, precision@10, MRR, nDCG@10, and hard-negative leakage.
- Context quality: whether packed context contains the needed evidence and ranks relevant chunks early.
- Answer quality: required scientific concepts, abstention/caution behavior, citation usage, and a lightweight atomic-support proxy.
- Judge quality: Codex-as-judge scores for context relevance, answer relevance, faithfulness, citation quality, scientific correctness, uncertainty calibration, and actionability.

## Literature Mapping
- [RAGAS](https://arxiv.org/abs/2309.15217): separate retrieval/context quality from generation faithfulness and answer relevance.
- [BEIR](https://arxiv.org/abs/2104.08663): ranked retrieval metrics and hard out-of-domain/alias pressure, with lexical baseline awareness.
- [KILT](https://arxiv.org/abs/2009.02252): downstream answer quality plus provenance, not retrieval alone.
- [ALCE](https://arxiv.org/abs/2305.14627): citation quality and automatic citation support checks.
- [AIS](https://arxiv.org/abs/2112.12870): whether generated statements are attributable to identified sources.
- [FActScore](https://aclanthology.org/2023.emnlp-main.741/): atomic factuality framing: score supported factual claims, not just whole answers.
- [ARES](https://arxiv.org/abs/2311.09476): LLM-judge dimensions: context relevance, answer faithfulness, answer relevance.

## Executive Summary
- Hard tasks run: 10
- Overall mean score: 0.751
- Retrieval score: 0.765
- Context score: 0.558
- Deterministic answer score: 0.848
- LLM judge score: 0.834
- Answer latency p50/p95: 16.0s / 22.9s
- Judge latency p50/p95: 10.1s / 23.0s

## Layer Scores
- `overall_score`: 0.751
- `retrieval_score`: 0.765
- `context_score`: 0.558
- `answer_deterministic_score`: 0.848
- `judge_score`: 0.834

## Judge Metric Means
- `context_relevance`: 4.00/5
- `answer_relevance`: 4.70/5
- `faithfulness`: 4.10/5
- `citation_quality`: 3.50/5
- `scientific_correctness`: 4.20/5
- `uncertainty_calibration`: 4.70/5
- `actionability`: 4.00/5

## Scores By Family
- `abstention` (1 tasks): overall 0.403, retrieval 0.200, context 0.000, answer 0.556, judge 0.857
- `freshness` (1 tasks): overall 0.771, retrieval 1.000, context 0.550, answer 0.706, judge 0.829
- `hard_negative` (1 tasks): overall 0.513, retrieval 0.189, context 0.372, answer 0.833, judge 0.657
- `multi_hop` (3 tasks): overall 0.878, retrieval 0.953, context 0.856, answer 0.933, judge 0.771
- `project_context` (2 tasks): overall 0.732, retrieval 0.818, context 0.365, answer 0.833, judge 0.914
- `uncertainty` (2 tasks): overall 0.863, retrieval 0.882, context 0.681, answer 0.960, judge 0.929

## Failure Taxonomy
- `answer_concept_miss`: 1/10 tasks
- `context_miss`: 6/10 tasks
- `hard_negative_leak`: 1/10 tasks
- `judge_citation_under_4`: 6/10 tasks
- `judge_critical_errors`: 2/10 tasks
- `judge_faithfulness_under_4`: 2/10 tasks
- `retrieval_miss`: 3/10 tasks
- `weak_citation_precision_proxy`: 4/10 tasks

## Per-Task Findings
### d93_nu_minus2_hysteresis_caution
- Overall: 0.840; retrieval 0.824; context 0.593; answer 0.944; judge 1.000
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 1.000/0.186
- Answer concept coverage: 0.667; behavior ok: True; citation precision proxy: 1.000
- Judge: faithfulness 5/5, citation 5/5, uncertainty 5/5. The answer correctly gives a cautious negative conclusion for D93, explicitly states there is not enough local evidence for robust hysteretic nu=-2 magnetism, and grounds the reasoning in the supplied D93 claim, open question, and follow-up edge. It avoids forbidden overclaims and appropriately notes missing raw loops, repeatability, and quantitative criteria.
- Answer: `raw/tasks/d93_nu_minus2_hysteresis_caution/answer.md`

### moire_exciton_exclude_polariton
- Overall: 0.513; retrieval 0.189; context 0.372; answer 0.833; judge 0.657
- Retrieval missed groups: [0]; hard negatives: [{'id': 'paper:nano_optical_imaging_of_the_tailored_exciton_polariton_transport_in_mose2_wavegu', 'label': 'Nano-optical imaging of the tailored exciton-polariton transport in MoSe2 waveguides', 'rank': 1, 'term': 'polariton'}, {'id': 'paper:nano_optical_imaging_of_the_tailored_exciton_polariton_transport_in_mose2_wavegu', 'label': 'Nano-optical imaging of the tailored exciton-polariton transport in MoSe2 waveguides', 'rank': 1, 'term': 'waveguide'}, {'id': 'paper:separation_of_the_valley_exciton_polariton_in_two_dimensional_semiconductors_wit', 'label': 'Separation of the valley exciton-polariton in two-dimensional semiconductors with an anisotropic photonic crystal', 'rank': 2, 'term': 'polariton'}, {'id': 'paper:metasurface_integrated_monolayer_exciton_polariton', 'label': 'Metasurface Integrated Monolayer Exciton Polariton', 'rank': 3, 'term': 'polariton'}]
- Context recall/precision: 0.500/0.244
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 1.000
- Judge: faithfulness 3/5, citation 3/5, uncertainty 3/5. The answer mostly addresses the request and correctly applies the exclusion logic, but it violates the forbidden-term constraint and relies on at least one key reference not supported by the supplied visible context. The arXiv PL/RMCD twisted MoTe2 reference is supported, and the caveat about incomplete context helps, but the unsupported 'strongest local hit' claim and verbatim distractor title reduce faithfulness and citation quality.
- Critical errors: ['The answer includes a forbidden distractor title verbatim: "Nano-optical imaging of the tailored exciton-polariton transport...".', 'It asserts `paper:signatures_of_fractional_charges_via_anyon_trions_in_twisted_mote2` and its local paths as a key reference, but that paper/path evidence is not present in the supplied visible context.']
- Answer: `raw/tasks/moire_exciton_exclude_polariton/answer.md`

### a5_dot_project_context
- Overall: 0.655; retrieval 0.815; context 0.000; answer 0.833; judge 0.971
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 0.000/0.000
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 1.000
- Judge: faithfulness 5/5, citation 4/5, uncertainty 5/5. The answer correctly identifies the A5 AAtA dot project, explicitly ties PL dispersion and peak-tracking interpretation to loading project-local context first, and names both context/projects and knowledge/projects plus the NAS project root. It appropriately caveats that the supplied context does not include the specific A5 note contents or analysis files. Citations are file-level rather than highly specific, but they are attached to the right claims.
- Answer: `raw/tasks/a5_dot_project_context/answer.md`

### b79_project_context
- Overall: 0.810; retrieval 0.820; context 0.729; answer 0.833; judge 0.857
- Retrieval missed groups: [0]; hard negatives: []
- Context recall/precision: 0.500/0.958
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 1.000
- Judge: faithfulness 4/5, citation 4/5, uncertainty 5/5. The answer correctly routes B79 RMCD/PL questions to project-specific local context under context/projects and knowledge/projects before generic optical-keyword handling, and it names RMCD and PL-related observables. It appropriately caveats that the supplied context does not expose a B79-specific project summary or data. Minor issues: some listed observables, such as RMCD sign/field dependence and spatial/domain contrast, are plausible but not directly supported by the supplied context, so the answer slightly extends beyond the evidence.
- Answer: `raw/tasks/b79_project_context/answer.md`

### fci_evidence_hierarchy
- Overall: 0.896; retrieval 1.000; context 0.944; answer 0.840; judge 0.800
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 1.000/0.887
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 0.375
- Judge: faithfulness 4/5, citation 3/5, uncertainty 5/5. The answer addresses the requested evidence hierarchy and explains what each probe can rule out, with good caveats that no single probe proves an FCI. It is mostly faithful to the supplied context, especially on compressibility/magneto-optics and local probes. Weaknesses are incomplete separation of compressibility versus thermodynamics, some under-specified citations, and a few claims relying on context items not fully visible in the provided pack.
- Answer: `raw/tasks/fci_evidence_hierarchy/answer.md`

### optical_control_chern_states
- Overall: 0.901; retrieval 0.920; context 0.940; answer 1.000; judge 0.743
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 1.000/0.880
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 1.000
- Judge: faithfulness 3/5, citation 3/5, uncertainty 4/5. The answer directly addresses the question and clearly separates passive PL/RMCD probe logic from active optical pumping/control of integer and fractional Chern states. It includes the required concepts and calibrates uncertainty reasonably. Main weakness is unsupported expansion beyond the supplied context via uncited/unprovided graph claims about magneto-optics, switching, bistability, and domain-wall writing.
- Critical errors: ['Cites and relies on claims not present in the supplied context: `claim:thermodynamic_evidence_of_fractional_chern_insulator_in_moire_mote2_local_compressibility_plus_m` and `claim:promoted_2508_optical_switching_domain_walls`.', 'States specific active-control outcomes such as zero-field optical switching, magnetic bistate cycling, and domain-wall writing without support in the visible supplied context.']
- Answer: `raw/tasks/optical_control_chern_states/answer.md`

### minus_one_third_interpretation
- Overall: 0.886; retrieval 0.940; context 0.769; answer 0.976; judge 0.857
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 0.667/0.872
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 0.857
- Judge: faithfulness 4/5, citation 3/5, uncertainty 5/5. Strong cautious answer that directly addresses nu=-1/3 optical FQAH interpretation, includes PL/RMCD, artifacts, trivial magnetic order, exciton/trion effects, disorder/domains, and concrete separating evidence. Main weaknesses are missing explicit CDW/inhomogeneity wording and reliance on a few citations not available in the supplied context.
- Answer: `raw/tasks/minus_one_third_interpretation/answer.md`

### displacement_field_topology
- Overall: 0.839; retrieval 0.940; context 0.684; answer 0.958; judge 0.771
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 1.000/0.369
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 0.750
- Judge: faithfulness 4/5, citation 3/5, uncertainty 5/5. The answer is mostly relevant and careful, with good caveats and reasonably specific provenance IDs. It correctly identifies displacement field as a layer-potential knob and describes the MoTe2/WSe2 sequence into QAH and AFM valley-coherent regimes. Main weaknesses are missing PL, generic transport discussion, incomplete phase-by-observable distinctions, and a few inferred mechanisms/observable expectations that are plausible but not directly supported by the supplied context.
- Answer: `raw/tasks/displacement_field_topology/answer.md`

### low_conf_superconductivity_arxiv
- Overall: 0.771; retrieval 1.000; context 0.550; answer 0.706; judge 0.829
- Retrieval missed groups: []; hard negatives: []
- Context recall/precision: 0.667/0.433
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 0.571
- Judge: faithfulness 4/5, citation 3/5, uncertainty 5/5. The answer follows the required cautious posture: it identifies the relevant records as low-confidence arXiv/source-reading leads, refuses to promote them as lab knowledge from the supplied context alone, and specifies what must be read before promotion. It is mostly faithful, though it references several nodes that are not visible in the supplied context excerpt beyond the answer's own claim that they were excluded by budget, so citation specificity is only moderate. It gives useful promotion discipline and avoids forbidden terms.
- Answer: `raw/tasks/low_conf_superconductivity_arxiv/answer.md`

### b79_exact_curie_temperature_abstain
- Overall: 0.403; retrieval 0.200; context 0.000; answer 0.556; judge 0.857
- Retrieval missed groups: [0]; hard negatives: []
- Context recall/precision: 0.000/0.000
- Answer concept coverage: 1.000; behavior ok: True; citation precision proxy: 0.000
- Judge: faithfulness 5/5, citation 4/5, uncertainty 5/5. The answer correctly abstains from inventing an exact value for B79, states that the supplied context lacks a local project note with that information, and avoids numeric temperature claims or forbidden unit terms. Citations are file-specific but not line-specific. The main limitation is that it gives only a minimal next action rather than a concrete follow-up search target.
- Answer: `raw/tasks/b79_exact_curie_temperature_abstain/answer.md`

## Presentation Plots
- `plots/overall_quality_by_task.png`
- `plots/pipeline_layer_scores.png`
- `plots/judge_metric_heatmap.png`
- `plots/failure_taxonomy.png`
- `plots/context_recall_vs_faithfulness.png`
- `plots/answer_judge_latency.png`
