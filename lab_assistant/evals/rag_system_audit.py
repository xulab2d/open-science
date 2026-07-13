#!/usr/bin/env python3
"""Comprehensive local audit for OpenScience RAG and fact-graph infrastructure.

The existing eval runner is intentionally deterministic and small. This script
keeps that baseline, then adds stress probes for retrieval, context packing,
latency, graph structure, route divergence, and optional Codex answer trials.
It writes all findings into a timestamped folder so repeated audits are easy to
compare without overwriting the tracked eval views.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "lab_assistant"
SCRIPTS_DIR = PACKAGE_ROOT / "scripts"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lab_assistant.evals.run_evals import run_suites  # noqa: E402
from lab_assistant.runtime.context_pack import build_context_pack  # noqa: E402
from lab_assistant.runtime.metrics import summarize_jsonl_records  # noqa: E402

import fact_graph  # noqa: E402


try:  # Plotting is useful but should not block raw-data generation.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - environment dependent
    plt = None


def normalize(value: str) -> str:
    value = value.lower()
    value = value.replace("₂", "2").replace("–", "-").replace("—", "-").replace("−", "-")
    value = re.sub(r"[^a-z0-9ν ]+", " ", value)
    return " ".join(value.split())


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:80]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * pct / 100.0
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    weight = index - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


@dataclass(frozen=True)
class StressTask:
    id: str
    category: str
    task_type: str
    query: str
    expected_any: tuple[str, ...] = ()
    forbidden_any: tuple[str, ...] = ()
    expected_types: tuple[str, ...] = ()
    note: str = ""


STRESS_TASKS: tuple[StressTask, ...] = (
    StressTask(
        id="golden_fqah_optical_control",
        category="golden",
        task_type="claim_lookup",
        query="fractional Chern optical control",
        expected_any=("optical pumping", "fractional Chern"),
        expected_types=("Claim",),
    ),
    StressTask(
        id="golden_rmcd_hysteresis",
        category="golden",
        task_type="claim_lookup",
        query="RMCD hysteresis magnetic transition",
        expected_any=("RMCD", "hysteresis"),
        expected_types=("Claim",),
    ),
    StressTask(
        id="golden_moire_exciton_papers",
        category="golden",
        task_type="paper_lookup",
        query="moire exciton optical signatures",
        expected_any=("Moire excitons", "moiré-trapped valley excitons"),
        expected_types=("Paper",),
    ),
    StressTask(
        id="golden_local_probe_bulk_edge",
        category="golden",
        task_type="paper_lookup",
        query="fractional Chern insulator local probe bulk edge",
        expected_any=("Local probe of bulk and edge states",),
        expected_types=("Paper",),
    ),
    StressTask(
        id="alias_fqah",
        category="alias_robustness",
        task_type="claim_lookup",
        query="FQAH optical pumping twisted MoTe2",
        expected_any=("optical pumping", "fractional Chern"),
        expected_types=("Claim",),
    ),
    StressTask(
        id="alias_fractional_anomalous_hall",
        category="alias_robustness",
        task_type="claim_lookup",
        query="fractional anomalous Hall optical probe PL RMCD",
        expected_any=("PL", "RMCD"),
        expected_types=("Claim",),
    ),
    StressTask(
        id="alias_unicode_mote2",
        category="alias_robustness",
        task_type="paper_lookup",
        query="twisted MoTe₂ fractional anomalous Hall signatures",
        expected_any=("twisted MoTe2", "Fractional Quantum Anomalous Hall"),
        expected_types=("Paper",),
    ),
    StressTask(
        id="alias_nu_symbol",
        category="alias_robustness",
        task_type="claim_lookup",
        query="ν = -1/3 PL spectrum magnetic field dispersion",
        expected_any=("nu=-1/3", "PL spectrum"),
        expected_types=("Claim",),
    ),
    StressTask(
        id="project_d93_no_hysteresis",
        category="lab_project",
        task_type="claim_lookup",
        query="D93 Run2 near nu=-2 RMCD no clear hysteresis displacement field",
        expected_any=("D93 Run2", "no clear hysteresis"),
        expected_types=("Claim", "OpenQuestion"),
    ),
    StressTask(
        id="project_a5_dot",
        category="lab_project",
        task_type="synthesis",
        query="A5 dot optical project PL dispersion peak tracking",
        expected_any=("A5 dot", "PL dispersion"),
    ),
    StressTask(
        id="project_b79",
        category="lab_project",
        task_type="synthesis",
        query="B79 RMCD PL project context",
        expected_any=("B79",),
    ),
    StressTask(
        id="project_active_status",
        category="lab_project",
        task_type="synthesis",
        query="active tMoTe2 projects RMCD PL D93 A5",
        expected_any=("D93", "A5"),
    ),
    StressTask(
        id="mechanism_optical_pumping",
        category="mechanism",
        task_type="synthesis",
        query="mechanism connecting optical pumping to writing Chern ferromagnet domains",
        expected_any=("optical pumping", "Chern"),
    ),
    StressTask(
        id="mechanism_displacement_field",
        category="mechanism",
        task_type="synthesis",
        query="displacement field tunes topology in twisted MoTe2 observables",
        expected_any=("displacement field", "MoTe2"),
    ),
    StressTask(
        id="evidence_hierarchy_fci",
        category="multi_hop",
        task_type="synthesis",
        query="evidence hierarchy for fractional Chern insulator transport compressibility optical local probe",
        expected_any=("compressibility", "transport", "local"),
    ),
    StressTask(
        id="multi_hop_bulk_edge_artifact",
        category="multi_hop",
        task_type="synthesis",
        query="why local compressibility helps distinguish bulk FCI behavior from edge transport artifacts",
        expected_any=("compressibility", "bulk", "edge"),
    ),
    StressTask(
        id="open_question_d93",
        category="open_question",
        task_type="contradiction_search",
        query="D93 near nu=-2 magnetic contrast without robust hysteresis uncertainty",
        expected_any=("without robust hysteresis",),
        expected_types=("OpenQuestion", "Claim", "Contradiction"),
    ),
    StressTask(
        id="open_question_fractional_interpretation",
        category="open_question",
        task_type="contradiction_search",
        query="competing interpretations nu=-1/3 FQAH optical signature charge density wave fractional Chern",
        expected_any=("fractional", "Chern"),
        expected_types=("OpenQuestion", "Contradiction", "Claim"),
    ),
    StressTask(
        id="hard_negative_exclude_polariton",
        category="negative",
        task_type="paper_lookup",
        query="moiré excitons exclude exciton polariton waveguide papers",
        expected_any=("moire excitons", "moiré-trapped valley excitons"),
        forbidden_any=("polariton", "waveguide"),
        expected_types=("Paper",),
    ),
    StressTask(
        id="hard_negative_d93_robust_hysteresis",
        category="negative",
        task_type="claim_lookup",
        query="D93 robust hysteretic nu=-2 magnetic state",
        expected_any=("D93", "no clear"),
        expected_types=("Claim", "OpenQuestion"),
    ),
    StressTask(
        id="freshness_low_conf_arxiv_superconductivity",
        category="freshness",
        task_type="synthesis",
        query="low-confidence arXiv superconductivity near fractional Chern states worth promotion",
        expected_any=("superconduct", "fractional Chern"),
    ),
    StressTask(
        id="paper_cri3_gate_control",
        category="golden",
        task_type="paper_lookup",
        query="gate control bilayer cri3 magnetism",
        expected_any=("Electrical control of 2D magnetism",),
        expected_types=("Paper",),
    ),
    StressTask(
        id="paper_wte2_edges",
        category="golden",
        task_type="paper_lookup",
        query="edge conduction monolayer WTe2 helical edge",
        expected_any=("Edge conduction", "Quantum Spin Hall Edges"),
        expected_types=("Paper",),
    ),
    StressTask(
        id="claim_second_moire_band",
        category="golden",
        task_type="claim_lookup",
        query="second moire band ferromagnetism",
        expected_any=("second moiré band", "ferromagnetic"),
        expected_types=("Claim",),
    ),
)


CONTEXT_PROBES: tuple[dict[str, Any], ...] = (
    {"id": "paper_moire_exciton", "task_type": "paper_lookup", "query": "moire exciton optical signatures", "expected": ("moire", "exciton")},
    {"id": "claim_d93", "task_type": "claim_lookup", "query": "D93 Run2 near nu=-2 no clear hysteresis", "expected": ("D93", "hysteresis")},
    {"id": "synthesis_fci_evidence", "task_type": "synthesis", "query": "evidence hierarchy for fractional Chern insulator", "expected": ("compressibility", "transport", "optical")},
    {"id": "hypothesis_optical_control", "task_type": "hypothesis_generation", "query": "optical pumping can write Chern ferromagnet domains", "expected": ("optical", "Chern")},
    {"id": "memory_plot_convention", "task_type": "memory_update", "query": "record corrected RMCD plotting convention with provenance", "expected": ("provenance", "memory")},
    {"id": "project_status_active", "task_type": "project_status", "query": "what changed in active tMoTe2 projects", "expected": ("active", "project")},
)


CODEX_TASKS: tuple[dict[str, Any], ...] = (
    {
        "id": "codex_d93_caution",
        "task_type": "claim_lookup",
        "query": "Do we have enough local evidence to claim D93 has a robust hysteretic nu=-2 magnetic state?",
        "expected_terms": ("D93", "no clear hysteresis", "uncertain"),
        "forbidden_terms": ("definitively robust",),
    },
    {
        "id": "codex_fci_evidence",
        "task_type": "synthesis",
        "query": "Rank evidence types for a fractional Chern insulator and explain what each rules out.",
        "expected_terms": ("transport", "compressibility", "local", "optical", "uncertainty"),
        "forbidden_terms": (),
    },
    {
        "id": "codex_moire_exciton",
        "task_type": "paper_lookup",
        "query": "What are the key local references for moire exciton optical signatures?",
        "expected_terms": ("moire", "exciton", "provenance"),
        "forbidden_terms": (),
    },
    {
        "id": "codex_optical_control",
        "task_type": "synthesis",
        "query": "Summarize what the local graph says about optical control of integer and fractional Chern states.",
        "expected_terms": ("optical", "Chern", "pumping", "fractional"),
        "forbidden_terms": (),
    },
)


def match_fragments(text: str, fragments: tuple[str, ...]) -> list[str]:
    norm = normalize(text)
    return [fragment for fragment in fragments if normalize(fragment) in norm]


def top_hit_text(hit: dict[str, Any]) -> str:
    return f"{hit.get('label', '')} {hit.get('summary', '')}"


def run_existing_evals() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records = run_suites("all")
    return records, summarize_jsonl_records(records)


def graph_structure() -> dict[str, Any]:
    nodes, edges = fact_graph.load_graph()
    node_values = list(nodes.values())
    by_type = Counter(str(node.get("type", "unknown")) for node in node_values)
    by_confidence = Counter(str(node.get("confidence", "unknown")) for node in node_values)
    provenance_methods: Counter[str] = Counter()
    source_files: Counter[str] = Counter()
    for node in node_values:
        for item in node.get("provenance", []):
            if not isinstance(item, dict):
                continue
            provenance_methods[item.get("method", "unknown")] += 1
            source_files[item.get("source", "unknown")] += 1

    degrees: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()
    edge_confidence: Counter[str] = Counter()
    for edge in edges:
        degrees[edge.get("source", "")] += 1
        degrees[edge.get("target", "")] += 1
        relation_counts[edge.get("relation", "unknown")] += 1
        edge_confidence[edge.get("confidence", "unknown")] += 1
    isolated = [node_id for node_id in nodes if degrees.get(node_id, 0) == 0]
    degree_values = [degrees.get(node_id, 0) for node_id in nodes]

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(sorted(by_type.items())),
        "node_confidence_counts": dict(sorted(by_confidence.items())),
        "edge_relation_counts": dict(sorted(relation_counts.items())),
        "edge_confidence_counts": dict(sorted(edge_confidence.items())),
        "provenance_method_counts": dict(provenance_methods.most_common()),
        "top_source_files": dict(source_files.most_common(25)),
        "degree": {
            "mean": statistics.mean(degree_values) if degree_values else 0,
            "median": statistics.median(degree_values) if degree_values else 0,
            "p95": percentile([float(v) for v in degree_values], 95),
            "max": max(degree_values) if degree_values else 0,
            "isolated_count": len(isolated),
            "isolated_sample": isolated[:25],
            "top_nodes": [
                {"id": node_id, "degree": degree, "type": nodes[node_id].get("type"), "label": nodes[node_id].get("label")}
                for node_id, degree in degrees.most_common(25)
                if node_id in nodes
            ],
        },
    }


def evaluate_stress_task(task: StressTask, top_k: int) -> dict[str, Any]:
    start = time.perf_counter()
    hits = fact_graph.task_aware_search(task.query, task_type=task.task_type, limit=max(top_k, 10))
    latency_ms = (time.perf_counter() - start) * 1000.0
    top = hits[:top_k]

    expected_matches: dict[str, list[int]] = {}
    for fragment in task.expected_any:
        expected_matches[fragment] = [
            index
            for index, hit in enumerate(top, start=1)
            if normalize(fragment) in normalize(top_hit_text(hit))
        ]
    matched_expected = [fragment for fragment, ranks in expected_matches.items() if ranks]
    first_rank = min((ranks[0] for ranks in expected_matches.values() if ranks), default=None)
    forbidden_hits = []
    for index, hit in enumerate(top, start=1):
        for fragment in task.forbidden_any:
            if normalize(fragment) in normalize(top_hit_text(hit)):
                forbidden_hits.append({"rank": index, "fragment": fragment, "id": hit.get("id"), "label": hit.get("label")})

    expected_types = set(task.expected_types)
    retrieved_types = {str(hit.get("type")) for hit in top}
    type_ok = bool(expected_types & retrieved_types) if expected_types else True
    recall = len(matched_expected) / len(task.expected_any) if task.expected_any else 1.0
    precision = (
        sum(1 for hit in top if any(normalize(fragment) in normalize(top_hit_text(hit)) for fragment in task.expected_any)) / len(top)
        if top and task.expected_any
        else 0.0
    )
    hit_at_k = 1.0 if first_rank is not None else 0.0
    mrr = 1.0 / first_rank if first_rank else 0.0
    provenance_coverage = sum(1 for hit in top if hit.get("provenance")) / len(top) if top else 0.0
    low_confidence_share = sum(1 for hit in top if hit.get("confidence") == "low") / len(top) if top else 0.0
    passed = bool(hit_at_k) and type_ok and not forbidden_hits

    pack_start = time.perf_counter()
    pack, _ = build_context_pack(task_type=task.task_type, query=task.query, write=False)
    pack_latency_ms = (time.perf_counter() - pack_start) * 1000.0
    context_graph_ids = [item.id for item in pack.items if item.kind == "graph_node"]
    retrieval_ids = [str(hit.get("id")) for hit in top]
    overlap = len(set(retrieval_ids) & set(context_graph_ids[:top_k]))
    context_text = "\n".join(item.content for item in pack.items)
    context_expected_matches = match_fragments(context_text, task.expected_any)

    return {
        "id": task.id,
        "category": task.category,
        "task_type": task.task_type,
        "query": task.query,
        "note": task.note,
        "passed": passed,
        "hit_at_k": hit_at_k,
        "recall_at_k": recall,
        "precision_at_k": precision,
        "mrr": mrr,
        "first_relevant_rank": first_rank,
        "type_ok": type_ok,
        "forbidden_count": len(forbidden_hits),
        "forbidden_hits": forbidden_hits,
        "matched_expected": matched_expected,
        "missed_expected": [fragment for fragment in task.expected_any if fragment not in matched_expected],
        "provenance_coverage": provenance_coverage,
        "low_confidence_share": low_confidence_share,
        "retrieval_latency_ms": latency_ms,
        "context_compile_latency_ms": pack_latency_ms,
        "context_chars": pack.metrics["chars"],
        "context_items": pack.metrics["item_count"],
        "context_excluded": pack.metrics["excluded_count"],
        "context_graph_nodes": len(context_graph_ids),
        "context_expected_coverage": len(context_expected_matches) / len(task.expected_any) if task.expected_any else 1.0,
        "context_matched_expected": context_expected_matches,
        "route_overlap_at_k": overlap / len(retrieval_ids) if retrieval_ids else 1.0,
        "retrieved": [
            {
                "rank": index,
                "id": hit.get("id"),
                "type": hit.get("type"),
                "label": hit.get("label"),
                "confidence": hit.get("confidence"),
                "score": hit.get("score"),
                "edge_count": hit.get("edge_count"),
                "has_provenance": bool(hit.get("provenance")),
            }
            for index, hit in enumerate(top, start=1)
        ],
        "context_graph_ids": context_graph_ids,
    }


def run_stress_suite(top_k: int) -> list[dict[str, Any]]:
    return [evaluate_stress_task(task, top_k=top_k) for task in STRESS_TASKS]


def run_context_probes(budgets: list[int]) -> list[dict[str, Any]]:
    records = []
    for probe in CONTEXT_PROBES:
        for budget in budgets:
            start = time.perf_counter()
            pack, _ = build_context_pack(
                task_type=probe["task_type"],
                query=probe["query"],
                char_budget=budget,
                write=False,
            )
            latency_ms = (time.perf_counter() - start) * 1000.0
            content = "\n".join(item.content for item in pack.items)
            expected = tuple(probe.get("expected", ()))
            matched = match_fragments(content, expected)
            by_kind = Counter(item.kind for item in pack.items)
            records.append(
                {
                    "id": probe["id"],
                    "task_type": probe["task_type"],
                    "query": probe["query"],
                    "budget": budget,
                    "chars": pack.metrics["chars"],
                    "token_estimate": pack.metrics["token_estimate"],
                    "item_count": pack.metrics["item_count"],
                    "excluded_count": pack.metrics["excluded_count"],
                    "latency_ms": latency_ms,
                    "budget_used_fraction": pack.metrics["chars"] / budget if budget else None,
                    "expected_coverage": len(matched) / len(expected) if expected else 1.0,
                    "matched_expected": matched,
                    "kind_counts": dict(sorted(by_kind.items())),
                    "items": [item.public_dict() for item in pack.items],
                    "excluded": [item.__dict__ for item in pack.excluded],
                }
            )
    return records


def run_latency_samples(repeats: int, top_k: int) -> list[dict[str, Any]]:
    rows = []
    for task in STRESS_TASKS:
        for repeat in range(repeats):
            start = time.perf_counter()
            hits = fact_graph.task_aware_search(task.query, task_type=task.task_type, limit=top_k)
            rows.append(
                {
                    "id": task.id,
                    "category": task.category,
                    "task_type": task.task_type,
                    "operation": "task_aware_search",
                    "repeat": repeat,
                    "latency_ms": (time.perf_counter() - start) * 1000.0,
                    "hit_count": len(hits),
                }
            )
    for probe in CONTEXT_PROBES:
        for repeat in range(max(1, repeats // 4)):
            start = time.perf_counter()
            pack, _ = build_context_pack(task_type=probe["task_type"], query=probe["query"], write=False)
            rows.append(
                {
                    "id": probe["id"],
                    "category": "context_probe",
                    "task_type": probe["task_type"],
                    "operation": "context_pack",
                    "repeat": repeat,
                    "latency_ms": (time.perf_counter() - start) * 1000.0,
                    "hit_count": pack.metrics["item_count"],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = {
                key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value
                for key, value in row.items()
            }
            writer.writerow(flat)


def summarize_stress(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, Any]] = {}
    by_task_type: dict[str, dict[str, Any]] = {}
    for key, bucket_name in (("category", "category"), ("task_type", "task_type")):
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            groups[str(record[key])].append(record)
        target = by_category if bucket_name == "category" else by_task_type
        for group, rows in sorted(groups.items()):
            target[group] = {
                "tasks": len(rows),
                "passed": sum(1 for row in rows if row["passed"]),
                "pass_rate": sum(1 for row in rows if row["passed"]) / len(rows),
                "hit_at_k_mean": statistics.mean(row["hit_at_k"] for row in rows),
                "recall_at_k_mean": statistics.mean(row["recall_at_k"] for row in rows),
                "precision_at_k_mean": statistics.mean(row["precision_at_k"] for row in rows),
                "mrr_mean": statistics.mean(row["mrr"] for row in rows),
                "route_overlap_at_k_mean": statistics.mean(row["route_overlap_at_k"] for row in rows),
                "context_expected_coverage_mean": statistics.mean(row["context_expected_coverage"] for row in rows),
                "retrieval_latency_ms_median": statistics.median(row["retrieval_latency_ms"] for row in rows),
                "context_compile_latency_ms_median": statistics.median(row["context_compile_latency_ms"] for row in rows),
            }
    return {
        "tasks": len(records),
        "passed": sum(1 for row in records if row["passed"]),
        "failed": sum(1 for row in records if not row["passed"]),
        "pass_rate": sum(1 for row in records if row["passed"]) / len(records) if records else 0.0,
        "hit_at_k_mean": statistics.mean(row["hit_at_k"] for row in records) if records else 0.0,
        "recall_at_k_mean": statistics.mean(row["recall_at_k"] for row in records) if records else 0.0,
        "precision_at_k_mean": statistics.mean(row["precision_at_k"] for row in records) if records else 0.0,
        "mrr_mean": statistics.mean(row["mrr"] for row in records) if records else 0.0,
        "forbidden_total": sum(row["forbidden_count"] for row in records),
        "route_overlap_at_k_mean": statistics.mean(row["route_overlap_at_k"] for row in records) if records else 0.0,
        "context_expected_coverage_mean": statistics.mean(row["context_expected_coverage"] for row in records) if records else 0.0,
        "by_category": by_category,
        "by_task_type": by_task_type,
        "failures": [
            {
                "id": row["id"],
                "category": row["category"],
                "task_type": row["task_type"],
                "query": row["query"],
                "missed_expected": row["missed_expected"],
                "forbidden_hits": row["forbidden_hits"],
                "top_labels": [hit["label"] for hit in row["retrieved"][:5]],
            }
            for row in records
            if not row["passed"]
        ],
    }


def summarize_latency(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        groups[(str(row["operation"]), str(row["task_type"]))].append(float(row["latency_ms"]))
    return {
        f"{operation}:{task_type}": {
            "count": len(values),
            "p50_ms": statistics.median(values),
            "p95_ms": percentile(values, 95),
            "max_ms": max(values),
        }
        for (operation, task_type), values in sorted(groups.items())
    }


def run_codex_trials(output_dir: Path, max_tasks: int, timeout_s: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    codex_path = subprocess.run(["/bin/zsh", "-lc", "command -v codex"], capture_output=True, text=True).stdout.strip()
    if not codex_path:
        return [{"id": "codex_unavailable", "passed": False, "error": "codex CLI not found"}]

    task_dir = output_dir / "raw" / "codex_answers"
    task_dir.mkdir(parents=True, exist_ok=True)
    for task in CODEX_TASKS[:max_tasks]:
        pack, markdown = build_context_pack(task_type=task["task_type"], query=task["query"], write=False)
        prompt = (
            "You are being evaluated as an OpenScience RAG answerer.\n"
            "Use only the supplied context. Do not run commands. Be concise.\n"
            "Separate Observation, Inference, and Uncertainty. Include cited graph node IDs or file paths when available.\n\n"
            f"Question: {task['query']}\n\n"
            "<context>\n"
            f"{markdown[:18000]}\n"
            "</context>\n"
        )
        answer_path = task_dir / f"{task['id']}.answer.txt"
        stdout_path = task_dir / f"{task['id']}.stdout.txt"
        stderr_path = task_dir / f"{task['id']}.stderr.txt"
        cmd = [
            "codex",
            "-a",
            "never",
            "exec",
            "-C",
            str(PACKAGE_ROOT),
            "-s",
            "read-only",
            "--ephemeral",
            "-o",
            str(answer_path),
            prompt,
        ]
        start = time.perf_counter()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, cwd=PACKAGE_ROOT)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            stdout_path.write_text(proc.stdout, encoding="utf-8")
            stderr_path.write_text(proc.stderr, encoding="utf-8")
            answer = answer_path.read_text(encoding="utf-8", errors="replace") if answer_path.exists() else proc.stdout
            expected = tuple(task.get("expected_terms", ()))
            forbidden = tuple(task.get("forbidden_terms", ()))
            matched = match_fragments(answer, expected)
            forbidden_matches = match_fragments(answer, forbidden)
            citation_like = len(re.findall(r"(claim:|paper:|project:|evidence:|graph/|knowledge/|context/)", answer))
            records.append(
                {
                    "id": task["id"],
                    "task_type": task["task_type"],
                    "query": task["query"],
                    "returncode": proc.returncode,
                    "latency_ms": elapsed_ms,
                    "answer_chars": len(answer),
                    "expected_term_coverage": len(matched) / len(expected) if expected else 1.0,
                    "matched_expected_terms": matched,
                    "forbidden_matches": forbidden_matches,
                    "citation_like_count": citation_like,
                    "context_chars": pack.metrics["chars"],
                    "context_items": pack.metrics["item_count"],
                    "answer_path": str(answer_path.relative_to(output_dir)),
                    "stdout_path": str(stdout_path.relative_to(output_dir)),
                    "stderr_path": str(stderr_path.relative_to(output_dir)),
                    "passed": proc.returncode == 0 and len(matched) == len(expected) and not forbidden_matches and citation_like > 0,
                }
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            stdout_path.write_text(exc.stdout or "", encoding="utf-8")
            stderr_path.write_text(exc.stderr or "", encoding="utf-8")
            records.append(
                {
                    "id": task["id"],
                    "task_type": task["task_type"],
                    "query": task["query"],
                    "returncode": None,
                    "latency_ms": elapsed_ms,
                    "passed": False,
                    "error": f"timeout after {timeout_s}s",
                    "answer_path": str(answer_path.relative_to(output_dir)),
                }
            )
    return records


def plot_bar(path: Path, labels: list[str], values: list[float], title: str, ylabel: str, ylim: tuple[float, float] | None = None) -> None:
    if plt is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(7, 0.55 * len(labels)), 4.2))
    ax.bar(labels, values, color="#3969ac")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def make_plots(output_dir: Path, existing_summary: dict[str, Any], stress_records: list[dict[str, Any]], context_records: list[dict[str, Any]], latency_rows: list[dict[str, Any]], graph_stats: dict[str, Any], codex_records: list[dict[str, Any]]) -> None:
    if plt is None:
        return
    plots = output_dir / "plots"
    suite_labels = sorted(existing_summary.get("suites", {}))
    suite_pass = [
        existing_summary["suites"][suite]["passed"] / existing_summary["suites"][suite]["tasks"]
        for suite in suite_labels
    ]
    plot_bar(plots / "existing_eval_pass_rate.png", suite_labels, suite_pass, "Existing deterministic eval pass rate", "pass rate", (0, 1.05))

    cat_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in stress_records:
        cat_groups[row["category"]].append(row)
    cat_labels = sorted(cat_groups)
    cat_pass = [sum(1 for row in cat_groups[label] if row["passed"]) / len(cat_groups[label]) for label in cat_labels]
    plot_bar(plots / "stress_pass_rate_by_category.png", cat_labels, cat_pass, "Stress retrieval pass rate by category", "pass rate", (0, 1.05))

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for category, rows in sorted(cat_groups.items()):
        ax.scatter(
            [row["retrieval_latency_ms"] for row in rows],
            [row["mrr"] for row in rows],
            label=category,
            s=42,
            alpha=0.8,
        )
    ax.set_xlabel("retrieval latency (ms)")
    ax.set_ylabel("MRR")
    ax.set_title("Stress task MRR vs retrieval latency")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(plots / "stress_mrr_vs_latency.png", dpi=180)
    plt.close(fig)

    node_counts = graph_stats.get("node_type_counts", {})
    plot_bar(
        plots / "graph_node_type_counts.png",
        list(node_counts.keys()),
        [float(value) for value in node_counts.values()],
        "Fact graph node composition",
        "nodes",
    )
    confidence_counts = graph_stats.get("node_confidence_counts", {})
    plot_bar(
        plots / "graph_confidence_counts.png",
        list(confidence_counts.keys()),
        [float(value) for value in confidence_counts.values()],
        "Fact graph node confidence",
        "nodes",
    )

    context_by_budget: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in context_records:
        context_by_budget[int(row["budget"])].append(row)
    budgets = sorted(context_by_budget)
    fig, ax1 = plt.subplots(figsize=(7.2, 4.2))
    chars = [statistics.mean(row["chars"] for row in context_by_budget[budget]) for budget in budgets]
    coverage = [statistics.mean(row["expected_coverage"] for row in context_by_budget[budget]) for budget in budgets]
    ax1.plot(budgets, chars, marker="o", color="#3969ac", label="mean chars")
    ax1.set_xlabel("char budget")
    ax1.set_ylabel("mean packed chars")
    ax1.grid(alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(budgets, coverage, marker="s", color="#cc503e", label="expected coverage")
    ax2.set_ylabel("mean expected term coverage")
    ax2.set_ylim(0, 1.05)
    ax1.set_title("Context budget sensitivity")
    fig.tight_layout()
    fig.savefig(plots / "context_budget_sensitivity.png", dpi=180)
    plt.close(fig)

    latency_groups: dict[str, list[float]] = defaultdict(list)
    for row in latency_rows:
        latency_groups[f"{row['operation']}:{row['task_type']}"].append(float(row["latency_ms"]))
    fig, ax = plt.subplots(figsize=(max(8, 0.45 * len(latency_groups)), 4.8))
    labels = sorted(latency_groups)
    ax.boxplot([latency_groups[label] for label in labels], tick_labels=labels, showfliers=False)
    ax.set_ylabel("latency (ms)")
    ax.set_title("Latency distributions")
    ax.tick_params(axis="x", rotation=35, labelsize=7)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(plots / "latency_distributions.png", dpi=180)
    plt.close(fig)

    if codex_records:
        labels = [row["id"] for row in codex_records]
        values = [float(row.get("latency_ms", 0.0)) / 1000.0 for row in codex_records]
        plot_bar(plots / "codex_answer_latency_seconds.png", labels, values, "Codex answer trial latency", "seconds")


def write_report(output_dir: Path, existing_summary: dict[str, Any], stress_summary: dict[str, Any], context_summary: dict[str, Any], latency_summary: dict[str, Any], graph_stats: dict[str, Any], codex_records: list[dict[str, Any]], test_results: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.extend(
        [
            "# RAG / Knowledge Net Audit",
            "",
            f"Generated: {datetime.now().isoformat(timespec='seconds')}",
            "",
            "## Executive Summary",
            f"- Existing deterministic evals: {existing_summary['passed']}/{existing_summary['tasks']} passed, p50 latency {existing_summary['latency_ms']['p50']} ms.",
            f"- Stress retrieval/context probes: {stress_summary['passed']}/{stress_summary['tasks']} passed; mean MRR {stress_summary['mrr_mean']:.3f}; mean route overlap {stress_summary['route_overlap_at_k_mean']:.3f}.",
            f"- Graph structure: {graph_stats['node_count']} nodes, {graph_stats['edge_count']} edges, {graph_stats['degree']['isolated_count']} isolated nodes.",
            f"- Pytest: {test_results.get('summary', 'not run')}.",
        ]
    )
    if codex_records:
        passed = sum(1 for row in codex_records if row.get("passed"))
        lines.append(f"- Codex answer trials: {passed}/{len(codex_records)} passed simple grounding checks.")
    else:
        lines.append("- Codex answer trials: not run.")

    lines.extend(
        [
            "",
            "## Critical Findings",
            "- Current tracked diagnostics are mostly smoke tests. They prove the infrastructure still runs, but not that the system answers hard lab questions correctly.",
            "- Retrieval benchmarks are keyword-friendly and share benchmark definitions across graph and lexical baseline comparisons, so 8/8 pass is not strong evidence of generalization.",
            "- Context packing uses a separate graph-search implementation from `fact_graph.task_aware_search`; the audit records `route_overlap_at_k` because standalone retrieval can pass while packed context differs.",
            "- Provenance is measured mostly as presence/absence, not whether a source truly supports the claim or is cited correctly in a final answer.",
            "- End-to-end answer quality remains the largest gap: the deterministic suite does not yet judge final responses for factuality, uncertainty, citation precision, or unsupported synthesis.",
            "",
            "## Existing Eval Baseline",
        ]
    )
    for suite, stats in sorted(existing_summary.get("suites", {}).items()):
        lines.append(f"- `{suite}`: {stats['passed']}/{stats['tasks']} passed")
    lines.extend(["", "## Stress Suite By Category"])
    for category, stats in sorted(stress_summary["by_category"].items()):
        lines.append(
            f"- `{category}`: {stats['passed']}/{stats['tasks']} passed; "
            f"MRR {stats['mrr_mean']:.3f}; context coverage {stats['context_expected_coverage_mean']:.3f}; "
            f"route overlap {stats['route_overlap_at_k_mean']:.3f}"
        )
    if stress_summary["failures"]:
        lines.extend(["", "## Stress Failures"])
        for failure in stress_summary["failures"][:20]:
            lines.append(f"- `{failure['id']}` ({failure['task_type']}): missed {failure['missed_expected']}; top={failure['top_labels'][:3]}")
    else:
        lines.extend(["", "## Stress Failures", "- none"])

    lines.extend(["", "## Context Budget Summary"])
    for budget, stats in sorted(context_summary.items()):
        lines.append(
            f"- `{budget}` chars: mean packed {stats['mean_chars']:.0f}, "
            f"mean expected coverage {stats['mean_expected_coverage']:.3f}, mean excluded {stats['mean_excluded']:.1f}"
        )

    lines.extend(["", "## Latency Summary"])
    for key, stats in sorted(latency_summary.items()):
        lines.append(f"- `{key}`: p50 {stats['p50_ms']:.2f} ms, p95 {stats['p95_ms']:.2f} ms, max {stats['max_ms']:.2f} ms")

    lines.extend(["", "## Graph Structure Notes"])
    lines.append(f"- Node types: {graph_stats['node_type_counts']}")
    lines.append(f"- Node confidence: {graph_stats['node_confidence_counts']}")
    lines.append(f"- Degree p95/max: {graph_stats['degree']['p95']} / {graph_stats['degree']['max']}")
    if graph_stats["degree"]["isolated_sample"]:
        lines.append(f"- Isolated node sample: {graph_stats['degree']['isolated_sample'][:10]}")

    if codex_records:
        lines.extend(["", "## Codex Answer Trials"])
        for row in codex_records:
            lines.append(
                f"- `{row['id']}`: passed={row.get('passed')} latency={row.get('latency_ms', 0) / 1000.0:.1f}s "
                f"coverage={row.get('expected_term_coverage')} citations={row.get('citation_like_count')} answer={row.get('answer_path')}"
            )

    lines.extend(
        [
            "",
            "## Artifacts",
            "- Raw JSON/JSONL/CSV: `raw/`",
            "- Plots: `plots/`",
            "- This report: `reports/findings.md`",
            "",
            "## Recommended Next Tests",
            "- Add answer-level gold tasks with required supporting nodes, required source files, forbidden distractors, and uncertainty expectations.",
            "- Add graded relevance labels and compute nDCG, not only substring hit/MRR.",
            "- Merge or explicitly cross-check the graph retrieval implementation used by context packs against `fact_graph.task_aware_search`.",
            "- Add hard-negative and low-evidence tasks to CI gates so false confidence becomes visible.",
            "- Validate citation support, not just citation presence, for every answer-level benchmark.",
        ]
    )
    report_path = output_dir / "reports" / "findings.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# RAG / Knowledge Net Audit\n\n"
        "Start with `reports/findings.md`. Raw data lives in `raw/`; plots live in `plots/`.\n",
        encoding="utf-8",
    )


def run_pytest() -> dict[str, Any]:
    candidates = [
        PACKAGE_ROOT / ".venv-science" / "bin" / "python",
        PACKAGE_ROOT / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    for python in candidates:
        if not python.exists():
            continue
        start = time.perf_counter()
        proc = subprocess.run(
            [str(python), "-m", "pytest", "-q"],
            cwd=PACKAGE_ROOT,
            capture_output=True,
            text=True,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if "No module named pytest" in proc.stderr or "No module named pytest" in proc.stdout:
            continue
        summary = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else f"returncode {proc.returncode}"
        return {
            "python": str(python),
            "returncode": proc.returncode,
            "latency_ms": elapsed_ms,
            "summary": summary,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    return {"returncode": None, "summary": "pytest unavailable", "stdout": "", "stderr": ""}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit RAG/fact-graph diagnostics and write a findings folder.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--latency-repeats", type=int, default=30)
    parser.add_argument("--context-budgets", type=int, nargs="+", default=[4000, 8000, 12000, 18000])
    parser.add_argument("--run-codex", action="store_true", help="Run optional Codex answer-generation trials.")
    parser.add_argument("--codex-max", type=int, default=4)
    parser.add_argument("--codex-timeout-s", type=int, default=240)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = args.output_dir or (PACKAGE_ROOT / "outputs" / f"rag_audit_{stamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)
    (output_dir / "plots").mkdir(exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "package_root": str(PACKAGE_ROOT),
        "python": sys.version,
        "platform": platform.platform(),
        "args": vars(args) | {"output_dir": str(output_dir)},
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=PACKAGE_ROOT, capture_output=True, text=True).stdout.strip(),
        "git_status_short": subprocess.run(["git", "status", "--short"], cwd=PACKAGE_ROOT, capture_output=True, text=True).stdout,
    }
    write_json(output_dir / "raw" / "manifest.json", manifest)

    existing_records, existing_summary = run_existing_evals()
    write_jsonl(output_dir / "raw" / "existing_eval_records.jsonl", existing_records)
    write_json(output_dir / "raw" / "existing_eval_summary.json", existing_summary)

    test_results = run_pytest()
    write_json(output_dir / "raw" / "pytest_result.json", {k: v for k, v in test_results.items() if k not in {"stdout", "stderr"}})
    (output_dir / "raw" / "pytest_stdout.txt").write_text(test_results.get("stdout", ""), encoding="utf-8")
    (output_dir / "raw" / "pytest_stderr.txt").write_text(test_results.get("stderr", ""), encoding="utf-8")

    stats = graph_structure()
    write_json(output_dir / "raw" / "graph_structure.json", stats)

    stress_records = run_stress_suite(top_k=args.top_k)
    stress_summary = summarize_stress(stress_records)
    write_jsonl(output_dir / "raw" / "stress_retrieval_results.jsonl", stress_records)
    write_json(output_dir / "raw" / "stress_summary.json", stress_summary)
    write_csv(output_dir / "raw" / "stress_retrieval_results.csv", stress_records)

    context_records = run_context_probes(args.context_budgets)
    write_jsonl(output_dir / "raw" / "context_probe_results.jsonl", context_records)
    write_csv(output_dir / "raw" / "context_probe_results.csv", context_records)
    context_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in context_records:
        context_groups[int(row["budget"])].append(row)
    context_summary = {
        str(budget): {
            "tasks": len(rows),
            "mean_chars": statistics.mean(row["chars"] for row in rows),
            "mean_items": statistics.mean(row["item_count"] for row in rows),
            "mean_excluded": statistics.mean(row["excluded_count"] for row in rows),
            "mean_expected_coverage": statistics.mean(row["expected_coverage"] for row in rows),
            "median_latency_ms": statistics.median(row["latency_ms"] for row in rows),
        }
        for budget, rows in sorted(context_groups.items())
    }
    write_json(output_dir / "raw" / "context_summary.json", context_summary)

    latency_rows = run_latency_samples(args.latency_repeats, top_k=args.top_k)
    latency_summary = summarize_latency(latency_rows)
    write_csv(output_dir / "raw" / "latency_samples.csv", latency_rows)
    write_json(output_dir / "raw" / "latency_summary.json", latency_summary)

    codex_records: list[dict[str, Any]] = []
    if args.run_codex:
        codex_records = run_codex_trials(output_dir, max_tasks=args.codex_max, timeout_s=args.codex_timeout_s)
        write_jsonl(output_dir / "raw" / "codex_answer_trials.jsonl", codex_records)
        write_csv(output_dir / "raw" / "codex_answer_trials.csv", codex_records)

    make_plots(output_dir, existing_summary, stress_records, context_records, latency_rows, stats, codex_records)
    write_report(output_dir, existing_summary, stress_summary, context_summary, latency_summary, stats, codex_records, test_results)

    print(f"audit output: {output_dir}")
    print(f"existing evals: {existing_summary['passed']}/{existing_summary['tasks']} passed")
    print(f"stress suite: {stress_summary['passed']}/{stress_summary['tasks']} passed")
    if codex_records:
        print(f"codex trials: {sum(1 for row in codex_records if row.get('passed'))}/{len(codex_records)} passed")
    print(f"report: {output_dir / 'reports' / 'findings.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
