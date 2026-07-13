#!/usr/bin/env python3
"""Run deterministic OpenScience runtime eval fixtures."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS = REPO_ROOT / "lab_assistant" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lab_assistant.runtime.context_pack import build_context_pack  # noqa: E402
from lab_assistant.runtime.metrics import summarize_jsonl_records  # noqa: E402
from lab_assistant.runtime.mutation import (  # noqa: E402
    attach_eval_result,
    decide_candidate,
    propose_candidate,
    proposed_memory_mutation,
    validate_memory_mutation,
)
from lab_assistant.runtime.replay import replay_trajectory  # noqa: E402
from lab_assistant.runtime.trajectory import make_trajectory, write_trajectory  # noqa: E402
from lab_assistant.science.hypothesis import scaffold_hypothesis, score_hypothesis  # noqa: E402
from lab_assistant.runtime.snapshot import read_jsonish  # noqa: E402

import fact_graph  # noqa: E402


PACKAGE_ROOT = REPO_ROOT / "lab_assistant"
FIXTURE_DIR = PACKAGE_ROOT / "evals" / "fixtures"


SUITES = ["retrieval", "paper_lookup", "context_pack", "replay", "memory_write", "synthesis"]


def normalize(value: str) -> str:
    import re

    value = value.lower().replace("₂", "2")
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return " ".join(value.split())


def load_fixtures(suite: str) -> list[dict[str, Any]]:
    path = FIXTURE_DIR / f"{suite}.yaml"
    data = read_jsonish(path)
    if isinstance(data, dict):
        return list(data.get("fixtures", []))
    return list(data)


def _hit_expected(hit: dict[str, Any], expected: dict[str, Any]) -> bool:
    label = normalize(f"{hit.get('label', '')} {hit.get('summary', '')}")
    if "id" in expected and hit.get("id") == expected["id"]:
        return True
    if "label_contains" in expected and normalize(expected["label_contains"]) in label:
        return True
    return False


def _forbidden_hit(hit: dict[str, Any], forbidden: dict[str, Any]) -> bool:
    if "id" in forbidden and hit.get("id") == forbidden["id"]:
        return True
    if "label_contains" in forbidden:
        label = normalize(f"{hit.get('label', '')} {hit.get('summary', '')}")
        return normalize(forbidden["label_contains"]) in label
    return False


def _search_hits(query: str, task_type: str, limit: int) -> tuple[list[dict[str, Any]], int]:
    started = time.perf_counter()
    if hasattr(fact_graph, "task_aware_search"):
        hits = fact_graph.task_aware_search(query, task_type=task_type, limit=limit)
    else:
        raw_hits = fact_graph.search_nodes(query, limit=limit)
        hits = [
            {"id": node_id, "type": node.get("type"), "label": node.get("label"), "summary": node.get("summary"), "confidence": node.get("confidence"), "provenance": node.get("provenance", [])}
            for _score, node_id, node, _touching in raw_hits
        ]
    elapsed = int((time.perf_counter() - started) * 1000)
    return hits, elapsed


def eval_retrieval_fixture(fixture: dict[str, Any], suite: str) -> dict[str, Any]:
    task_type = fixture.get("task_type", "claim_lookup")
    metrics_req = fixture.get("metrics", {})
    k = int(metrics_req.get("k", 5))
    hits, latency_ms = _search_hits(fixture["query"], task_type, k)
    expected = fixture.get("expected", {})
    must_any = expected.get("must_retrieve_any", [])
    matched_expected = [item for item in must_any if any(_hit_expected(hit, item) for hit in hits[:k])]
    relevant_hit_indexes = [
        index
        for index, hit in enumerate(hits[:k], start=1)
        if any(_hit_expected(hit, item) for item in must_any)
    ]
    type_requirements = set(expected.get("must_retrieve_types", []))
    retrieved_types = {hit.get("type") for hit in hits[:k]}
    forbidden = expected.get("forbidden", [])
    forbidden_count = sum(1 for hit in hits[:k] for item in forbidden if _forbidden_hit(hit, item))
    recall = len(matched_expected) / len(must_any) if must_any else 1.0
    precision = len(relevant_hit_indexes) / len(hits[:k]) if hits[:k] else 0.0
    mrr = 1.0 / relevant_hit_indexes[0] if relevant_hit_indexes else 0.0
    provenance_coverage = (
        sum(1 for hit in hits[:k] if hit.get("provenance")) / len(hits[:k])
        if hits[:k]
        else 0.0
    )
    unsupported_low = (
        sum(1 for hit in hits[:k] if hit.get("confidence") == "low" and not hit.get("provenance")) / len(hits[:k])
        if hits[:k]
        else 0.0
    )
    passed = (
        recall >= float(metrics_req.get("recall_at_k_min", 0.0))
        and mrr >= float(metrics_req.get("mrr_min", 0.0))
        and precision >= float(metrics_req.get("precision_at_k_min", 0.0))
        and latency_ms <= int(metrics_req.get("max_latency_ms", 1_000_000))
        and type_requirements.issubset(retrieved_types)
        and forbidden_count == 0
        and (not metrics_req.get("require_provenance") or provenance_coverage > 0)
    )
    return {
        "suite": suite,
        "id": fixture["id"],
        "task_type": task_type,
        "query": fixture["query"],
        "passed": passed,
        "scores": {
            "retrieval_recall_at_5": recall,
            "precision_at_5": precision,
            "mrr": mrr,
            "provenance_coverage": provenance_coverage,
            "low_confidence_unsupported_use": unsupported_low,
            "latency_ms": latency_ms,
            "graph_search_latency_ms": latency_ms,
        },
        "retrieved": [{"id": hit.get("id"), "type": hit.get("type"), "label": hit.get("label")} for hit in hits],
        "failure_reasons": [] if passed else ["retrieval thresholds, type requirements, provenance, latency, or forbidden checks failed"],
    }


def eval_context_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    pack1, _ = build_context_pack(task_type=fixture["task_type"], query=fixture["query"], char_budget=fixture.get("char_budget"), write=False)
    pack2, _ = build_context_pack(task_type=fixture["task_type"], query=fixture["query"], char_budget=fixture.get("char_budget"), write=False)
    expected = fixture.get("expected", {})
    paths = {item.path for item in pack1.items if item.path}
    ids = {item.id for item in pack1.items}
    kinds = {item.kind for item in pack1.items}
    required_paths = set(expected.get("required_paths", []))
    required_ids = set(expected.get("required_item_ids", []))
    required_kinds = set(expected.get("required_kinds", []))
    forbidden_paths = set(expected.get("forbidden_paths", []))
    relevant_count = len(required_paths) + len(required_ids) + len(required_kinds)
    covered = len(required_paths & paths) + len(required_ids & ids) + len(required_kinds & kinds)
    coverage = covered / relevant_count if relevant_count else 1.0
    irrelevant_hits = len(forbidden_paths & paths)
    irrelevant_rate = irrelevant_hits / len(pack1.items) if pack1.items else 0.0
    same_hash = pack1.context_pack_id == pack2.context_pack_id
    metrics_req = fixture.get("metrics", {})
    passed = (
        same_hash
        and coverage >= float(metrics_req.get("required_coverage_min", 1.0))
        and pack1.metrics["chars"] <= int(metrics_req.get("max_chars", 1_000_000))
        and irrelevant_rate <= float(metrics_req.get("irrelevant_rate_max", 1.0))
    )
    return {
        "suite": "context_pack",
        "id": fixture["id"],
        "task_type": fixture["task_type"],
        "query": fixture["query"],
        "passed": passed,
        "scores": {
            "context_relevance": coverage,
            "irrelevant_item_rate": irrelevant_rate,
            "context_hash_stability": 1.0 if same_hash else 0.0,
            "context_chars": pack1.metrics["chars"],
            "context_item_count": pack1.metrics["item_count"],
            "context_compile_latency_ms": pack1.metrics["latency_ms"],
            "latency_ms": pack1.metrics["latency_ms"],
            "token_estimate": pack1.metrics["token_estimate"],
        },
        "context_pack_id": pack1.context_pack_id,
        "items": [item.public_dict() for item in pack1.items],
        "failure_reasons": [] if passed else ["context pack coverage, budget, or determinism check failed"],
    }


def eval_replay_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    pack, _ = build_context_pack(task_type=fixture["task_type"], query=fixture["query"], write=False)
    trajectory = make_trajectory(
        fixture["task_type"],
        fixture["query"],
        context_pack=pack.to_trajectory_dict(),
        trajectory_id=f"eval_{fixture['id']}",
        created_at="2026-01-01T00:00:00Z",
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = write_trajectory(trajectory, Path(tmp))
        replay = replay_trajectory(str(path))
    expected = fixture.get("expected", {})
    passed = (
        (not expected.get("same_context_pack_id", True) or replay["same_context_pack_id"])
        and replay["retrieved_item_jaccard"] >= float(fixture.get("metrics", {}).get("jaccard_min", 1.0))
    )
    return {
        "suite": "replay",
        "id": fixture["id"],
        "task_type": fixture["task_type"],
        "query": fixture["query"],
        "passed": passed,
        "scores": {
            "replay_context_hash_match": 1.0 if replay["same_context_pack_id"] else 0.0,
            "retrieved_item_jaccard": replay["retrieved_item_jaccard"],
            "trajectory_schema_valid": 1.0 if replay["trajectory_schema_valid"] else 0.0,
            "latency_ms": 0,
        },
        "replay": replay,
        "failure_reasons": [] if passed else ["replay stability check failed"],
    }


def eval_memory_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "improvements"
        candidate = propose_candidate(
            name=fixture["candidate_name"],
            from_trajectory=fixture.get("from_trajectory", "manual"),
            hypothesis=fixture.get("hypothesis"),
            target_metrics=fixture.get("target_metrics"),
            protected_metrics=fixture.get("protected_metrics"),
            archive_root=archive,
            created_at="2026-01-01T00:00:00Z",
        )
        mutation = proposed_memory_mutation(
            mutation_type=fixture.get("mutation_type", "knowledge_note"),
            target_path=fixture.get("target_path", "lab_assistant/memory/review_log.md"),
            rationale=fixture.get("rationale", "eval mutation proposal"),
            payload=fixture.get("payload", {"note": fixture["id"]}),
            candidate_id=candidate.candidate_id if fixture.get("with_candidate", True) else None,
        )
        valid, warnings = validate_memory_mutation(mutation)
        attach_eval_result(candidate.candidate_id, {"suite": "memory_write", "passed": valid, "warnings": warnings}, archive_root=archive)
        if fixture.get("decision"):
            decide_candidate(candidate.candidate_id, fixture["decision"], "eval decision", archive_root=archive)
    expected_valid = fixture.get("expected", {}).get("valid_mutation", True)
    passed = valid is expected_valid
    return {
        "suite": "memory_write",
        "id": fixture["id"],
        "task_type": "memory_update",
        "query": fixture.get("hypothesis", fixture["candidate_name"]),
        "passed": passed,
        "scores": {
            "proposed_mutation_count": 1,
            "promotion_count": 1 if fixture.get("decision") == "promoted" else 0,
            "rejection_count": 1 if fixture.get("decision") == "rejected" else 0,
            "provenance_completeness": 1.0 if mutation.get("candidate_id") else 0.0,
            "invalid_mutation_rate": 0.0 if valid else 1.0,
            "duplicate_detection_rate": 1.0 if fixture.get("payload", {}).get("duplicate_of") else 0.0,
            "contradiction_link_rate": 1.0 if fixture.get("payload", {}).get("contradiction") else 0.0,
            "stale_deprecated_fact_handling": 1.0 if fixture.get("payload", {}).get("status") in {"deprecated", "weakened", "rejected"} else 0.0,
            "latency_ms": 0,
        },
        "mutation": mutation,
        "warnings": warnings,
        "failure_reasons": [] if passed else ["memory mutation validity did not match expected"],
    }


def eval_synthesis_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    hypothesis = scaffold_hypothesis(fixture["query"])
    score = score_hypothesis(hypothesis.to_dict())
    metrics_req = fixture.get("metrics", {})
    min_score = float(metrics_req.get("mean_score_min", 0.0))
    min_provenance = float(metrics_req.get("provenance_completeness_min", 0.0))
    passed = score["mean_score"] >= min_score and score["scores"]["provenance_completeness"] >= min_provenance and not score["errors"]
    return {
        "suite": "synthesis",
        "id": fixture["id"],
        "task_type": "hypothesis_generation",
        "query": fixture["query"],
        "passed": passed,
        "scores": {
            **score["scores"],
            "synthesis_mean_score": score["mean_score"],
            "latency_ms": 0,
        },
        "hypothesis": hypothesis.to_dict(),
        "rubric_version": score["rubric_version"],
        "failure_reasons": [] if passed else ["synthesis rubric thresholds failed"],
    }


def run_suite(suite: str) -> list[dict[str, Any]]:
    fixtures = load_fixtures(suite)
    records = []
    for fixture in fixtures:
        if suite in {"retrieval", "paper_lookup"}:
            records.append(eval_retrieval_fixture(fixture, suite))
        elif suite == "context_pack":
            records.append(eval_context_fixture(fixture))
        elif suite == "replay":
            records.append(eval_replay_fixture(fixture))
        elif suite == "memory_write":
            records.append(eval_memory_fixture(fixture))
        elif suite == "synthesis":
            records.append(eval_synthesis_fixture(fixture))
        else:
            raise ValueError(f"unknown suite: {suite}")
    return records


def run_suites(suite: str) -> list[dict[str, Any]]:
    if suite == "all":
        records: list[dict[str, Any]] = []
        for name in SUITES:
            records.extend(run_suite(name))
        return records
    return run_suite(suite)


def write_results(records: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
    summary = summarize_jsonl_records(records)
    summary_path = output.parent / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    latest_path = output.parent / "latest.jsonl"
    if output.resolve() != latest_path.resolve():
        latest_path.write_text(output.read_text(encoding="utf-8"), encoding="utf-8")
    write_report(records, summary, PACKAGE_ROOT / "evals" / "views" / "metrics_report.md")


def write_report(records: list[dict[str, Any]], summary: dict[str, Any], path: Path) -> None:
    failures = [record for record in records if not record.get("passed")]
    metric_means = summary.get("metrics", {})
    lines = [
        "# OpenScience Runtime Metrics Report",
        "",
        "Purpose:",
        "- Quantitative smoke test for retrieval, context compilation, replay, memory mutation, and synthesis loops.",
        "",
        "## Summary",
        f"- Eval tasks run: {summary['tasks']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Pass rate: {summary['pass_rate']:.3f}",
        f"- Latency p50 ms: {summary['latency_ms']['p50']}",
        f"- Latency p95 ms: {summary['latency_ms']['p95']}",
        "",
        "## Suites",
    ]
    for suite, stats in sorted(summary.get("suites", {}).items()):
        lines.append(f"- `{suite}`: {stats['passed']}/{stats['tasks']} passed")
    lines.extend(["", "## Metric Means"])
    for key in sorted(metric_means):
        value = metric_means[key]
        lines.append(f"- `{key}`: {value:.4f}")
    lines.extend(["", "## Failure Clusters"])
    if failures:
        for record in failures[:20]:
            reason = "; ".join(record.get("failure_reasons", [])) or "unspecified"
            lines.append(f"- `{record['suite']}/{record['id']}`: {reason}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommended Candidate Improvements",
            "- If retrieval recall or MRR fails, propose a retrieval-policy candidate and compare against this result file.",
            "- If context chars grow without coverage gains, propose a context-policy budget candidate.",
            "- If synthesis provenance completeness falls, tighten hypothesis mutation gates before graph promotion.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenScience runtime evals.")
    parser.add_argument("--suite", default="all", choices=["all", *SUITES])
    parser.add_argument("--output", type=Path, default=PACKAGE_ROOT / "evals" / "results" / "latest.jsonl")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = run_suites(args.suite)
    write_results(records, args.output)
    passed = sum(1 for record in records if record.get("passed"))
    print(f"evals: {passed}/{len(records)} passed")
    print(f"results: {args.output}")
    print(f"summary: {args.output.parent / 'summary.json'}")
    print(f"report: {PACKAGE_ROOT / 'evals' / 'views' / 'metrics_report.md'}")
    return 0 if passed == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
