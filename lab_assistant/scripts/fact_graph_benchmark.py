#!/usr/bin/env python3
"""Evaluate whether the OpenScience fact graph is useful on representative queries."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from fact_graph import load_graph, search_nodes
from fact_graph_common import REPO_ROOT


BENCHMARKS = [
    {
        "query": "fractional Chern optical control",
        "expected": [
            "optical control of integer and fractional chern insulators",
            "signatures of fractional charges via anyon",
            "signatures of fractional quantum anomalous hall states in twisted mote2",
        ],
    },
    {
        "query": "second moire band ferromagnetism",
        "expected": [
            "second moiré band",
            "higher flat band",
            "ferromagnetic phase in the second moiré band",
        ],
    },
    {
        "query": "magnetic proximity wse2 cri3",
        "expected": [
            "magnetic proximity effect in wse2/cri3",
            "valley manipulation by optically tuning the magnetic proximity effect in wse2/cri3",
        ],
    },
    {
        "query": "gate control bilayer cri3 magnetism",
        "expected": [
            "electrical control of 2d magnetism in bilayer cri3",
            "electrical control of 2d magnetism",
        ],
    },
    {
        "query": "moire exciton optical signatures",
        "expected": [
            "moire excitons",
            "signatures of moiré-trapped valley excitons",
            "evidence for moiré excitons",
            "observation of moiré excitons",
        ],
    },
    {
        "query": "edge conduction monolayer wte2",
        "expected": [
            "edge conduction in monolayer wte2",
            "imaging quantum spin hall edges in monolayer wte2",
        ],
    },
    {
        "query": "interlayer exciton mose2 wse2",
        "expected": [
            "observation of long-lived interlayer excitons in monolayer mose2-wse2 heterostructures",
            "directional interlayer spin-valley transfer in 2d heterostructures",
        ],
    },
    {
        "query": "fractional Chern insulator local probe bulk edge",
        "expected": [
            "local probe of bulk and edge states in a fractional chern insulator",
        ],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small usefulness benchmark on the fact graph.")
    parser.add_argument(
        "--staging",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "graph" / "staging" / "xu_group_publications.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "graph" / "views" / "performance_report.md",
    )
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def normalize(value: str) -> str:
    value = value.lower()
    value = value.replace("–", "-").replace("—", "-").replace("−", "-").replace("₂", "2")
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return " ".join(value.split())


def graph_stats(staging_path: Path) -> dict:
    nodes, edges = load_graph()
    node_list = list(nodes.values())
    paper_nodes = [node for node in node_list if node.get("type") == "Paper"]
    claim_nodes = [node for node in node_list if node.get("type") == "Claim"]
    official_nodes = [
        node
        for node in paper_nodes
        if any(item.get("method") == "official xu group publications ingest" for item in node.get("provenance", []))
    ]
    curated_nodes = [
        node
        for node in paper_nodes
        if any(item.get("method") == "deterministic paper-shelf ingest" for item in node.get("provenance", []))
    ]
    topic_counts: Counter[str] = Counter()
    for node in official_nodes:
        topic_counts.update(node.get("metadata", {}).get("topic_tags", []))

    official_entry_count = 0
    if staging_path.exists():
        official_entry_count = sum(1 for line in staging_path.read_text(encoding="utf-8").splitlines() if line.strip())

    return {
        "nodes": len(node_list),
        "edges": len(edges),
        "papers": len(paper_nodes),
        "claims": len(claim_nodes),
        "official_papers": len(official_nodes),
        "official_entries": official_entry_count,
        "curated_papers": len(curated_nodes),
        "topic_counts": topic_counts,
    }


def run_benchmarks(limit: int) -> list[dict]:
    results = []
    for benchmark in BENCHMARKS:
        hits = search_nodes(benchmark["query"], limit=limit)
        top_labels = [normalize(item[2].get("label", "")) for item in hits]
        expected_terms = [normalize(item) for item in benchmark["expected"]]
        passed = any(any(expected in label for expected in expected_terms) for label in top_labels)
        results.append(
            {
                "query": benchmark["query"],
                "passed": passed,
                "hits": [
                    {
                        "id": node_id,
                        "type": node["type"],
                        "score": score,
                        "label": node["label"],
                    }
                    for score, node_id, node, _touching in hits
                ],
            }
        )
    return results


def write_report(path: Path, stats: dict, results: list[dict]) -> None:
    passed = sum(1 for item in results if item["passed"])
    lines = [
        "# Fact Graph Performance Report",
        "",
        "Purpose:",
        "- Quick usefulness audit after expanding the graph.",
        "- Focus on coverage plus whether representative scientific queries pull up the right nodes near the top.",
        "",
        "## Coverage",
        f"- Nodes: {stats['nodes']}",
        f"- Edges: {stats['edges']}",
        f"- Paper nodes: {stats['papers']}",
        f"- Claim nodes: {stats['claims']}",
        f"- Official Xu publication entries parsed: {stats['official_entries']}",
        f"- Paper nodes with official Xu publication provenance: {stats['official_papers']}",
        f"- Curated paper nodes from `knowledge/papers/`: {stats['curated_papers']}",
        "",
        "## Official Topic Coverage",
    ]
    for topic, count in sorted(stats["topic_counts"].items()):
        lines.append(f"- `{topic}`: {count}")
    lines.extend(
        [
            "",
            "## Retrieval Benchmarks",
            f"- Passed: {passed}/{len(results)}",
            "",
        ]
    )

    for result in results:
        status = "PASS" if result["passed"] else "MISS"
        lines.append(f"### {status}: {result['query']}")
        for hit in result["hits"]:
            lines.append(f"- `{hit['type']}` score={hit['score']}: {hit['label']}")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "- Broad paper coverage is useful only if representative science queries pull up the right papers or claim nodes near the top.",
            "- Official-publication ingest mainly improves breadth; the curated paper shelves remain the main source of medium-confidence scientific takeaways.",
            "- Misses usually indicate either a missing curated paper shelf, weak concept links, or overly generic search vocabulary.",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    stats = graph_stats(args.staging)
    results = run_benchmarks(limit=args.limit)
    write_report(args.output, stats, results)
    passed = sum(1 for item in results if item["passed"])
    print(f"benchmarks: {passed}/{len(results)} passed")
    print(f"report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
