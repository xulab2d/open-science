#!/usr/bin/env python3
"""Ingest extracted lab summary decks into the OpenScience fact graph.

This is intentionally conservative: deck text becomes provenance-linked evidence,
and only short, interpretation-like lines become low-confidence claims.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from fact_graph_common import (
    EDGES_PATH,
    NODES_PATH,
    REPO_ROOT,
    concept_matches,
    merge_by_id,
    seed_concept_nodes,
    seed_project_nodes,
    slugify,
    today_stamp,
)


SLIDE_RE = re.compile(r"\[Slide\s+(?P<num>\d+)\]\s*", re.IGNORECASE)

CLAIM_KEYWORDS = {
    "fraction": 5,
    "fractional": 5,
    "correlated": 5,
    "qah": 5,
    "ah state": 5,
    "rmcd": 5,
    "hysteresis": 5,
    "magnetic": 4,
    "afm": 4,
    "fm": 4,
    "transition": 4,
    "disappear": 4,
    "visible": 3,
    "clear": 3,
    "feature": 3,
    "state": 3,
    "staircase": 3,
    "wigner": 3,
    "trion": 3,
    "exciton": 3,
    "dot": 3,
    "d-field": 3,
    "displacement field": 3,
    "gate": 2,
    "gating": 2,
    "need": 2,
    "next": 2,
    "try": 1,
    "seems": 1,
    "probably": 1,
    "likely": 1,
    "unclear": 1,
    "no clear": 2,
    "no obvious": 2,
}

BOILERPLATE_PATTERNS = [
    re.compile(r"^slide\s+\d+$", re.IGNORECASE),
    re.compile(r"^[\d\s.,:+\-_/()=<>~#]+$"),
    re.compile(r"^https?://", re.IGNORECASE),
    re.compile(r"^(spot|slide|sample|fab|measure|measuring|temperature|t\s*=)", re.IGNORECASE),
    re.compile(r"^(rmcd|pl|dual gate|spatial|doping|d-field).*(scan|map|dependence|sweep)\b", re.IGNORECASE),
]

PROJECT_PATTERNS = [
    ("project:d93_run2", ["d93", "yifan_d93"]),
    ("project:shuai_mt43", ["mt43", "shuai-mt43"]),
    ("project:a5_dot", ["a5", "aata dot"]),
    ("project:b79", ["b79"]),
    ("project:c7", ["c7"]),
    ("project:d88", ["d88"]),
]


def normalize_text(text: str) -> str:
    text = text.replace("\x0b", "\n")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return text


def split_slides(text: str) -> list[tuple[str, str]]:
    normalized = normalize_text(text)
    parts = SLIDE_RE.split(normalized)
    slides: list[tuple[str, str]] = []
    if parts and parts[0].strip():
        slides.append(("unknown", parts[0].strip()))
    for index in range(1, len(parts), 2):
        num = parts[index]
        body = parts[index + 1].strip() if index + 1 < len(parts) else ""
        if body:
            slides.append((num, body))
    return slides


def clean_line(line: str) -> str:
    line = " ".join(line.strip(" \t-*->").split())
    return line


def is_boilerplate(line: str) -> bool:
    if len(line) < 28 or len(line) > 240:
        return True
    if sum(ch.isdigit() for ch in line) > max(12, len(line) // 3):
        return True
    lower = line.lower()
    if any(term in lower for term in ["scan", "map", "dependence", "sweep"]) and not any(
        term in lower
        for term in [
            "clear",
            "feature",
            "state",
            "hysteresis",
            "transition",
            "fraction",
            "correlated",
            "disappear",
            "visible",
            "need",
            "seems",
            "probably",
            "unclear",
        ]
    ):
        return True
    return any(pattern.search(line) for pattern in BOILERPLATE_PATTERNS)


def claim_score(line: str) -> int:
    lower = line.lower()
    score = 0
    for term, weight in CLAIM_KEYWORDS.items():
        if term in lower:
            score += weight
    if any(phrase in lower for phrase in ["there is", "there are", "can see", "we see", "looks", "seems"]):
        score += 2
    if any(phrase in lower for phrase in ["need to", "next thing", "try another", "follow up"]):
        score += 2
    return score


def extract_claims(text: str, max_claims: int) -> list[dict[str, str]]:
    candidates: list[tuple[int, int, dict[str, str]]] = []
    seen: set[str] = set()
    order = 0
    for slide_num, body in split_slides(text):
        for raw in body.splitlines():
            line = clean_line(raw)
            if is_boilerplate(line):
                continue
            key = re.sub(r"[^a-z0-9]+", " ", line.lower()).strip()
            if key in seen:
                continue
            seen.add(key)
            score = claim_score(line)
            if score < 4:
                continue
            candidates.append((score, order, {"slide": slide_num, "text": line}))
            order += 1

    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected = sorted(candidates[:max_claims], key=lambda item: item[1])
    return [item[2] for item in selected]


def summary_from_text(text: str, max_chars: int = 500) -> str:
    lines = []
    for _slide, body in split_slides(text):
        for raw in body.splitlines():
            line = clean_line(raw)
            if line and not is_boilerplate(line):
                lines.append(line)
            if len(" ".join(lines)) >= max_chars:
                break
        if len(" ".join(lines)) >= max_chars:
            break
    summary = " ".join(lines)[:max_chars].strip()
    return summary or "Extracted text from a lab summary deck."


def project_for_deck(path: str, title: str, collection_id: str) -> str:
    lower = f"{path} {title}".lower()
    for project_id, terms in PROJECT_PATTERNS:
        if any(term in lower for term in terms):
            return project_id
    if "2d magnet" in collection_id.lower() or any(term in lower for term in ["cri3", "crsite3", "nips3", "vs2"]):
        return "project:2d_magnets_deck_corpus"
    return "project:tmote2_deck_corpus"


def confidence_for_claim(line: str) -> str:
    lower = line.lower()
    if any(term in lower for term in ["unclear", "seems", "probably", "likely", "possible", "perhaps"]):
        return "low"
    return "medium"


def build_records(paths: list[Path], max_claims: int) -> tuple[list[dict], list[dict]]:
    updated = today_stamp()
    nodes = seed_concept_nodes("lab summary deck extraction", "deterministic deck ingest")
    nodes.extend(seed_project_nodes("lab summary deck extraction", "deterministic deck ingest"))
    edges: list[dict] = []

    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "ok" or not data.get("text"):
            continue
        doc_id = data["doc_id"]
        title = data.get("title_guess") or Path(data.get("path", doc_id)).stem
        source_path = data.get("path", "")
        collection_id = data.get("collection_id", "")
        text = normalize_text(data["text"])
        source = str(path.relative_to(REPO_ROOT))
        project_id = project_for_deck(source_path, title, collection_id)
        provenance = [
            {"source": source, "method": "extracted deck text"},
            {"source": source_path, "method": "original deck path"},
        ]

        evidence_id = f"evidence:deck_{doc_id}"
        nodes.append(
            {
                "id": evidence_id,
                "type": "Evidence",
                "label": f"Deck: {title}",
                "aliases": [source_path, doc_id],
                "summary": summary_from_text(text),
                "provenance": provenance,
                "confidence": "medium",
                "updated": updated,
                "metadata": {
                    "collection_id": collection_id,
                    "char_count": data.get("char_count", 0),
                    "kind": data.get("kind", ""),
                },
            }
        )
        edges.append(
            {
                "id": f"edge:{slugify(evidence_id + '_part_of_' + project_id, 120)}",
                "source": evidence_id,
                "target": project_id,
                "relation": "part_of",
                "claim": f"{title} is a summary deck associated with {project_id}.",
                "provenance": provenance,
                "confidence": "medium" if project_id.startswith("project:") else "low",
                "updated": updated,
            }
        )

        deck_text_for_matching = f"{title} {text[:4000]}"
        for concept_id in sorted(concept_matches(deck_text_for_matching)):
            edges.append(
                {
                    "id": f"edge:{slugify(evidence_id + '_mentions_' + concept_id, 120)}",
                    "source": evidence_id,
                    "target": concept_id,
                    "relation": "mentions",
                    "claim": f"{title} contains deck text relevant to {concept_id}.",
                    "provenance": provenance,
                    "confidence": "low",
                    "updated": updated,
                }
            )

        for claim in extract_claims(text, max_claims=max_claims):
            claim_text = claim["text"]
            claim_id = f"claim:deck_{doc_id}_slide_{claim['slide']}_{slugify(claim_text, 56)}"
            conf = confidence_for_claim(claim_text)
            claim_provenance = provenance + [{"source": f"{source}#slide-{claim['slide']}", "method": "salient line extraction"}]
            nodes.append(
                {
                    "id": claim_id,
                    "type": "Claim",
                    "label": claim_text,
                    "aliases": [title, f"slide {claim['slide']}"],
                    "summary": f"Deck-derived claim from {title}, slide {claim['slide']}: {claim_text}",
                    "provenance": claim_provenance,
                    "confidence": conf,
                    "updated": updated,
                }
            )
            edges.append(
                {
                    "id": f"edge:{slugify(evidence_id + '_supports_' + claim_id, 120)}",
                    "source": evidence_id,
                    "target": claim_id,
                    "relation": "supports_claim",
                    "claim": claim_text,
                    "provenance": claim_provenance,
                    "confidence": conf,
                    "updated": updated,
                }
            )
            for concept_id in sorted(concept_matches(claim_text)):
                edges.append(
                    {
                        "id": f"edge:{slugify(claim_id + '_mentions_' + concept_id, 120)}",
                        "source": claim_id,
                        "target": concept_id,
                        "relation": "mentions",
                        "claim": f"Deck-derived claim is relevant to {concept_id}.",
                        "provenance": claim_provenance,
                        "confidence": conf,
                        "updated": updated,
                    }
                )

    return nodes, edges


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest extracted lab summary decks into fact graph.")
    parser.add_argument(
        "--summaries-dir",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "knowledge" / "extracted" / "summaries_curated",
    )
    parser.add_argument("--max-claims-per-deck", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(p for p in args.summaries_dir.glob("*.json") if p.name != "manifest.json")
    nodes, edges = build_records(paths, args.max_claims_per_deck)
    node_added, node_updated = merge_by_id(NODES_PATH, nodes)
    edge_added, edge_updated = merge_by_id(EDGES_PATH, edges)
    print(f"summary decks: {len(paths)} files")
    print(f"nodes: +{node_added}, provenance-updates={node_updated}")
    print(f"edges: +{edge_added}, provenance-updates={edge_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
