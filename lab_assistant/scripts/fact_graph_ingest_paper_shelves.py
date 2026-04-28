#!/usr/bin/env python3
"""Ingest curated Markdown paper shelves into the OpenScience fact graph."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from fact_graph_common import (
    EDGES_PATH,
    NODES_PATH,
    REPO_ROOT,
    concept_matches,
    seed_concept_nodes,
    slugify,
    today_stamp,
    upsert_by_id,
)


PAPER_RE = re.compile(r"^(?P<num>\d+)\.\s+(?P<citation>.+)$")
FIELD_RE = re.compile(r"^- (?P<key>link|result to remember|specific detail|use for):\s*(?P<value>.+)$")


def parse_paper_shelf(path: Path) -> list[dict[str, str]]:
    papers: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        match = PAPER_RE.match(line)
        if match:
            if current:
                papers.append(current)
            current = {
                "citation": match.group("citation").strip(),
                "section": section,
                "source": str(path.relative_to(REPO_ROOT)),
            }
            title_match = re.search(r'"([^"]+)"', current["citation"])
            current["title"] = title_match.group(1) if title_match else current["citation"]
            continue
        field = FIELD_RE.match(line)
        if field and current is not None:
            current[field.group("key")] = field.group("value").strip()
    if current:
        papers.append(current)
    return papers


def build_records(paths: list[Path]) -> tuple[list[dict], list[dict]]:
    updated = today_stamp()
    nodes = seed_concept_nodes("lab_assistant/knowledge/papers", "deterministic paper-shelf ingest")
    edges: list[dict] = []
    for path in paths:
        for paper in parse_paper_shelf(path):
            title = paper["title"]
            paper_id = f"paper:{slugify(title)}"
            result = paper.get("result to remember", "")
            detail = paper.get("specific detail", "")
            use_for = paper.get("use for", "")
            summary_parts = [part for part in [result, detail, f"Use for: {use_for}" if use_for else ""] if part]
            summary = " ".join(summary_parts) or paper["citation"]
            provenance = [{"source": paper["source"], "method": "deterministic paper-shelf ingest"}]
            if paper.get("link"):
                provenance.append({"source": paper["link"], "method": "source link from paper shelf"})

            nodes.append(
                {
                    "id": paper_id,
                    "type": "Paper",
                    "label": title,
                    "aliases": [paper["citation"]],
                    "summary": summary,
                    "provenance": provenance,
                    "confidence": "medium",
                    "updated": updated,
                }
            )

            if result:
                claim_id = f"claim:{slugify(title + ' ' + result, 96)}"
                nodes.append(
                    {
                        "id": claim_id,
                        "type": "Claim",
                        "label": result,
                        "aliases": [title],
                        "summary": summary,
                        "provenance": provenance,
                        "confidence": "medium",
                        "updated": updated,
                    }
                )
                edges.append(
                    {
                        "id": f"edge:{slugify(paper_id + '_supports_' + claim_id, 120)}",
                        "source": paper_id,
                        "target": claim_id,
                        "relation": "supports_claim",
                        "claim": result,
                        "provenance": provenance,
                        "confidence": "medium",
                        "updated": updated,
                    }
                )

            text = " ".join([title, result, detail, use_for])
            for concept_id in sorted(concept_matches(text)):
                edges.append(
                    {
                        "id": f"edge:{slugify(paper_id + '_mentions_' + concept_id, 120)}",
                        "source": paper_id,
                        "target": concept_id,
                        "relation": "mentions",
                        "claim": f"{title} is relevant to {concept_id}.",
                        "provenance": provenance,
                        "confidence": "medium",
                        "updated": updated,
                    }
                )
    return nodes, edges


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest curated paper shelves into fact graph.")
    parser.add_argument("--papers-dir", type=Path, default=REPO_ROOT / "lab_assistant" / "knowledge" / "papers")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(p for p in args.papers_dir.glob("*.md") if p.name != "README.md")
    nodes, edges = build_records(paths)
    node_added, node_updated = upsert_by_id(NODES_PATH, nodes)
    edge_added, edge_updated = upsert_by_id(EDGES_PATH, edges)
    print(f"paper shelves: {len(paths)} files")
    print(f"nodes: +{node_added}, updated={node_updated}")
    print(f"edges: +{edge_added}, updated={edge_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
