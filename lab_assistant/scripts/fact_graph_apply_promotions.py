#!/usr/bin/env python3
"""Apply curated fact-graph promotions from JSON source files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fact_graph_common import EDGES_PATH, NODES_PATH, REPO_ROOT, load_jsonl, write_jsonl


def unique_provenance(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def merge_record(existing: dict[str, Any] | None, incoming: dict[str, Any]) -> dict[str, Any]:
    if existing is None:
        return incoming
    merged = dict(existing)
    for key, value in incoming.items():
        if key == "provenance":
            merged[key] = unique_provenance(merged.get(key, []) + value)
        elif key == "metadata" and isinstance(value, dict):
            old = merged.get(key, {})
            merged[key] = {**old, **value} if isinstance(old, dict) else value
        else:
            merged[key] = value
    return merged


def upsert(path: Path, incoming: list[dict[str, Any]]) -> tuple[int, int]:
    records = load_jsonl(path)
    by_id = {record["id"]: record for record in records}
    added = 0
    updated = 0
    for record in incoming:
        record_id = record["id"]
        if record_id in by_id:
            by_id[record_id] = merge_record(by_id[record_id], record)
            updated += 1
        else:
            by_id[record_id] = record
            added += 1
    write_jsonl(path, sorted(by_id.values(), key=lambda item: item["id"]))
    return added, updated


def apply_updates(path: Path, updates: list[dict[str, Any]]) -> int:
    if not updates:
        return 0
    records = load_jsonl(path)
    by_id = {record["id"]: record for record in records}
    updated = 0
    for update in updates:
        record_id = update["id"]
        if record_id not in by_id:
            raise SystemExit(f"cannot update missing node: {record_id}")
        by_id[record_id] = merge_record(by_id[record_id], update)
        updated += 1
    write_jsonl(path, sorted(by_id.values(), key=lambda item: item["id"]))
    return updated


def load_promotions(paths: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        nodes.extend(data.get("nodes", []))
        edges.extend(data.get("edges", []))
        updates.extend(data.get("node_updates", []))
    return nodes, edges, updates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply curated fact-graph promotions.")
    parser.add_argument(
        "--promotions-dir",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "graph" / "sources" / "promotions",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(args.promotions_dir.glob("*.json"))
    nodes, edges, updates = load_promotions(paths)
    updated_nodes = apply_updates(NODES_PATH, updates)
    node_added, node_updated = upsert(NODES_PATH, nodes)
    edge_added, edge_updated = upsert(EDGES_PATH, edges)
    print(f"promotion files: {len(paths)}")
    print(f"node updates: {updated_nodes}")
    print(f"nodes: +{node_added}, updated={node_updated}")
    print(f"edges: +{edge_added}, updated={edge_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
