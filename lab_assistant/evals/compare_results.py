#!/usr/bin/env python3
"""Compare baseline and candidate eval JSONL files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lab_assistant.runtime.metrics import compare_metric_maps, summarize_jsonl_records  # noqa: E402


LOWER_IS_BETTER = {
    "latency_ms_mean",
    "context_chars_mean",
    "context_compile_latency_ms_mean",
    "graph_search_latency_ms_mean",
    "low_confidence_unsupported_use_mean",
    "invalid_mutation_rate_mean",
    "irrelevant_item_rate_mean",
}

PROTECTED = {
    "pass_rate",
    "paper_lookup_precision_mean",
    "precision_at_5_mean",
    "replay_context_hash_match_mean",
    "context_hash_stability_mean",
}


def load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def numeric_summary(path: Path) -> dict[str, float]:
    summary = summarize_jsonl_records(load_records(path))
    metrics = dict(summary.get("metrics", {}))
    metrics["pass_rate"] = float(summary.get("pass_rate", 0.0))
    metrics["failed"] = float(summary.get("failed", 0))
    metrics["tasks"] = float(summary.get("tasks", 0))
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare OpenScience eval results.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = numeric_summary(args.baseline)
    candidate = numeric_summary(args.candidate)
    rows, regressions = compare_metric_maps(
        baseline,
        candidate,
        protected_metrics=PROTECTED,
        lower_is_better=LOWER_IS_BETTER,
    )
    print("metric\tbaseline\tcandidate\tdelta")
    for metric, row in sorted(rows.items()):
        print(f"{metric}\t{row['baseline']:.6g}\t{row['candidate']:.6g}\t{row['delta']:+.6g}")
    if regressions:
        print("\nprotected regressions:")
        for regression in regressions:
            print(
                f"- {regression.metric}: {regression.baseline:.6g} -> "
                f"{regression.candidate:.6g} ({regression.delta:+.6g})"
            )
    else:
        print("\nprotected regressions: none")
    payload = {
        "metrics": rows,
        "regressions": [regression.__dict__ for regression in regressions],
    }
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())
