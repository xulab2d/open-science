# Presentation Outline: Current RAG Quality

## Slide 1: Evaluation Design
- Literature-inspired axes: retrieval ranking, context relevance/recall, faithfulness, citation support, abstention.
- 100 answer-level runs across 10 hard local scientific tasks spanning project context, hard negatives, multi-hop synthesis, freshness, and abstention.

## Slide 2: Overall Pipeline Scores
- Use `plots/pipeline_layer_scores.png`.
- Takeaway: this separates retrieval failures from context and generation failures.

## Slide 3: Task-Level Scorecard
- Use `plots/overall_quality_by_task.png`.
- Use error bars to show run-to-run variability.

## Slide 4: Score Distributions
- Use `plots/overall_quality_distribution_by_task.png` and `plots/overall_score_histogram.png`.
- Highlight low-scoring tasks as concrete weak spots.

## Slide 5: Judge Heatmap
- Use `plots/judge_metric_heatmap.png`.
- Discuss faithfulness/citation/uncertainty rather than only hit rate.

## Slide 6: Failure Taxonomy
- Use `plots/failure_taxonomy.png`.
- Use `plots/failure_rate_by_task.png` for task-specific reliability.
- Prioritize fixes by count and scientific risk.

## Slide 7: Context Recall vs Faithfulness
- Use `plots/context_recall_vs_faithfulness.png`.
- Diagnose whether poor answers come from retrieval/context or answer synthesis.

## Slide 8: Recommendations
- Unify graph search and context-pack search.
- Add negative filtering and project-aware routing.
- Add citation-support grading and abstention tests to CI.
- Expand gold hard tasks with human-reviewed expected evidence.
