#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_inventory(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("type") == "meta":
            continue
        rows.append(obj)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a compact overview of knowledge sources.")
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = load_inventory(Path(args.inventory))
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["kind"], row["collection_label"])].append(row)

    lines = ["# Reference Overview", ""]
    lines.append("This file is a compact map of where reusable lab and field context lives.")
    lines.append("")

    for (kind, label), docs in sorted(grouped.items()):
        lines.append(f"## {label}")
        lines.append("")
        lines.append(f"- kind: `{kind}`")
        lines.append(f"- count: `{len(docs)}`")
        lines.append(f"- root: `{docs[0]['root']}`")
        lines.append("- examples:")
        for doc in docs[:8]:
            lines.append(f"  - `{doc['relative_path']}`")
        lines.append("")

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"overview={args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
