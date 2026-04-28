#!/usr/bin/env python3
"""List active projects deterministically (no embedding search).

Reads:
- memory/projects.md (human-readable)
- index/projects_registry.jsonl (structured)

Usage:
  python3 tools/list_projects.py
  python3 tools/list_projects.py --json
"""

import argparse, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_registry(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            # keep going; registry is append-only in spirit
            continue
    return rows


def read_projects_md(path: Path):
    if not path.exists():
        return ""
    return path.read_text()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    reg = read_registry(ROOT / "index" / "projects_registry.jsonl")
    md = read_projects_md(ROOT / "memory" / "projects.md")

    if args.json:
        print(json.dumps({"registry": reg, "projects_md": md}, indent=2))
        return

    # compact, Slack-friendly bullets
    active = [r for r in reg if r.get("status") in ("active", "ongoing", "unknown", None)]
    print("Active projects (from index/projects_registry.jsonl):")
    for r in active:
        title = r.get("title", r.get("project_id"))
        people = ", ".join([p.get("name","?") for p in r.get("people",[])]) or "(unknown)"
        mods = ", ".join(r.get("modalities", [])) or "(unspecified)"
        path = (r.get("paths") or {}).get("dropbox") or (r.get("paths") or {}).get("root") or ""
        extra = f" — {path}" if path else ""
        print(f"- {title} [{mods}] (people: {people}){extra}")

    print("\nHuman-readable overview: memory/projects.md")
    # Print headings only
    for line in md.splitlines():
        if line.startswith("## "):
            print(f"{line}")


if __name__ == "__main__":
    main()
