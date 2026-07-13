# OpenScience Runtime Evals

Purpose:
- Evaluate trajectories, task-routed context packs, graph retrieval, memory mutation gates, and structured synthesis.
- Produce machine-readable JSONL/JSON plus a compact Markdown report.

Commands:
```bash
python3 lab_assistant/evals/run_evals.py --suite all --output lab_assistant/evals/results/latest.jsonl
python3 lab_assistant/evals/compare_results.py --baseline lab_assistant/evals/results/baseline.jsonl --candidate lab_assistant/evals/results/latest.jsonl
python3 -m lab_assistant.runtime.metrics summarize --results lab_assistant/evals/results/latest.jsonl
```

Fixture style:
- Files in `fixtures/` are JSON-compatible YAML.
- Each row is one task with explicit expected retrieval, context, replay, mutation, or synthesis behavior.
- LLM judging can be added later, but deterministic grounding/retrieval metrics remain primary.

Produced metrics include:
- Retrieval: recall@5, precision@5, MRR, provenance coverage, unsupported low-confidence use, latency.
- Context: chars, token estimate, item count, context hash stability, relevant coverage, compile latency.
- Replay: context pack ID match and retrieved item Jaccard similarity.
- Memory: proposal/promotion/rejection counts, mutation validity, provenance completeness.
- Synthesis: rubric scores for groundedness, falsifiability, mechanism clarity, contradiction awareness, novelty, actionability, and provenance.
