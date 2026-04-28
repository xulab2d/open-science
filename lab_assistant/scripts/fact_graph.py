#!/usr/bin/env python3
"""Small JSONL fact-graph utility for OpenScience."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_DIR = REPO_ROOT / "lab_assistant" / "graph"
NODES_PATH = GRAPH_DIR / "nodes.jsonl"
EDGES_PATH = GRAPH_DIR / "edges.jsonl"
SCHEMA_PATH = GRAPH_DIR / "schema.json"
VIEWS_DIR = GRAPH_DIR / "views"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            records.append(record)
    return records


def tokenize(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[A-Za-z0-9_ν]+", text.lower()) if len(tok) > 1}


def token_bigrams(text: str) -> set[str]:
    tokens = [tok for tok in re.findall(r"[A-Za-z0-9_ν]+", text.lower()) if len(tok) > 1]
    return {f"{tokens[index]} {tokens[index + 1]}" for index in range(len(tokens) - 1)}


def node_text(node: dict[str, Any]) -> str:
    aliases = " ".join(node.get("aliases", []))
    return f"{node.get('id', '')} {node.get('type', '')} {node.get('label', '')} {aliases} {node.get('summary', '')}"


def edge_text(edge: dict[str, Any]) -> str:
    return f"{edge.get('id', '')} {edge.get('relation', '')} {edge.get('claim', '')}"


def load_graph() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    nodes = {node["id"]: node for node in load_jsonl(NODES_PATH)}
    edges = load_jsonl(EDGES_PATH)
    return nodes, edges


def confidence_score(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 0)


def score_node(query: str, qtokens: set[str], node: dict[str, Any]) -> int:
    label = str(node.get("label", ""))
    aliases = " ".join(node.get("aliases", []))
    summary = str(node.get("summary", ""))
    label_tokens = tokenize(label)
    alias_tokens = tokenize(aliases)
    summary_tokens = tokenize(summary)
    query_bigrams = token_bigrams(query)
    label_bigrams = token_bigrams(label)
    alias_bigrams = token_bigrams(aliases)
    summary_bigrams = token_bigrams(summary)

    score = 0
    score += 4 * len(qtokens & label_tokens)
    score += 2 * len(qtokens & alias_tokens)
    score += 1 * len(qtokens & summary_tokens)
    score += 4 * len(query_bigrams & label_bigrams)
    score += 2 * len(query_bigrams & alias_bigrams)
    score += 1 * len(query_bigrams & summary_bigrams)
    lower_query = query.lower()
    if lower_query in label.lower():
        score += 8
    elif lower_query in aliases.lower():
        score += 5
    elif lower_query in summary.lower():
        score += 3
    score += confidence_score(node.get("confidence", "low"))
    if node.get("id", "").startswith("paper:arxiv_"):
        score -= 1
    return score


def search_nodes(query: str, limit: int = 8, node_types: set[str] | None = None) -> list[tuple[int, str, dict[str, Any], int]]:
    nodes, edges = load_graph()
    return rank_nodes(query, nodes, edges, limit=limit, node_types=node_types)


def rank_nodes(
    query: str,
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    limit: int = 8,
    node_types: set[str] | None = None,
) -> list[tuple[int, str, dict[str, Any], int]]:
    qtokens = tokenize(query)
    scored: list[tuple[int, str, dict[str, Any], int]] = []
    for node_id, node in nodes.items():
        if node_types is not None and node.get("type") not in node_types:
            continue
        score = score_node(query, qtokens, node)
        if score:
            touching = sum(1 for edge in edges if edge["source"] == node_id or edge["target"] == node_id)
            scored.append((score, node_id, node, touching))

    scored.sort(key=lambda item: (-item[0], -item[3], item[1]))
    return scored[:limit]


def validate() -> int:
    schema = load_json(SCHEMA_PATH)
    nodes, edges = load_graph()
    errors: list[str] = []

    for node_id, node in nodes.items():
        for field in schema["node_required"]:
            if field not in node:
                errors.append(f"node {node_id}: missing {field}")
        if node.get("type") not in schema["node_types"]:
            errors.append(f"node {node_id}: invalid type {node.get('type')}")
        if node.get("confidence") not in schema["confidence_values"]:
            errors.append(f"node {node_id}: invalid confidence {node.get('confidence')}")
        if not node.get("provenance"):
            errors.append(f"node {node_id}: missing provenance")

    edge_ids: set[str] = set()
    for edge in edges:
        edge_id = edge.get("id", "<missing>")
        if edge_id in edge_ids:
            errors.append(f"edge {edge_id}: duplicate id")
        edge_ids.add(edge_id)
        for field in schema["edge_required"]:
            if field not in edge:
                errors.append(f"edge {edge_id}: missing {field}")
        if edge.get("source") not in nodes:
            errors.append(f"edge {edge_id}: unknown source {edge.get('source')}")
        if edge.get("target") not in nodes:
            errors.append(f"edge {edge_id}: unknown target {edge.get('target')}")
        if edge.get("relation") not in schema["edge_relations"]:
            errors.append(f"edge {edge_id}: invalid relation {edge.get('relation')}")
        if edge.get("confidence") not in schema["confidence_values"]:
            errors.append(f"edge {edge_id}: invalid confidence {edge.get('confidence')}")
        if not edge.get("provenance"):
            errors.append(f"edge {edge_id}: missing provenance")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"ok: {len(nodes)} nodes, {len(edges)} edges")
    return 0


def search(query: str, limit: int) -> int:
    scored = search_nodes(query, limit=limit)
    for score, node_id, node, touching in scored:
        print(f"{node_id}\t{node['type']}\tscore={score}\tedges={touching}\t{node['label']}")
        print(f"  {node['summary']}")
    if not scored:
        print("no matches")
    return 0


def search_papers(query: str, limit: int) -> int:
    scored = search_nodes(query, limit=limit, node_types={"Paper"})
    for score, node_id, node, touching in scored:
        print(f"{node_id}\t{node['type']}\tscore={score}\tedges={touching}\t{node['label']}")
        print(f"  {node['summary']}")
    if not scored:
        print("no matches")
    return 0


def collect_neighborhood(start: str, depth: int) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    nodes, edges = load_graph()
    if start not in nodes:
        raise SystemExit(f"unknown node: {start}")

    adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["source"]].append((edge["target"], edge))
        adjacency[edge["target"]].append((edge["source"], edge))

    seen_nodes = {start}
    seen_edges: dict[str, dict[str, Any]] = {}
    queue = deque([(start, 0)])
    while queue:
        node_id, dist = queue.popleft()
        if dist >= depth:
            continue
        for other, edge in adjacency.get(node_id, []):
            seen_edges[edge["id"]] = edge
            if other not in seen_nodes:
                seen_nodes.add(other)
                queue.append((other, dist + 1))

    return {node_id: nodes[node_id] for node_id in sorted(seen_nodes)}, [seen_edges[key] for key in sorted(seen_edges)]


def provenance_text(items: list[dict[str, Any]]) -> str:
    sources = []
    for item in items:
        source = item.get("source", "unknown")
        method = item.get("method", "unknown")
        sources.append(f"{source} ({method})")
    return "; ".join(sources)


def render_neighborhood(start: str, depth: int) -> str:
    nodes, edges = collect_neighborhood(start, depth)
    lines = [f"# Fact Graph Neighborhood: {start}", ""]
    lines.append("## Nodes")
    for node_id, node in nodes.items():
        lines.append(f"- `{node_id}` [{node['type']}, {node['confidence']}]: {node['label']}")
        lines.append(f"  {node['summary']}")
        lines.append(f"  Provenance: {provenance_text(node.get('provenance', []))}")
    lines.append("")
    lines.append("## Edges")
    for edge in edges:
        lines.append(f"- `{edge['source']}` -{edge['relation']}-> `{edge['target']}` [{edge['confidence']}]")
        lines.append(f"  {edge['claim']}")
        lines.append(f"  Provenance: {provenance_text(edge.get('provenance', []))}")
    lines.append("")
    return "\n".join(lines)


def build_views() -> int:
    nodes, edges = load_graph()
    VIEWS_DIR.mkdir(parents=True, exist_ok=True)

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes.values():
        by_type[node["type"]].append(node)

    index_lines = [
        "# Fact Graph Views",
        "",
        "Generated from `graph/nodes.jsonl` and `graph/edges.jsonl`.",
        "",
        f"- Nodes: {len(nodes)}",
        f"- Edges: {len(edges)}",
        "",
        "## Node Types",
    ]
    for node_type in sorted(by_type):
        filename = f"{node_type.lower()}.md"
        index_lines.append(f"- [{node_type}]({filename}): {len(by_type[node_type])}")
        lines = [f"# {node_type}", ""]
        for node in sorted(by_type[node_type], key=lambda n: n["id"]):
            lines.append(f"## {node['label']}")
            lines.append(f"- ID: `{node['id']}`")
            lines.append(f"- Confidence: {node['confidence']}")
            lines.append(f"- Summary: {node['summary']}")
            aliases = ", ".join(node.get("aliases", []))
            if aliases:
                lines.append(f"- Aliases: {aliases}")
            lines.append(f"- Provenance: {provenance_text(node.get('provenance', []))}")
            related = [e for e in edges if e["source"] == node["id"] or e["target"] == node["id"]]
            if related:
                lines.append("")
                lines.append("Related edges:")
                for edge in related:
                    lines.append(f"- `{edge['source']}` -{edge['relation']}-> `{edge['target']}`: {edge['claim']}")
            lines.append("")
        (VIEWS_DIR / filename).write_text("\n".join(lines), encoding="utf-8")

    (VIEWS_DIR / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"wrote {VIEWS_DIR / 'INDEX.md'}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenScience fact graph utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=8)

    p_search_papers = sub.add_parser("search-papers")
    p_search_papers.add_argument("query")
    p_search_papers.add_argument("--limit", type=int, default=8)

    p_neighborhood = sub.add_parser("neighborhood")
    p_neighborhood.add_argument("node_id")
    p_neighborhood.add_argument("--depth", type=int, default=1)

    sub.add_parser("build-views")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cmd == "validate":
        return validate()
    if args.cmd == "search":
        return search(args.query, args.limit)
    if args.cmd == "search-papers":
        return search_papers(args.query, args.limit)
    if args.cmd == "neighborhood":
        print(render_neighborhood(args.node_id, args.depth))
        return 0
    if args.cmd == "build-views":
        return build_views()
    raise SystemExit(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
