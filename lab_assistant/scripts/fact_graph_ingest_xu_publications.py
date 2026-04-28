#!/usr/bin/env python3
"""Ingest the official Xu Group publication list into the OpenScience fact graph."""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import urlopen

from fact_graph_common import (
    EDGES_PATH,
    NODES_PATH,
    REPO_ROOT,
    concept_matches,
    confidence_rank,
    load_jsonl,
    merge_record,
    seed_concept_nodes,
    slugify,
    today_stamp,
    unique_list,
    write_jsonl,
)


PUBLICATIONS_URL = "https://sites.google.com/uw.edu/xulab/publications"
BLOCK_RE = re.compile(r"<(p|h1|h2|h3|h4)\b[^>]*>(.*?)</\1>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
HREF_RE = re.compile(r'href="([^"]+)"', re.I)
TEXT_URL_RE = re.compile(r"https?://[^\s)]+")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s),;]+", re.I)
ARTICLE_KEY_RE = re.compile(r"s\d{5}-\d{3}-\d{5}-[a-z0-9]+", re.I)
ARXIV_RE = re.compile(r"arxiv[:/ ]+([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", re.I)


TOPIC_RULES: list[tuple[str, list[str]]] = [
    ("moire_tmote2", ["mote2", "fractional chern", "anomalous hall", "composite fermi", "chern magnet"]),
    ("graphene_moire", ["graphene", "hofstadter", "twisted bilayer graphene", "double bilayer graphene"]),
    ("semiconductor_moire", ["moire", "moiré", "heterobilayer", "superlattice", "twisted wse2", "ws2", "wse2/ws2"]),
    ("valley_exciton_optics", ["exciton", "trion", "valley", "photoluminescence", "polariton"]),
    ("vdw_magnetism", ["magnet", "magnetic", "magnon", "ferromagnet", "antiferromagnet", "cri3", "crcl3", "crsbr", "fe3gete2"]),
    ("topological_quantum_materials", ["wte2", "topological", "weyl", "chern", "quantum spin hall", "majorana"]),
    ("strain_and_devices", ["strain", "metalens", "nanocavity", "light-emitting", "photonic crystal", "tunnel junction"]),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest official Xu Group publication metadata into the fact graph.")
    parser.add_argument(
        "--url",
        default=PUBLICATIONS_URL,
        help="Official publications page to parse.",
    )
    parser.add_argument(
        "--staging",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "graph" / "staging" / "xu_group_publications.jsonl",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=REPO_ROOT / "lab_assistant" / "knowledge" / "index" / "xu_group_publications.md",
    )
    parser.add_argument(
        "--include-before-uw",
        action="store_true",
        help="Include the 'Before UW (2002-2010)' section.",
    )
    return parser.parse_args()


def clean_text(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value)
    return " ".join(value.split())


def normalize_title(value: str) -> str:
    replacements = {
        "–": "-",
        "—": "-",
        "−": "-",
        "₂": "2",
        "α": "alpha",
        "β": "beta",
        "γ": "gamma",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\s+", " ", value.strip())
    return value


def title_key(value: str) -> str:
    value = normalize_title(value).lower()
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return " ".join(value.split())


def extract_urls(block_html: str, block_text: str) -> list[str]:
    urls = [match.rstrip(".,;") for match in HREF_RE.findall(block_html)]
    urls.extend(match.rstrip(".,;") for match in TEXT_URL_RE.findall(block_text))
    for match in DOI_RE.findall(block_text):
        urls.append(f"https://doi.org/{match.rstrip('.,;')}")
    cleaned = []
    for url in urls:
        lower = url.lower()
        if lower.startswith("#"):
            continue
        if "arxiv.org/search/" in lower or "arxiv.org/find/" in lower:
            continue
        cleaned.append(url)
    return unique_list(cleaned)


def extract_keys(*values: str) -> set[str]:
    keys: set[str] = set()
    for value in values:
        for match in DOI_RE.findall(value):
            keys.add(match.rstrip(".,;").lower())
        for match in ARTICLE_KEY_RE.findall(value):
            keys.add(match.lower())
        arxiv_match = ARXIV_RE.search(value)
        if arxiv_match:
            keys.add(arxiv_match.group(1).lower())
    return keys


def infer_topics(text: str) -> list[str]:
    lower = text.lower()
    tags = [tag for tag, terms in TOPIC_RULES if any(term in lower for term in terms)]
    return tags or ["other_quantum_materials"]


def publication_quality(year: str, raw_citation: str, urls: list[str]) -> float:
    lower = raw_citation.lower()
    score = 0.0
    if year.isdigit():
        score += int(year) / 10000.0
    if any("doi.org" in url for url in urls):
        score += 4.0
    if any("nature.com" in url or "science.org" in url or "aps.org" in url for url in urls):
        score += 2.0
    if "arxiv" in lower:
        score -= 2.0
    if year == "submitted":
        score -= 1.0
    return score


def parse_publications(url: str, include_before_uw: bool) -> list[dict]:
    page = urlopen(url, timeout=30).read().decode("utf-8", errors="ignore")
    blocks = BLOCK_RE.findall(page)
    current_year: str | None = None
    before_uw = False
    by_title: dict[str, dict] = {}

    for tag, body in blocks:
        text = clean_text(body)
        if not text or text.startswith("var DOCS_timing"):
            continue
        tag = tag.lower()
        if tag == "h2" and text == "Submitted":
            current_year = "submitted"
            before_uw = False
            continue
        if tag == "h2" and text == "Before UW (2002-2010)":
            current_year = "before_uw"
            before_uw = True
            continue
        if tag == "h2" and re.fullmatch(r"20\d{2}", text):
            current_year = text
            before_uw = False
            continue
        if current_year is None:
            continue
        if before_uw and not include_before_uw:
            continue

        title = normalize_title(text.split(",", 1)[0].strip())
        if not title or title.lower().startswith("doi:"):
            continue
        if len(title.split()) < 3:
            continue

        urls = extract_urls(body, text)
        raw_key = title_key(title)
        entry = {
            "year": current_year,
            "title": title,
            "title_key": raw_key,
            "raw_citation": text,
            "urls": urls,
            "citation_keys": sorted(extract_keys(text, " ".join(urls))),
            "topic_tags": infer_topics(text),
            "status": "submitted" if current_year == "submitted" else "published",
        }
        score = publication_quality(current_year, text, urls)
        previous = by_title.get(raw_key)
        if previous is None or score > previous["_score"]:
            entry["_score"] = score
            by_title[raw_key] = entry

    results = []
    for item in by_title.values():
        item.pop("_score", None)
        results.append(item)
    results.sort(key=lambda item: (item["year"] == "submitted", item["year"]), reverse=True)
    return results


def title_similarity(a: str, b: str) -> bool:
    if a == b:
        return True
    if a in b or b in a:
        a_tokens = set(a.split())
        b_tokens = set(b.split())
        overlap = len(a_tokens & b_tokens)
        return overlap >= max(4, int(0.7 * min(len(a_tokens), len(b_tokens))))
    return False


def node_source_keys(node: dict) -> set[str]:
    values = [node.get("label", "")]
    values.extend(node.get("aliases", []))
    values.extend(str(item.get("source", "")) for item in node.get("provenance", []))
    metadata = node.get("metadata", {})
    if isinstance(metadata, dict):
        values.extend(str(item) for item in metadata.values() if isinstance(item, str))
    return extract_keys(*values)


def pick_canonical_paper_id(candidates: list[dict]) -> str:
    def score(node: dict) -> tuple[int, int, int, str]:
        methods = " ".join(item.get("method", "") for item in node.get("provenance", []))
        return (
            0 if node["id"].startswith("paper:arxiv_") else 1,
            confidence_rank(node.get("confidence", "low")),
            1 if "paper-shelf" in methods or "knowledge/papers" in methods else 0,
            node["id"],
        )

    return sorted(candidates, key=score, reverse=True)[0]["id"]


def existing_paper_indices() -> tuple[dict[str, dict], dict[str, set[str]], dict[str, set[str]]]:
    nodes = {node["id"]: node for node in load_jsonl(NODES_PATH)}
    key_index: dict[str, set[str]] = defaultdict(set)
    title_index: dict[str, set[str]] = defaultdict(set)
    for node in nodes.values():
        if node.get("type") != "Paper":
            continue
        for key in node_source_keys(node):
            key_index[key].add(node["id"])
        title_index[title_key(str(node.get("label", "")))].add(node["id"])
        for alias in node.get("aliases", []):
            title_index[title_key(alias)].add(node["id"])
    return nodes, key_index, title_index


def matching_paper_id(entry: dict, nodes: dict[str, dict], key_index: dict[str, set[str]], title_index: dict[str, set[str]]) -> str | None:
    candidate_ids: set[str] = set()
    for key in entry["citation_keys"]:
        candidate_ids.update(key_index.get(key, set()))
    candidate_ids.update(title_index.get(entry["title_key"], set()))

    if not candidate_ids:
        for other_key, ids in title_index.items():
            if other_key and title_similarity(entry["title_key"], other_key):
                candidate_ids.update(ids)

    candidate_nodes = [nodes[item] for item in sorted(candidate_ids) if item in nodes and nodes[item].get("type") == "Paper"]
    if not candidate_nodes:
        return None
    return pick_canonical_paper_id(candidate_nodes)


def venue_hint(raw_citation: str) -> str:
    tail = raw_citation.split(",", 1)[-1]
    for marker in [
        "Nature",
        "Science",
        "PRX",
        "Physical Review",
        "Nature Physics",
        "Nature Materials",
        "Nature Nanotechnology",
        "Nature Communications",
        "Nano Letters",
        "Annual Review",
        "Communications Physics",
        "Nano Today",
    ]:
        if marker.lower() in tail.lower():
            return marker
    return ""


def build_records(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    updated = today_stamp()
    nodes = seed_concept_nodes(PUBLICATIONS_URL, "official xu group publications ingest")
    edges: list[dict] = []
    existing_nodes, key_index, title_index = existing_paper_indices()

    for entry in entries:
        matched_id = matching_paper_id(entry, existing_nodes, key_index, title_index)
        paper_id = matched_id or f"paper:{slugify(entry['title'])}"
        provenance = [{"source": PUBLICATIONS_URL, "method": "official xu group publications ingest"}]
        provenance.extend({"source": url, "method": "official publication link"} for url in entry["urls"])

        summary_bits = [f"Official Xu Group publication ({entry['year']})."]
        venue = venue_hint(entry["raw_citation"])
        if venue:
            summary_bits.append(f"Venue hint: {venue}.")
        if entry["topic_tags"]:
            summary_bits.append(f"Topics: {', '.join(entry['topic_tags'])}.")

        nodes.append(
            {
                "id": paper_id,
                "type": "Paper",
                "label": entry["title"],
                "aliases": [entry["raw_citation"]],
                "summary": " ".join(summary_bits),
                "provenance": provenance,
                "confidence": "low",
                "updated": updated,
                "metadata": {
                    "year": entry["year"],
                    "status": entry["status"],
                    "topic_tags": entry["topic_tags"],
                    "citation_keys": entry["citation_keys"],
                    "raw_citation": entry["raw_citation"],
                    "official_xu_group_publication": True,
                },
            }
        )

        text = " ".join([entry["title"], entry["raw_citation"], " ".join(entry["topic_tags"])])
        for concept_id in sorted(concept_matches(text)):
            edges.append(
                {
                    "id": f"edge:{slugify(paper_id + '_mentions_' + concept_id, 120)}",
                    "source": paper_id,
                    "target": concept_id,
                    "relation": "mentions",
                    "claim": f"{entry['title']} is relevant to {concept_id}.",
                    "provenance": provenance,
                    "confidence": "low",
                    "updated": updated,
                }
            )

    return nodes, edges


def upsert_records(path: Path, incoming: list[dict]) -> tuple[int, int]:
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


def write_staging(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def write_index(path: Path, entries: list[dict]) -> None:
    def markdown_url(url: str) -> str:
        return url.replace("(", "%28").replace(")", "%29")

    def best_url(urls: list[str]) -> str | None:
        if not urls:
            return None

        def score(url: str) -> tuple[int, str]:
            lower = url.lower()
            if "doi.org" in lower:
                return (4, url)
            if any(host in lower for host in ["nature.com", "science.org", "aps.org", "acs.org", "cell.com"]):
                return (3, url)
            if "arxiv.org/abs/" in lower:
                return (2, url)
            return (1, url)

        return sorted(urls, key=score, reverse=True)[0]

    by_year: dict[str, list[dict]] = defaultdict(list)
    topic_counter: Counter[str] = Counter()
    for entry in entries:
        by_year[entry["year"]].append(entry)
        topic_counter.update(entry["topic_tags"])

    ordered_years = sorted(by_year, key=lambda year: (year == "submitted", year), reverse=True)
    lines = [
        "# Xu Group Publications",
        "",
        "Purpose:",
        "- Deterministic index of publications from the official Xu Group publications page.",
        "- Broad metadata coverage for fact-graph expansion; curated scientific takeaways still live in `knowledge/papers/` and `knowledge/syntheses/`.",
        "",
        f"- Source: {PUBLICATIONS_URL}",
        f"- Canonical publication entries: {len(entries)}",
        "",
        "## Topic Counts",
    ]
    for topic, count in sorted(topic_counter.items()):
        lines.append(f"- `{topic}`: {count}")
    lines.append("")

    for year in ordered_years:
        lines.append(f"## {year}")
        for entry in by_year[year]:
            tags = ", ".join(entry["topic_tags"])
            chosen_url = best_url(entry["urls"])
            if chosen_url:
                lines.append(f"- [{entry['title']}]({markdown_url(chosen_url)})")
            else:
                lines.append(f"- {entry['title']}")
            lines.append(f"  tags: {tags}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    entries = parse_publications(args.url, args.include_before_uw)
    nodes, edges = build_records(entries)
    write_staging(args.staging, entries)
    write_index(args.index, entries)
    node_added, node_updated = upsert_records(NODES_PATH, nodes)
    edge_added, edge_updated = upsert_records(EDGES_PATH, edges)
    print(f"official xu publications: {len(entries)}")
    print(f"staging: {args.staging}")
    print(f"index: {args.index}")
    print(f"nodes: +{node_added}, updated={node_updated}")
    print(f"edges: +{edge_added}, updated={edge_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
