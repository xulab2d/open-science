#!/usr/bin/env python3
"""Shared helpers for OpenScience fact-graph scripts."""

from __future__ import annotations

from datetime import date
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_DIR = REPO_ROOT / "lab_assistant" / "graph"
NODES_PATH = GRAPH_DIR / "nodes.jsonl"
EDGES_PATH = GRAPH_DIR / "edges.jsonl"


CONCEPT_RULES = [
    ("concept:moire_filling", ["filling", "nu", "ν", "moire cell", "moiré cell"]),
    ("concept:displacement_field", ["displacement field", "electric field", "gate field", "D field"]),
    ("material:twisted_mote2", ["twisted mote2", "mote2", "mote₂"]),
    ("phenomenon:moire_magnetism", ["magnetism", "magnetic", "ferromagnetic", "antiferromagnetic", "orbital magnetization"]),
    ("phenomenon:phase_competition", ["competing", "competition", "nearby phases", "ground states"]),
    ("phenomenon:fqah", ["fqah", "fractional quantum anomalous hall", "fractional chern", "fci"]),
    ("phenomenon:fqsh", ["fqsh", "fractional quantum spin hall"]),
    ("observable:rmcd", ["rmcd", "mcd", "magnetic circular dichroism"]),
    ("observable:pl", ["photoluminescence", "pl", "trion", "exciton", "anyon-trion"]),
]


SEED_CONCEPTS = {
    "concept:topological_flat_band": {
        "type": "Concept",
        "label": "topological flat band",
        "aliases": ["flat topological band", "Chern band"],
        "summary": "Narrow moiré band with nontrivial topology; a central ingredient for interaction-driven Chern physics.",
    },
    "concept:valley_chern_number": {
        "type": "Concept",
        "label": "valley Chern number",
        "aliases": ["valley Chern"],
        "summary": "Topological index associated with valley-resolved moiré bands.",
    },
    "phenomenon:second_moire_band": {
        "type": "Phenomenon",
        "label": "second moiré band correlated states",
        "aliases": ["second moire band", "higher-band MoTe2"],
        "summary": "Correlated magnetic/topological phenomenology away from the canonical first-band filling regime.",
    },
    "observable:compressibility": {
        "type": "Observable",
        "label": "compressibility",
        "aliases": ["local compressibility"],
        "summary": "Thermodynamic/local probe for incompressible correlated states.",
    },
    "observable:transport": {
        "type": "Observable",
        "label": "transport",
        "aliases": ["Hall transport", "longitudinal resistance", "Hall plateau"],
        "summary": "Electronic transport observables used to identify integer/fractional anomalous Hall and related states.",
    },
    "phenomenon:2d_magnetism": {
        "type": "Phenomenon",
        "label": "two-dimensional magnetism",
        "aliases": ["2D magnetism", "van der Waals magnetism"],
        "summary": "Magnetic order and magnetic excitations in atomically thin or van der Waals materials.",
    },
    "mechanism:magnetic_proximity": {
        "type": "Mechanism",
        "label": "magnetic proximity effect",
        "aliases": ["proximity exchange", "magnetic proximity"],
        "summary": "Magnetic influence of one material on an adjacent layer, often visible through optical valley splitting or polarization.",
    },
    "mechanism:gate_controlled_hamiltonian": {
        "type": "Mechanism",
        "label": "gate-controlled Hamiltonian tuning",
        "aliases": ["electric-field Hamiltonian control", "gate geometry tuning"],
        "summary": "Use of gate field/displacement field to change the effective lattice, band, or interaction landscape rather than only density.",
    },
}


EXTRA_CONCEPT_RULES = [
    ("concept:topological_flat_band", ["topological flat", "flat band", "chern band"]),
    ("concept:valley_chern_number", ["valley chern"]),
    ("phenomenon:second_moire_band", ["second moiré band", "second moire band", "higher band"]),
    ("observable:compressibility", ["compressibility", "incompressible"]),
    ("observable:transport", ["transport", "hall", "resistance", "plateau"]),
    ("phenomenon:2d_magnetism", ["cri3", "2d magnet", "van der waals magnet", "ferromagnetism"]),
    ("mechanism:magnetic_proximity", ["magnetic proximity", "proximity exchange"]),
    ("mechanism:gate_controlled_hamiltonian", ["gate-controlled", "gate field", "electric field", "displacement field"]),
]


PROJECT_SEEDS = {
    "project:shuai_mt43": {
        "label": "Shuai MT43",
        "aliases": ["MT43", "Shuai-MT43-DR911"],
        "summary": "Transport-focused tMoTe2 project around sweep-B and related n-B maps.",
    },
    "project:a5_dot": {
        "label": "A5 dot",
        "aliases": ["A5", "Zengde Weijie A5", "AAtA dot"],
        "summary": "AAtA dot optical project with PL dispersion and peak-tracking analyses.",
    },
    "project:d93_run2": {
        "label": "D93 Run2",
        "aliases": ["D93", "CWB Yifan D93", "Yifan_D93"],
        "summary": "tMoTe2 D93 Run2 work involving AH/QAH, RMCD, and magnetic transition comparisons.",
    },
    "project:b79": {
        "label": "B79",
        "aliases": ["WJL Zengde B79", "B79 Attodry911"],
        "summary": "Attodry911 optical project with established reflectance conventions.",
    },
    "project:c7": {
        "label": "C7",
        "aliases": ["Zengde WJL C7", "C7 Attodry911"],
        "summary": "Attodry911 optical, PL, and reflectance project.",
    },
    "project:d88": {
        "label": "D88",
        "aliases": ["Courtney Christiano D88", "D88 AAA"],
        "summary": "Benchmark-style optical and magnetic tMoTe2 measurements.",
    },
    "project:tmote2_deck_corpus": {
        "label": "tMoTe2 deck corpus",
        "aliases": ["tMoTe2 project decks", "summary decks"],
        "summary": "Curated collection of tMoTe2 working-summary slide decks used for lab context.",
    },
    "project:2d_magnets_deck_corpus": {
        "label": "2D magnets deck corpus",
        "aliases": ["2D magnet summaries", "CrI3 decks", "CrSiTe3 decks"],
        "summary": "Historical working-summary decks for Xu Lab two-dimensional magnet projects.",
    },
}


def slugify(text: str, max_len: int = 80) -> str:
    text = text.lower()
    text = text.replace("₂", "2").replace("é", "e").replace("è", "e").replace("ö", "o")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:max_len].strip("_") or "item"


def today_stamp() -> str:
    return date.today().isoformat()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def merge_by_id(path: Path, new_records: list[dict[str, Any]]) -> tuple[int, int]:
    existing = load_jsonl(path)
    by_id = {record["id"]: record for record in existing}
    added = 0
    updated = 0
    for record in new_records:
        record_id = record["id"]
        if record_id in by_id:
            old = by_id[record_id]
            old_sources = {
                json.dumps(item, sort_keys=True)
                for item in old.get("provenance", [])
                if isinstance(item, dict)
            }
            for item in record.get("provenance", []):
                key = json.dumps(item, sort_keys=True)
                if key not in old_sources:
                    old.setdefault("provenance", []).append(item)
                    old_sources.add(key)
                    updated += 1
            continue
        by_id[record_id] = record
        added += 1
    write_jsonl(path, sorted(by_id.values(), key=lambda r: r["id"]))
    return added, updated


def unique_list(values: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def confidence_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, -1)


def merge_record(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    existing_rank = confidence_rank(existing.get("confidence", "low"))
    incoming_rank = confidence_rank(incoming.get("confidence", "low"))

    for key, value in incoming.items():
        if key == "provenance":
            merged[key] = unique_list(existing.get(key, []) + value)
            continue
        if key == "aliases":
            merged[key] = unique_list(existing.get(key, []) + value)
            continue
        if key == "metadata" and isinstance(value, dict):
            old = existing.get(key, {})
            merged[key] = {**old, **value} if isinstance(old, dict) else dict(value)
            continue
        if key == "confidence":
            merged[key] = incoming.get("confidence") if incoming_rank >= existing_rank else existing.get("confidence")
            continue
        if key in {"label", "summary"}:
            existing_value = str(existing.get(key, "")).strip()
            incoming_value = str(value).strip()
            if not existing_value:
                merged[key] = incoming_value
            elif incoming_rank > existing_rank:
                merged[key] = incoming_value
            elif incoming_rank == existing_rank and len(incoming_value) > len(existing_value):
                merged[key] = incoming_value
            else:
                merged[key] = existing_value
            continue
        merged[key] = value
    return merged


def upsert_by_id(path: Path, new_records: list[dict[str, Any]]) -> tuple[int, int]:
    existing = load_jsonl(path)
    by_id = {record["id"]: record for record in existing}
    added = 0
    updated = 0
    for record in new_records:
        record_id = record["id"]
        if record_id in by_id:
            by_id[record_id] = merge_record(by_id[record_id], record)
            updated += 1
        else:
            by_id[record_id] = record
            added += 1
    write_jsonl(path, sorted(by_id.values(), key=lambda r: r["id"]))
    return added, updated


def concept_matches(text: str) -> set[str]:
    lower = text.lower()
    matches: set[str] = set()
    for concept_id, terms in CONCEPT_RULES + EXTRA_CONCEPT_RULES:
        if any(term in lower for term in terms):
            matches.add(concept_id)
    return matches


def seed_concept_nodes(source: str, method: str) -> list[dict[str, Any]]:
    updated = today_stamp()
    records = []
    for node_id, node in SEED_CONCEPTS.items():
        records.append(
            {
                "id": node_id,
                "type": node["type"],
                "label": node["label"],
                "aliases": node.get("aliases", []),
                "summary": node["summary"],
                "provenance": [{"source": source, "method": method}],
                "confidence": "medium",
                "updated": updated,
            }
        )
    return records


def seed_project_nodes(source: str, method: str) -> list[dict[str, Any]]:
    updated = today_stamp()
    records = []
    for node_id, node in PROJECT_SEEDS.items():
        records.append(
            {
                "id": node_id,
                "type": "Project",
                "label": node["label"],
                "aliases": node.get("aliases", []),
                "summary": node["summary"],
                "provenance": [{"source": source, "method": method}],
                "confidence": "medium",
                "updated": updated,
            }
        )
    return records
