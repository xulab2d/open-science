# Hard RAG Quality Benchmark

Generated: 2026-07-13T07:23:25

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
- Hard benchmark runs: 100 total across 10 unique tasks.
- Overall mean score: 0.756 +/- 0.031 95% CI.
- Retrieval score: 0.765
- Context score: 0.558
- Deterministic answer score: 0.879
- LLM judge score: 0.820
- Answer latency p50/p95: 15.6s / 29.3s
- Judge latency p50/p95: 11.4s / 18.1s

## Layer Scores
- `overall_score`: 0.756
- `retrieval_score`: 0.765
- `context_score`: 0.558
- `answer_deterministic_score`: 0.879
- `judge_score`: 0.820

## Judge Metric Means
- `context_relevance`: 3.82/5
- `answer_relevance`: 4.64/5
- `faithfulness`: 3.93/5
- `citation_quality`: 3.45/5
- `scientific_correctness`: 4.22/5
- `uncertainty_calibration`: 4.67/5
- `actionability`: 3.98/5

## Scores By Family
- `abstention` (10 runs, 1 tasks): overall 0.463, retrieval 0.200, context 0.000, answer 0.764, judge 0.889
- `freshness` (10 runs, 1 tasks): overall 0.759, retrieval 1.000, context 0.550, answer 0.817, judge 0.669
- `hard_negative` (10 runs, 1 tasks): overall 0.509, retrieval 0.189, context 0.372, answer 0.812, judge 0.663
- `multi_hop` (30 runs, 3 tasks): overall 0.888, retrieval 0.953, context 0.856, answer 0.962, judge 0.781
- `project_context` (20 runs, 2 tasks): overall 0.730, retrieval 0.818, context 0.365, answer 0.799, judge 0.939
- `uncertainty` (20 runs, 2 tasks): overall 0.850, retrieval 0.882, context 0.681, answer 0.956, judge 0.881

## Failure Taxonomy
- `answer_concept_miss`: 17/100 runs (17.0%)
- `context_miss`: 60/100 runs (60.0%)
- `hard_negative_leak`: 10/100 runs (10.0%)
- `judge_citation_under_4`: 55/100 runs (55.0%)
- `judge_critical_errors`: 25/100 runs (25.0%)
- `judge_faithfulness_under_4`: 36/100 runs (36.0%)
- `retrieval_miss`: 30/100 runs (30.0%)
- `weak_citation_precision_proxy`: 25/100 runs (25.0%)

## Per-Task Aggregate Findings
### a5_dot_project_context
- Overall: 0.641 +/- 0.006 95% CI (min 0.619, max 0.655, n=10).
- Layers: retrieval 0.815, context 0.000, answer 0.776, judge 0.971.
- Failure rates: answer_concept_miss 80%, context_miss 100%.
- Judge means: faithfulness 5.00/5, citation 4.00/5, uncertainty 5.00/5.
- Worst run: `a5_dot_project_context__run_009` score 0.619; answer `raw/tasks/a5_dot_project_context/run_009/answer.md`.
- Best run: `a5_dot_project_context__run_000` score 0.655; answer `raw/tasks/a5_dot_project_context/run_000/answer.md`.

### b79_exact_curie_temperature_abstain
- Overall: 0.463 +/- 0.022 95% CI (min 0.410, max 0.501, n=10).
- Layers: retrieval 0.200, context 0.000, answer 0.764, judge 0.889.
- Failure rates: context_miss 100%, retrieval_miss 100%, weak_citation_precision_proxy 30%.
- Judge means: faithfulness 5.00/5, citation 4.00/5, uncertainty 5.00/5.
- Worst run: `b79_exact_curie_temperature_abstain__run_005` score 0.410; answer `raw/tasks/b79_exact_curie_temperature_abstain/run_005/answer.md`.
- Best run: `b79_exact_curie_temperature_abstain__run_003` score 0.501; answer `raw/tasks/b79_exact_curie_temperature_abstain/run_003/answer.md`.

### b79_project_context
- Overall: 0.819 +/- 0.005 95% CI (min 0.803, max 0.831, n=10).
- Layers: retrieval 0.820, context 0.729, answer 0.822, judge 0.906.
- Failure rates: context_miss 100%, judge_citation_under_4 10%, retrieval_miss 100%.
- Judge means: faithfulness 4.90/5, citation 3.90/5, uncertainty 5.00/5.
- Worst run: `b79_project_context__run_009` score 0.803; answer `raw/tasks/b79_project_context/run_009/answer.md`.
- Best run: `b79_project_context__run_003` score 0.831; answer `raw/tasks/b79_project_context/run_003/answer.md`.

### d93_nu_minus2_hysteresis_caution
- Overall: 0.839 +/- 0.005 95% CI (min 0.826, max 0.854, n=10).
- Layers: retrieval 0.824, context 0.593, answer 0.949, judge 0.989.
- Failure rates: answer_concept_miss 80%.
- Judge means: faithfulness 5.00/5, citation 5.00/5, uncertainty 5.00/5.
- Worst run: `d93_nu_minus2_hysteresis_caution__run_000` score 0.826; answer `raw/tasks/d93_nu_minus2_hysteresis_caution/run_000/answer.md`.
- Best run: `d93_nu_minus2_hysteresis_caution__run_001` score 0.854; answer `raw/tasks/d93_nu_minus2_hysteresis_caution/run_001/answer.md`.

### displacement_field_topology
- Overall: 0.834 +/- 0.009 95% CI (min 0.812, max 0.863, n=10).
- Layers: retrieval 0.940, context 0.684, answer 0.954, judge 0.757.
- Failure rates: judge_citation_under_4 100%, judge_critical_errors 10%, judge_faithfulness_under_4 10%, weak_citation_precision_proxy 80%.
- Judge means: faithfulness 3.90/5, citation 3.00/5, uncertainty 4.90/5.
- Worst run: `displacement_field_topology__run_001` score 0.812; answer `raw/tasks/displacement_field_topology/run_001/answer.md`.
- Best run: `displacement_field_topology__run_004` score 0.863; answer `raw/tasks/displacement_field_topology/run_004/answer.md`.

### fci_evidence_hierarchy
- Overall: 0.919 +/- 0.010 95% CI (min 0.891, max 0.936, n=10).
- Layers: retrieval 1.000, context 0.944, answer 0.934, judge 0.797.
- Failure rates: judge_citation_under_4 60%, judge_faithfulness_under_4 20%, weak_citation_precision_proxy 10%.
- Judge means: faithfulness 3.80/5, citation 3.40/5, uncertainty 4.50/5.
- Worst run: `fci_evidence_hierarchy__run_006` score 0.891; answer `raw/tasks/fci_evidence_hierarchy/run_006/answer.md`.
- Best run: `fci_evidence_hierarchy__run_000` score 0.936; answer `raw/tasks/fci_evidence_hierarchy/run_000/answer.md`.

### low_conf_superconductivity_arxiv
- Overall: 0.759 +/- 0.011 95% CI (min 0.730, max 0.796, n=10).
- Layers: retrieval 1.000, context 0.550, answer 0.817, judge 0.669.
- Failure rates: context_miss 100%, judge_citation_under_4 100%, judge_critical_errors 80%, judge_faithfulness_under_4 90%, weak_citation_precision_proxy 100%.
- Judge means: faithfulness 2.50/5, citation 2.30/5, uncertainty 4.40/5.
- Worst run: `low_conf_superconductivity_arxiv__run_002` score 0.730; answer `raw/tasks/low_conf_superconductivity_arxiv/run_002/answer.md`.
- Best run: `low_conf_superconductivity_arxiv__run_001` score 0.796; answer `raw/tasks/low_conf_superconductivity_arxiv/run_001/answer.md`.

### minus_one_third_interpretation
- Overall: 0.861 +/- 0.006 95% CI (min 0.843, max 0.882, n=10).
- Layers: retrieval 0.940, context 0.769, answer 0.962, judge 0.774.
- Failure rates: answer_concept_miss 10%, context_miss 100%, judge_citation_under_4 90%, judge_critical_errors 10%, judge_faithfulness_under_4 60%, weak_citation_precision_proxy 10%.
- Judge means: faithfulness 3.40/5, citation 3.10/5, uncertainty 5.00/5.
- Worst run: `minus_one_third_interpretation__run_006` score 0.843; answer `raw/tasks/minus_one_third_interpretation/run_006/answer.md`.
- Best run: `minus_one_third_interpretation__run_001` score 0.882; answer `raw/tasks/minus_one_third_interpretation/run_001/answer.md`.

### moire_exciton_exclude_polariton
- Overall: 0.509 +/- 0.008 95% CI (min 0.492, max 0.527, n=10).
- Layers: retrieval 0.189, context 0.372, answer 0.812, judge 0.663.
- Failure rates: context_miss 100%, hard_negative_leak 100%, judge_citation_under_4 100%, judge_critical_errors 90%, judge_faithfulness_under_4 100%, retrieval_miss 100%, weak_citation_precision_proxy 20%.
- Judge means: faithfulness 2.60/5, citation 2.70/5, uncertainty 3.70/5.
- Worst run: `moire_exciton_exclude_polariton__run_009` score 0.492; answer `raw/tasks/moire_exciton_exclude_polariton/run_009/answer.md`.
- Best run: `moire_exciton_exclude_polariton__run_000` score 0.527; answer `raw/tasks/moire_exciton_exclude_polariton/run_000/answer.md`.

### optical_control_chern_states
- Overall: 0.912 +/- 0.007 95% CI (min 0.894, max 0.929, n=10).
- Layers: retrieval 0.920, context 0.940, answer 0.998, judge 0.789.
- Failure rates: judge_citation_under_4 90%, judge_critical_errors 60%, judge_faithfulness_under_4 80%.
- Judge means: faithfulness 3.20/5, citation 3.10/5, uncertainty 4.20/5.
- Worst run: `optical_control_chern_states__run_008` score 0.894; answer `raw/tasks/optical_control_chern_states/run_008/answer.md`.
- Best run: `optical_control_chern_states__run_000` score 0.929; answer `raw/tasks/optical_control_chern_states/run_000/answer.md`.

## Presentation Plots
- `plots/overall_quality_by_task.png`
- `plots/overall_quality_distribution_by_task.png`
- `plots/pipeline_layer_scores.png`
- `plots/pipeline_layer_scores_by_task.png`
- `plots/judge_metric_heatmap.png`
- `plots/failure_taxonomy.png`
- `plots/failure_rate_by_task.png`
- `plots/context_recall_vs_faithfulness.png`
- `plots/overall_score_histogram.png`
- `plots/answer_judge_latency.png`
