# Scientific Agent Runtime Implementation Report

## What Changed

- Added trajectory runtime modules in `runtime/`:
  - `snapshot.py`: deterministic repository/memory hashing.
  - `context_pack.py`: task-routed context compiler with budgets, item reasons, exclusions, and stable pack IDs.
  - `trajectory.py`: schema-validated trajectory records and CLI creation.
  - `replay.py`: deterministic replay checks for context pack stability.
  - `metrics.py`: retrieval, repeatability, latency, and regression metrics.
  - `mutation.py`: candidate archive with proposal, eval attachment, promote/reject decisions, and durable-mutation warnings.
- Added declarative policy in `context_policy/`.
- Added machine-readable skill metadata for fact graph, reference retrieval, knowledge maintenance, request triage, background cataloguing, and scientific synthesis.
- Added structured hypothesis support in `science/`.
- Extended the fact graph schema for belief-graph nodes and status fields while preserving existing JSONL graph commands.
- Added task-aware graph retrieval, adjacency/degree precomputation, and graph search latency reporting in `scripts/fact_graph.py`.
- Added eval harness, fixtures, results, report generation, and comparison scripts in `evals/`.
- Added pytest coverage for trajectory, context compiler, graph retrieval, metrics, mutation archive, and synthesis loops.

## Commands

Run tests from the repository root:

```bash
./lab_assistant/.venv-science/bin/python -m pytest lab_assistant/tests
```

Run all evals and regenerate the report:

```bash
python3 lab_assistant/evals/run_evals.py --suite all --output lab_assistant/evals/results/latest.jsonl
```

Compare a candidate against the current baseline:

```bash
python3 lab_assistant/evals/compare_results.py --baseline lab_assistant/evals/results/baseline.jsonl --candidate lab_assistant/evals/results/latest.jsonl
```

Compile a task-routed context pack:

```bash
python3 -m lab_assistant.runtime.context_pack --task-type paper_lookup --query "moire exciton optical signatures"
```

Create a dry-run trajectory:

```bash
python3 -m lab_assistant.runtime.trajectory new --task-type claim_lookup --input "RMCD hysteresis" --dry-run
```

## Current Metrics

Generated from `evals/results/latest.jsonl`:

- Eval tasks: 27
- Passed: 27
- Failed: 0
- Pass rate: 1.000
- Retrieval recall@5 mean: 0.9231
- Retrieval MRR mean: 0.8872
- Precision@5 mean: 0.4808
- Provenance coverage mean: 1.0000
- Unsupported low-confidence use mean: 0.0000
- Context relevance mean: 1.0000
- Context hash stability mean: 1.0000
- Context chars mean: 12603.4
- Context compile latency mean: 43.2 ms
- Replay context hash match mean: 1.0000
- Retrieved item Jaccard mean: 1.0000
- Duplicate detection rate mean: 0.3333
- Stale/deprecated fact handling mean: 0.3333
- Synthesis mean score: 4.5714
- Latency p50 ms: 9.0
- Latency p95 ms: 19.4
- Protected regressions vs `baseline.jsonl`: none

## Known Limitations

- The first-pass context compiler uses lexical graph retrieval; SQLite FTS/BM25 is not yet built.
- Synthesis generation is a deterministic scaffold, not a full LLM generate-critique-evolve loop.
- Memory mutations are candidate-gated and validated, but no automatic patch application gate is implemented.
- Baseline is the first measured baseline for this runtime, not a historical pre-change baseline.

## Next Closed Loop

Add a candidate runner that applies a patch in an isolated worktree, runs the eval harness, compares against baseline protected metrics, and moves the candidate to `promoted/` or `rejected/` based on policy.
