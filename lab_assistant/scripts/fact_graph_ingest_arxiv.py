#!/usr/bin/env python3
"""Fetch arXiv metadata and add low/medium-confidence paper nodes to the fact graph."""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from fact_graph_common import (
    EDGES_PATH,
    NODES_PATH,
    REPO_ROOT,
    concept_matches,
    merge_by_id,
    seed_concept_nodes,
    slugify,
    today_stamp,
)


ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def text_of(entry: ET.Element, tag: str) -> str:
    elem = entry.find(f"{ATOM}{tag}")
    return "" if elem is None or elem.text is None else " ".join(elem.text.split())


def fetch_query(query: str, max_results: int) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    root = ET.fromstring(data)
    results = []
    for entry in root.findall(f"{ATOM}entry"):
        arxiv_id = text_of(entry, "id").rsplit("/", 1)[-1]
        authors = [
            " ".join(author.find(f"{ATOM}name").text.split())
            for author in entry.findall(f"{ATOM}author")
            if author.find(f"{ATOM}name") is not None and author.find(f"{ATOM}name").text
        ]
        doi_elem = entry.find(f"{ARXIV}doi")
        primary = entry.find(f"{ARXIV}primary_category")
        results.append(
            {
                "arxiv_id": arxiv_id,
                "title": text_of(entry, "title"),
                "summary": text_of(entry, "summary"),
                "published": text_of(entry, "published"),
                "updated": text_of(entry, "updated"),
                "authors": authors,
                "doi": "" if doi_elem is None or doi_elem.text is None else doi_elem.text.strip(),
                "primary_category": "" if primary is None else primary.attrib.get("term", ""),
                "url": text_of(entry, "id"),
            }
        )
    return results


def filter_results(results: list[dict], exclude_terms: list[str] | None = None) -> list[dict]:
    if not exclude_terms:
        return results
    lowered = [term.lower() for term in exclude_terms if term.strip()]
    kept: list[dict] = []
    for result in results:
        haystack = f"{result.get('title', '')} {result.get('summary', '')}".lower()
        if any(term in haystack for term in lowered):
            continue
        kept.append(result)
    return kept


def build_records(results: list[dict], query_name: str) -> tuple[list[dict], list[dict]]:
    updated = today_stamp()
    nodes = seed_concept_nodes("arXiv metadata queries", "arxiv metadata ingest")
    edges: list[dict] = []
    for result in results:
        paper_id = f"paper:arxiv_{slugify(result['arxiv_id'])}"
        title = result["title"]
        abstract = result["summary"]
        summary = abstract[:700] + ("..." if len(abstract) > 700 else "")
        provenance = [
            {
                "source": result["url"],
                "method": f"arxiv metadata ingest:{query_name}",
            }
        ]
        nodes.append(
            {
                "id": paper_id,
                "type": "Paper",
                "label": title,
                "aliases": [result["arxiv_id"]] + result.get("authors", [])[:3],
                "summary": summary,
                "provenance": provenance,
                "confidence": "low",
                "updated": updated,
                "metadata": {
                    "published": result["published"],
                    "updated": result["updated"],
                    "doi": result["doi"],
                    "primary_category": result["primary_category"],
                },
            }
        )
        text = f"{title} {abstract}"
        for concept_id in sorted(concept_matches(text)):
            edges.append(
                {
                    "id": f"edge:{slugify(paper_id + '_mentions_' + concept_id, 120)}",
                    "source": paper_id,
                    "target": concept_id,
                    "relation": "mentions",
                    "claim": f"arXiv metadata suggests this paper is relevant to {concept_id}.",
                    "provenance": provenance,
                    "confidence": "low",
                    "updated": updated,
                }
            )
    return nodes, edges


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest arXiv metadata into fact graph.")
    parser.add_argument("--queries", type=Path, default=REPO_ROOT / "lab_assistant" / "graph" / "sources" / "arxiv_queries.json")
    parser.add_argument("--staging", type=Path, default=REPO_ROOT / "lab_assistant" / "graph" / "staging" / "arxiv_results.jsonl")
    parser.add_argument("--sleep", type=float, default=3.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.queries.read_text(encoding="utf-8"))
    all_results: list[dict] = []
    all_nodes: list[dict] = []
    all_edges: list[dict] = []
    for item in config["queries"]:
        results = fetch_query(item["query"], int(item.get("max_results", 8)))
        results = filter_results(results, item.get("exclude_terms"))
        for result in results:
            result["query_name"] = item["name"]
        nodes, edges = build_records(results, item["name"])
        all_results.extend(results)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
        time.sleep(args.sleep)

    args.staging.parent.mkdir(parents=True, exist_ok=True)
    with args.staging.open("w", encoding="utf-8") as f:
        for result in all_results:
            f.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")

    node_added, node_updated = merge_by_id(NODES_PATH, all_nodes)
    edge_added, edge_updated = merge_by_id(EDGES_PATH, all_edges)
    print(f"arxiv results: {len(all_results)}")
    print(f"staging: {args.staging}")
    print(f"nodes: +{node_added}, provenance-updates={node_updated}")
    print(f"edges: +{edge_added}, provenance-updates={edge_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
