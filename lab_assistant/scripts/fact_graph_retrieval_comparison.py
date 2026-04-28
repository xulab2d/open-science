#!/usr/bin/env python3
"""Compare fact-graph paper retrieval against a simpler non-graph baseline."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from fact_graph import load_graph, rank_nodes
from fact_graph_benchmark import BENCHMARKS, normalize
from fact_graph_ingest_paper_shelves import parse_paper_shelf
from fact_graph_common import REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare graph retrieval against a simpler paper-search baseline.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--graph-limit", type=int, default=30)
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "graph" / "views" / "retrieval_comparison.md",
    )
    parser.add_argument(
        "--papers-dir",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "knowledge" / "papers",
    )
    parser.add_argument(
        "--staging",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "graph" / "staging" / "xu_group_publications.jsonl",
    )
    return parser.parse_args()


def tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[A-Za-z0-9_ν]+", text.lower()) if len(token) > 1}


def load_baseline_records(papers_dir: Path, staging_path: Path) -> list[dict]:
    by_title: dict[str, dict] = {}

    for path in sorted(p for p in papers_dir.glob("*.md") if p.name != "README.md"):
        for paper in parse_paper_shelf(path):
            title = paper["title"]
            key = normalize(title)
            summary = " ".join(
                part
                for part in [
                    paper.get("result to remember", ""),
                    paper.get("specific detail", ""),
                    paper.get("use for", ""),
                ]
                if part
            )
            record = {
                "title": title,
                "summary": summary,
                "aliases": [paper.get("citation", "")],
                "source": str(path.relative_to(REPO_ROOT)),
                "kind": "curated",
            }
            old = by_title.get(key)
            if old is None or len(summary) > len(old.get("summary", "")):
                by_title[key] = record

    if staging_path.exists():
        for line in staging_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            title = entry["title"]
            key = normalize(title)
            record = {
                "title": title,
                "summary": f"{entry.get('raw_citation', '')} Topics: {', '.join(entry.get('topic_tags', []))}",
                "aliases": [entry.get("raw_citation", "")],
                "source": str(staging_path.relative_to(REPO_ROOT)),
                "kind": "official",
            }
            if key not in by_title:
                by_title[key] = record

    return sorted(by_title.values(), key=lambda item: normalize(item["title"]))


def baseline_search(records: list[dict], query: str, limit: int) -> list[dict]:
    qtokens = tokenize(query)
    lower_query = query.lower()
    scored: list[tuple[int, dict]] = []

    for record in records:
        title = record["title"]
        summary = record["summary"]
        aliases = " ".join(record.get("aliases", []))
        title_tokens = tokenize(title)
        summary_tokens = tokenize(summary)
        alias_tokens = tokenize(aliases)
        score = 0
        score += 4 * len(qtokens & title_tokens)
        score += 2 * len(qtokens & alias_tokens)
        score += 1 * len(qtokens & summary_tokens)
        if lower_query in title.lower():
            score += 8
        elif lower_query in aliases.lower():
            score += 5
        elif lower_query in summary.lower():
            score += 3
        if record.get("kind") == "curated":
            score += 1
        if score:
            scored.append((score, record))

    scored.sort(key=lambda item: (-item[0], normalize(item[1]["title"])))
    return [record for _score, record in scored[:limit]]


def graph_paper_search(
    query: str,
    nodes: dict[str, dict],
    edges: list[dict],
    paper_limit: int,
    graph_limit: int,
) -> list[dict]:
    hits = rank_nodes(query, nodes, edges, limit=graph_limit, node_types={"Paper"})
    return [
        {"title": node["label"], "summary": node.get("summary", ""), "score": score}
        for score, _node_id, node, _touching in hits[:paper_limit]
    ]


def first_match_rank(records: list[dict], expected_terms: list[str]) -> int | None:
    for index, record in enumerate(records, start=1):
        title = normalize(record["title"])
        if any(term in title for term in expected_terms):
            return index
    return None


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def compare(records: list[dict], top_k: int, graph_limit: int, repeats: int) -> dict:
    nodes, edges = load_graph()
    per_query = []
    graph_times: list[float] = []
    baseline_times: list[float] = []

    for item in BENCHMARKS:
        query = item["query"]
        expected_terms = [normalize(term) for term in item["expected"]]

        t0 = time.perf_counter()
        graph_hits = graph_paper_search(query, nodes, edges, paper_limit=top_k, graph_limit=graph_limit)
        graph_times.append(time.perf_counter() - t0)

        t1 = time.perf_counter()
        baseline_hits = baseline_search(records, query, limit=top_k)
        baseline_times.append(time.perf_counter() - t1)

        graph_rank = first_match_rank(graph_hits, expected_terms)
        baseline_rank = first_match_rank(baseline_hits, expected_terms)

        per_query.append(
            {
                "query": query,
                "graph_hits": graph_hits,
                "baseline_hits": baseline_hits,
                "graph_rank": graph_rank,
                "baseline_rank": baseline_rank,
            }
        )

    # latency benchmark with repeated runs
    graph_repeat_times: list[float] = []
    baseline_repeat_times: list[float] = []
    for _ in range(repeats):
        for item in BENCHMARKS:
            query = item["query"]
            start = time.perf_counter()
            graph_paper_search(query, nodes, edges, paper_limit=top_k, graph_limit=graph_limit)
            graph_repeat_times.append(time.perf_counter() - start)

            start = time.perf_counter()
            baseline_search(records, query, limit=top_k)
            baseline_repeat_times.append(time.perf_counter() - start)

    graph_passes = sum(1 for row in per_query if row["graph_rank"] is not None)
    baseline_passes = sum(1 for row in per_query if row["baseline_rank"] is not None)
    graph_avg_rank = sum(row["graph_rank"] for row in per_query if row["graph_rank"] is not None) / max(graph_passes, 1)
    baseline_avg_rank = sum(row["baseline_rank"] for row in per_query if row["baseline_rank"] is not None) / max(baseline_passes, 1)

    return {
        "queries": per_query,
        "graph_passes": graph_passes,
        "baseline_passes": baseline_passes,
        "graph_avg_rank": graph_avg_rank,
        "baseline_avg_rank": baseline_avg_rank,
        "graph_median_ms": median(graph_repeat_times) * 1000.0,
        "baseline_median_ms": median(baseline_repeat_times) * 1000.0,
        "graph_single_ms": median(graph_times) * 1000.0,
        "baseline_single_ms": median(baseline_times) * 1000.0,
        "paper_records": len(records),
    }


def write_report(path: Path, result: dict, top_k: int) -> None:
    lines = [
        "# Retrieval Comparison",
        "",
        "Purpose:",
        "- Compare fact-graph paper retrieval against a simpler non-graph lexical paper search over the local knowledge corpus.",
        "- Distinguish raw lookup speed from retrieval usefulness.",
        "",
        "## Aggregate",
        f"- Benchmark queries: {len(result['queries'])}",
        f"- Baseline paper records: {result['paper_records']}",
        f"- Graph paper hit@{top_k}: {result['graph_passes']}/{len(result['queries'])}",
        f"- Baseline paper hit@{top_k}: {result['baseline_passes']}/{len(result['queries'])}",
        f"- Graph average first relevant paper rank: {result['graph_avg_rank']:.2f}",
        f"- Baseline average first relevant paper rank: {result['baseline_avg_rank']:.2f}",
        f"- Graph median lookup time: {result['graph_median_ms']:.3f} ms",
        f"- Baseline median lookup time: {result['baseline_median_ms']:.3f} ms",
        "",
        "Interpretation:",
    ]

    if result["graph_median_ms"] < result["baseline_median_ms"]:
        lines.append("- On this local corpus, graph search is also faster in raw lookup time.")
    else:
        lines.append("- On this local corpus, the graph is not faster in raw milliseconds; its advantage has to come from retrieval quality or richer context.")

    if result["graph_avg_rank"] < result["baseline_avg_rank"]:
        lines.append("- The graph surfaces relevant papers earlier on average.")
    elif result["graph_avg_rank"] > result["baseline_avg_rank"]:
        lines.append("- The simpler baseline surfaces relevant papers earlier on average.")
    else:
        lines.append("- The graph and the simpler baseline tie on average paper rank for these queries.")

    lines.append("")
    lines.append("## Per Query")
    for row in result["queries"]:
        lines.append(f"### {row['query']}")
        lines.append(f"- Graph first relevant paper rank: {row['graph_rank']}")
        lines.append(f"- Baseline first relevant paper rank: {row['baseline_rank']}")
        lines.append("- Graph top papers:")
        for hit in row["graph_hits"]:
            lines.append(f"  - {hit['title']}")
        lines.append("- Baseline top papers:")
        for hit in row["baseline_hits"]:
            lines.append(f"  - {hit['title']}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    records = load_baseline_records(args.papers_dir, args.staging)
    result = compare(records, top_k=args.top_k, graph_limit=args.graph_limit, repeats=args.repeats)
    write_report(args.output, result, top_k=args.top_k)
    print(f"graph hit@{args.top_k}: {result['graph_passes']}/{len(result['queries'])}")
    print(f"baseline hit@{args.top_k}: {result['baseline_passes']}/{len(result['queries'])}")
    print(f"graph median ms: {result['graph_median_ms']:.3f}")
    print(f"baseline median ms: {result['baseline_median_ms']:.3f}")
    print(f"report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
