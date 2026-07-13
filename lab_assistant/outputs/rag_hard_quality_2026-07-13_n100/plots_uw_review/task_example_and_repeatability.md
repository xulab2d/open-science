# Example Scientific Task and Repeatability Readout

## Worked Example: Moire Exciton Hard Negative

Task ID: `moire_exciton_exclude_polariton`

Prompt: Find the key local references for moire exciton optical signatures, but exclude exciton-polariton or waveguide papers unless they directly address moire trapping.

Why this is hard:
- It asks for moire-exciton optical-signature references.
- It explicitly forbids exciton-polariton or waveguide distractors unless they directly address moire trapping.
- The evaluator therefore tests both positive retrieval and negative filtering.

Gold rubric encoded in the task:
- Required evidence groups: one group for moire exciton language; one group for moire-trapped valley exciton language.
- Required answer concepts: moire exciton, optical/PL/photoluminescence, and explicit exclusion of distractors.
- Forbidden retrieval terms: `polariton`, `waveguide`.
- Forbidden answer titles: polariton/waveguide papers that should not be recommended.
- Citation expectation: cite graph/paper IDs or `knowledge/papers/moire_excitons_and_optics.md`.

Run 000 metric trace:
- Retrieval: recall@10 `0.50`, precision@10 `0.10`, MRR `0.14`, nDCG@10 `0.20`.
- Retrieval hard-negative problem: first relevant hit was rank `7`, while forbidden polariton/waveguide hits appeared at the top of retrieval.
- Context: recall `0.50`, precision proxy `0.24`.
- Deterministic answer checks: concept coverage `1.00`, citation precision proxy `1.00`, behavior OK `True`.
- LLM judge: context relevance `3/5`, faithfulness `3/5`, citation quality `3/5`, scientific correctness `3/5`.
- Composite scores: retrieval `0.189`, context `0.372`, answer `0.833`, judge `0.714`, overall `0.527`.

Scoring model:
- Retrieval score averages recall@10, precision@10, MRR, nDCG@10, and a binary no-forbidden-retrieval-hit term.
- Context score averages context recall and an average-precision-like context precision proxy.
- Deterministic answer score averages required concept coverage, citation precision proxy, required citation-pattern coverage, expected behavior, atomic support proxy, and absence of forbidden answer terms.
- Judge score averages seven normalized 1-5 judge metrics: context relevance, answer relevance, faithfulness, citation quality, scientific correctness, uncertainty calibration, and actionability.
- Overall score is the mean of retrieval, context, deterministic answer, and judge scores.

Interpretation for this example:
- The answer often understands the task, but retrieval brings polariton/waveguide distractors to the top.
- That creates low retrieval score and weak judge faithfulness/citation quality even when the final answer tries to exclude the distractors.
- This is a concrete negative-filtering failure, not just a generation failure.

## Repeatability Summary

Across all tasks, mean overall score is `0.756 +/- 0.031` 95% CI.
Per-task run-to-run variation is small compared with between-task differences.

| Task | Mean | Std | 95% CI | Min | Max | Span |
|---|---:|---:|---:|---:|---:|---:|
| B79 Curie temp abstention | 0.463 | 0.035 | 0.022 | 0.410 | 0.501 | 0.090 |
| Low-conf arXiv caution | 0.759 | 0.018 | 0.011 | 0.730 | 0.796 | 0.065 |
| Displacement-field topology | 0.834 | 0.014 | 0.009 | 0.812 | 0.863 | 0.051 |
| FCI evidence hierarchy | 0.919 | 0.017 | 0.010 | 0.891 | 0.936 | 0.045 |
| -1/3 interpretation | 0.861 | 0.010 | 0.006 | 0.843 | 0.882 | 0.039 |
| A5 dot project context | 0.641 | 0.010 | 0.006 | 0.619 | 0.655 | 0.036 |
| Optical control of Chern states | 0.912 | 0.011 | 0.007 | 0.894 | 0.929 | 0.036 |
| Moire exciton hard negative | 0.509 | 0.013 | 0.008 | 0.492 | 0.527 | 0.036 |
| B79 project context | 0.819 | 0.008 | 0.005 | 0.803 | 0.831 | 0.029 |
| D93 nu=-2 caution | 0.839 | 0.008 | 0.005 | 0.826 | 0.854 | 0.028 |

Presentation figures:
- `09_repeatability_run_scores.*` shows every run-level overall score.
- `10_repeatability_variation.*` ranks tasks by score span and CI.
- Raw repeatability table: `repeatability_stats.csv`.
