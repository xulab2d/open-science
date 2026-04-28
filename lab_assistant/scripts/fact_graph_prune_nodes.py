#!/usr/bin/env python3
"""Remove selected fact-graph nodes and their attached edges."""

from __future__ import annotations

import argparse

from fact_graph_common import EDGES_PATH, NODES_PATH, load_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prune selected nodes from the fact graph.")
    parser.add_argument("--node-id", action="append", required=True, dest="node_ids")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    doomed = set(args.node_ids)

    nodes = load_jsonl(NODES_PATH)
    kept_nodes = [node for node in nodes if node["id"] not in doomed]
    removed_nodes = len(nodes) - len(kept_nodes)

    edges = load_jsonl(EDGES_PATH)
    kept_edges = [edge for edge in edges if edge["source"] not in doomed and edge["target"] not in doomed]
    removed_edges = len(edges) - len(kept_edges)

    write_jsonl(NODES_PATH, kept_nodes)
    write_jsonl(EDGES_PATH, kept_edges)

    print(f"removed_nodes: {removed_nodes}")
    print(f"removed_edges: {removed_edges}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
