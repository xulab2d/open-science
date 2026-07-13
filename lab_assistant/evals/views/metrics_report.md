# OpenScience Runtime Metrics Report

Purpose:
- Quantitative smoke test for retrieval, context compilation, replay, memory mutation, and synthesis loops.

## Summary
- Eval tasks run: 27
- Passed: 27
- Failed: 0
- Pass rate: 1.000
- Latency p50 ms: 9.0
- Latency p95 ms: 19.099999999999998

## Suites
- `context_pack`: 5/5 passed
- `memory_write`: 3/3 passed
- `paper_lookup`: 5/5 passed
- `replay`: 3/3 passed
- `retrieval`: 8/8 passed
- `synthesis`: 3/3 passed

## Metric Means
- `actionability_mean`: 4.0000
- `context_chars_mean`: 12777.0000
- `context_compile_latency_ms_mean`: 64.0000
- `context_hash_stability_mean`: 1.0000
- `context_item_count_mean`: 11.6000
- `context_relevance_mean`: 1.0000
- `contradiction_awareness_mean`: 5.0000
- `contradiction_link_rate_mean`: 0.3333
- `duplicate_detection_rate_mean`: 0.3333
- `falsifiability_mean`: 5.0000
- `graph_search_latency_ms_mean`: 9.9231
- `groundedness_mean`: 5.0000
- `invalid_mutation_rate_mean`: 0.3333
- `irrelevant_item_rate_mean`: 0.0000
- `latency_ms_mean`: 16.6296
- `low_confidence_unsupported_use_mean`: 0.0000
- `mechanism_clarity_mean`: 4.0000
- `mrr_mean`: 0.8872
- `novelty_proxy_mean`: 4.0000
- `precision_at_5_mean`: 0.4808
- `promotion_count_mean`: 0.6667
- `proposed_mutation_count_mean`: 1.0000
- `provenance_completeness_mean`: 2.8333
- `provenance_coverage_mean`: 1.0000
- `rejection_count_mean`: 0.3333
- `replay_context_hash_match_mean`: 1.0000
- `retrieval_recall_at_5_mean`: 0.9231
- `retrieved_item_jaccard_mean`: 1.0000
- `stale_deprecated_fact_handling_mean`: 0.3333
- `synthesis_mean_score_mean`: 4.5714
- `token_estimate_mean`: 3194.6000
- `trajectory_schema_valid_mean`: 1.0000

## Failure Clusters
- none

## Recommended Candidate Improvements
- If retrieval recall or MRR fails, propose a retrieval-policy candidate and compare against this result file.
- If context chars grow without coverage gains, propose a context-policy budget candidate.
- If synthesis provenance completeness falls, tighten hypothesis mutation gates before graph promotion.
