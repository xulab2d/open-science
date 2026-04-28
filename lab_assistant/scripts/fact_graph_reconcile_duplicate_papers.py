#!/usr/bin/env python3
"""Merge exact-normalized duplicate paper nodes into canonical records."""

from __future__ import annotations

import json
import re
from collections import defaultdict

from fact_graph_common import EDGES_PATH, NODES_PATH, confidence_rank, load_jsonl, merge_record, write_jsonl


def normalize_title(value: str) -> str:
    value = value.lower().replace("–", "-").replace("—", "-").replace("−", "-").replace("₂", "2")
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return " ".join(value.split())


def canonical_score(node: dict, touching_edges: int) -> tuple[int, int, int, int, str]:
    methods = " ".join(item.get("method", "") for item in node.get("provenance", []))
    return (
        0 if node["id"].startswith("paper:arxiv_") else 1,
        confidence_rank(node.get("confidence", "low")),
        1 if "paper-shelf" in methods or "knowledge/papers" in methods else 0,
        touching_edges,
        node["id"],
    )


def main() -> int:
    nodes = load_jsonl(NODES_PATH)
    edges = load_jsonl(EDGES_PATH)
    by_id = {node["id"]: node for node in nodes}

    by_norm: dict[str, list[dict]] = defaultdict(list)
    for node in nodes:
        if node.get("type") == "Paper":
            by_norm[normalize_title(str(node.get("label", "")))].append(node)

    redirects: dict[str, str] = {}
    for group in by_norm.values():
        if len(group) < 2:
            continue
        scored = sorted(
            group,
            key=lambda node: canonical_score(
                node,
                sum(1 for edge in edges if edge["source"] == node["id"] or edge["target"] == node["id"]),
            ),
            reverse=True,
        )
        canonical = scored[0]
        for duplicate in scored[1:]:
            redirects[duplicate["id"]] = canonical["id"]
            by_id[canonical["id"]] = merge_record(
                by_id[canonical["id"]],
                {
                    **duplicate,
                    "id": canonical["id"],
                    "aliases": duplicate.get("aliases", []) + [duplicate.get("label", "")],
                },
            )

    if not redirects:
        print("no duplicate papers to reconcile")
        return 0

    merged_edges: dict[str, dict] = {}
    for edge in edges:
        source = redirects.get(edge["source"], edge["source"])
        target = redirects.get(edge["target"], edge["target"])
        key = json.dumps([source, target, edge["relation"], edge["claim"]], ensure_ascii=False)
        candidate = dict(edge)
        candidate["source"] = source
        candidate["target"] = target
        if key in merged_edges:
            merged_edges[key] = merge_record(merged_edges[key], candidate)
        else:
            merged_edges[key] = candidate

    kept_nodes = [node for node_id, node in sorted(by_id.items()) if node_id not in redirects]
    kept_edges = list(merged_edges.values())
    write_jsonl(NODES_PATH, kept_nodes)
    write_jsonl(EDGES_PATH, sorted(kept_edges, key=lambda item: item["id"]))

    print(f"merged duplicate paper nodes: {len(redirects)}")
    for old_id, new_id in sorted(redirects.items()):
        print(f"- {old_id} -> {new_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
