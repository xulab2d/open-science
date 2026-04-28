#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any


def iso_now() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def infer_title(path: Path) -> str:
    stem = path.stem.replace("_", " ").strip()
    return stem or path.name


def doc_id(collection_id: str, path: Path) -> str:
    raw = f"{collection_id}:{path}"
    return hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


def matches_patterns(path: Path, patterns: list[str]) -> bool:
    if not patterns:
        return True
    name = path.name
    text = path.as_posix()
    for pattern in patterns:
        if pattern in text or pattern in name or fnmatch.fnmatch(name, f"*{pattern}*"):
            return True
    return False


def iter_collection_files(collection: dict[str, Any]) -> list[Path]:
    root = Path(collection["root"])
    if not root.exists():
        return []

    include_exts = {ext.lower() for ext in collection.get("include_extensions", [])}
    patterns = collection.get("path_patterns", [])
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if include_exts and path.suffix.lower() not in include_exts:
            continue
        if not matches_patterns(path, patterns):
            continue
        out.append(path)
    return sorted(out)


def build_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for collection in manifest.get("collections", []):
        root = Path(collection["root"])
        for path in iter_collection_files(collection):
            stat = path.stat()
            rel = path.relative_to(root).as_posix() if root in path.parents or path == root else path.name
            records.append(
                {
                    "doc_id": doc_id(collection["id"], path),
                    "collection_id": collection["id"],
                    "collection_label": collection["label"],
                    "kind": collection["kind"],
                    "root": str(root),
                    "path": str(path),
                    "relative_path": rel,
                    "ext": path.suffix.lower(),
                    "title_guess": infer_title(path),
                    "size_bytes": stat.st_size,
                    "modified_at": dt.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
                }
            )
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        meta = {"type": "meta", "generated_at": iso_now(), "count": len(records)}
        fh.write(json.dumps(meta, ensure_ascii=True) + "\n")
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=True) + "\n")


def write_markdown_summary(path: Path, records: list[dict[str, Any]]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(record["collection_label"], []).append(record)

    lines = ["# Reference Inventory", ""]
    lines.append(f"- generated_at: `{iso_now()}`")
    lines.append(f"- document_count: `{len(records)}`")
    lines.append("")

    for label in sorted(grouped):
        docs = grouped[label]
        lines.append(f"## {label}")
        lines.append("")
        lines.append(f"- count: `{len(docs)}`")
        lines.append(f"- newest: `{max(doc['modified_at'] for doc in docs)}`")
        lines.append("")
        for doc in docs[:25]:
            lines.append(f"- `{doc['relative_path']}`")
        if len(docs) > 25:
            lines.append(f"- ... `{len(docs) - 25}` more")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an inventory of papers and summary decks.")
    ap.add_argument("--manifest", required=True, help="Path to source manifest JSON")
    ap.add_argument("--out-jsonl", required=True, help="Path to output JSONL inventory")
    ap.add_argument("--out-md", required=True, help="Path to output markdown summary")
    args = ap.parse_args()

    manifest = load_manifest(Path(args.manifest))
    records = build_records(manifest)
    write_jsonl(Path(args.out_jsonl), records)
    write_markdown_summary(Path(args.out_md), records)
    print(f"inventory_records={len(records)}")
    print(f"jsonl={args.out_jsonl}")
    print(f"markdown={args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
