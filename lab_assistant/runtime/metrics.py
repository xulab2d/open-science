"""Deterministic metrics used by trajectory and eval loops."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Any, Iterable


def recall_at_k(retrieved: list[str], relevant: Iterable[str], k: int) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 1.0
    hits = set(retrieved[:k]) & relevant_set
    return len(hits) / len(relevant_set)


def precision_at_k(retrieved: list[str], relevant: Iterable[str], k: int) -> float:
    if k <= 0:
        return 0.0
    relevant_set = set(relevant)
    if not retrieved[:k]:
        return 0.0
    hits = sum(1 for item in retrieved[:k] if item in relevant_set)
    return hits / min(k, len(retrieved[:k]))


def hit_at_k(retrieved: list[str], relevant: Iterable[str], k: int) -> float:
    relevant_set = set(relevant)
    return 1.0 if any(item in relevant_set for item in retrieved[:k]) else 0.0


def mean_reciprocal_rank(retrieved: list[str], relevant: Iterable[str]) -> float:
    relevant_set = set(relevant)
    for index, item in enumerate(retrieved, start=1):
        if item in relevant_set:
            return 1.0 / index
    return 0.0


def ndcg_at_k(retrieved: list[str], relevance: dict[str, float], k: int) -> float:
    def gain(rank: int, rel: float) -> float:
        import math

        return (2**rel - 1) / math.log2(rank + 1)

    dcg = sum(gain(rank, relevance.get(item, 0.0)) for rank, item in enumerate(retrieved[:k], start=1))
    ideal_values = sorted(relevance.values(), reverse=True)[:k]
    ideal = sum(gain(rank, rel) for rank, rel in enumerate(ideal_values, start=1))
    return dcg / ideal if ideal else 1.0


def jaccard_similarity(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    return len(left_set & right_set) / len(left_set | right_set)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct / 100.0
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def latency_summary(values: list[float]) -> dict[str, float | None]:
    return {
        "count": len(values),
        "p50": median(values) if values else None,
        "p95": percentile(values, 95),
        "max": max(values) if values else None,
    }


@dataclass(frozen=True)
class Regression:
    metric: str
    baseline: float
    candidate: float
    delta: float


def compare_metric_maps(
    baseline: dict[str, float],
    candidate: dict[str, float],
    protected_metrics: Iterable[str] = (),
    lower_is_better: Iterable[str] = (),
    tolerance: float = 1e-9,
) -> tuple[dict[str, dict[str, float]], list[Regression]]:
    lower_better = set(lower_is_better)
    protected = set(protected_metrics)
    all_metrics = sorted(set(baseline) | set(candidate))
    rows: dict[str, dict[str, float]] = {}
    regressions: list[Regression] = []
    for metric in all_metrics:
        if metric not in baseline or metric not in candidate:
            continue
        before = float(baseline[metric])
        after = float(candidate[metric])
        delta = after - before
        rows[metric] = {"baseline": before, "candidate": after, "delta": delta}
        regressed = delta > tolerance if metric in lower_better else delta < -tolerance
        if regressed and (not protected or metric in protected):
            regressions.append(Regression(metric=metric, baseline=before, candidate=after, delta=delta))
    return rows, regressions


def flatten_numeric_scores(records: list[dict[str, Any]]) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for record in records:
        scores = record.get("scores", {})
        if not isinstance(scores, dict):
            continue
        for key, value in scores.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                buckets.setdefault(key, []).append(float(value))
    return {f"{key}_mean": sum(values) / len(values) for key, values in buckets.items() if values}


def summarize_jsonl_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    latency_values = [
        float(record["scores"]["latency_ms"])
        for record in records
        if isinstance(record.get("scores"), dict) and isinstance(record["scores"].get("latency_ms"), (int, float))
    ]
    passed = sum(1 for record in records if record.get("passed") is True)
    failed = sum(1 for record in records if record.get("passed") is False)
    summary: dict[str, Any] = {
        "tasks": len(records),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / len(records) if records else 0.0,
        "latency_ms": latency_summary(latency_values),
        "metrics": flatten_numeric_scores(records),
    }
    suites: dict[str, dict[str, int]] = {}
    for record in records:
        suite = str(record.get("suite", "unknown"))
        bucket = suites.setdefault(suite, {"tasks": 0, "passed": 0, "failed": 0})
        bucket["tasks"] += 1
        if record.get("passed") is True:
            bucket["passed"] += 1
        elif record.get("passed") is False:
            bucket["failed"] += 1
    summary["suites"] = suites
    return summary


def main() -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Summarize OpenScience eval JSONL metrics.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    summarize = sub.add_parser("summarize")
    summarize.add_argument("--results", required=True)
    args = parser.parse_args()

    if args.cmd == "summarize":
        path = Path(args.results)
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(json.dumps(summarize_jsonl_records(records), indent=2, sort_keys=True))
        return 0
    raise SystemExit(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
