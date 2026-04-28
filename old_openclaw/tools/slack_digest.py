#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable


QUESTION_CATEGORIES = ["naming", "ownership", "instrument", "schema", "analysis"]

def _sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_people(path: Path) -> dict[str, dict[str, Any]]:
    people: dict[str, dict[str, Any]] = {}
    for rec in _read_jsonl(path):
        if rec.get("type") == "meta":
            continue
        pk = rec.get("person_key")
        if isinstance(pk, str) and pk:
            people[pk] = rec
    return people


def _load_routing_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = _load_json(path)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for x in items:
        if not x or x in seen:
            continue
        out.append(x)
        seen.add(x)
    return out


def _route(category: str, family: str | None, rules: dict[str, Any]) -> list[str]:
    categories = rules.get("categories") if isinstance(rules.get("categories"), dict) else {}
    families = rules.get("families") if isinstance(rules.get("families"), dict) else {}
    cat_rule = categories.get(category) if isinstance(categories.get(category), dict) else {}
    fam_rule = families.get(family) if isinstance(families.get(family), dict) else {}

    people_keys: list[str] = []
    people_keys.extend([p for p in (cat_rule.get("people_keys") or []) if isinstance(p, str)])
    people_keys.extend([p for p in (fam_rule.get("people_keys") or []) if isinstance(p, str)])
    return _dedupe_preserve_order([p.strip() for p in people_keys if p.strip()])


def _infer_family(evidence_paths: list[str]) -> str | None:
    for p in evidence_paths:
        s = str(p).replace(os.sep, "/")
        if s.startswith("data::"):
            rel = s[len("data::") :].lstrip("/")
            fam = rel.split("/", 1)[0].strip()
            if fam:
                return fam
        if s.startswith("data/"):
            parts = s.split("/")
            if len(parts) >= 2 and parts[1]:
                return parts[1]
    return None


def _person_label(person_key: str, people: dict[str, dict[str, Any]]) -> str:
    rec = people.get(person_key) or {}
    display = rec.get("display_name")
    if isinstance(display, str) and display.strip():
        return f"{display.strip()} (`{person_key}`)"
    return f"`{person_key}`"


def _write_text_if_changed(path: Path, content: str) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if existing == content:
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Generate a Slack-ready clarifications digest (no API calls).")
    ap.add_argument("--queue", default="index/open_questions.jsonl", help="Questions queue JSONL path")
    ap.add_argument("--people", default="index/people.jsonl", help="People index JSONL path")
    ap.add_argument("--routing", default="index/routing_rules.json", help="Routing rules JSON path")
    ap.add_argument("--out", default="out/slack_clarifications_digest.md", help="Output markdown path")
    args = ap.parse_args(argv)

    cwd = Path.cwd().resolve()
    queue_path = (cwd / args.queue).resolve()
    people_path = (cwd / args.people).resolve()
    routing_path = (cwd / args.routing).resolve()
    out_path = (cwd / args.out).resolve()

    records = _read_jsonl(queue_path)
    people = _load_people(people_path) if people_path.exists() else {}
    routing = _load_routing_rules(routing_path)

    open_items: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("type") == "meta":
            continue
        status = rec.get("status") or "open"
        if status != "open":
            continue
        open_items.append(rec)

    # category -> assignee_key -> [items]
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for item in open_items:
        category = item.get("category") if isinstance(item.get("category"), str) else "analysis"
        if category not in QUESTION_CATEGORIES:
            category = "analysis"

        evidence_paths = item.get("evidence_paths") if isinstance(item.get("evidence_paths"), list) else []
        evidence_paths = [str(p) for p in evidence_paths]

        suggested = item.get("suggested_assignees") if isinstance(item.get("suggested_assignees"), list) else []
        suggested = [str(p) for p in suggested if isinstance(p, str)]
        suggested = _dedupe_preserve_order([p.strip() for p in suggested if p.strip()])

        if not suggested and routing:
            family = _infer_family(evidence_paths)
            suggested = _route(category, family, routing)

        primary = suggested[0] if suggested else "unassigned"
        grouped.setdefault(category, {}).setdefault(primary, []).append(item)

    lines: list[str] = []
    today = dt.date.today().isoformat()
    lines.append(f"# OpenClaw clarifications digest ({today})")
    lines.append("")
    stable_payload = json.dumps(sorted(open_items, key=lambda r: (str(r.get("id") or ""), str(r.get("created_at") or ""))), sort_keys=True)
    digest_id = _sha1_hex(stable_payload)[:12]
    lines.append(f"- digest_id: `{digest_id}`")
    lines.append(f"- open questions: `{len(open_items)}`")
    lines.append("")

    if not open_items:
        lines.append("_No open questions in the queue._")
        lines.append("")
        content = "\n".join(lines)
        wrote = _write_text_if_changed(out_path, content + "\n")
        print(f"wrote: {wrote} -> {out_path}")
        return 0

    for category in QUESTION_CATEGORIES:
        if category not in grouped:
            continue
        cat_groups = grouped[category]
        cat_count = sum(len(v) for v in cat_groups.values())
        lines.append(f"## {category} ({cat_count})")
        lines.append("")

        for assignee in sorted(cat_groups.keys(), key=lambda x: (x == "unassigned", x)):
            items = cat_groups[assignee]
            if assignee == "unassigned":
                lines.append("### unassigned")
            else:
                lines.append(f"### {_person_label(assignee, people)}")
            lines.append("")

            for q in sorted(items, key=lambda r: (str(r.get("created_at") or ""), str(r.get("id") or ""))):
                qid = q.get("id") if isinstance(q.get("id"), str) else ""
                qtext = q.get("question_text") if isinstance(q.get("question_text"), str) else ""
                ev = q.get("evidence_paths") if isinstance(q.get("evidence_paths"), list) else []
                ev = [str(p) for p in ev][:3]

                prefix = f"- `{qid}` " if qid else "- "
                lines.append(prefix + qtext.strip())
                if ev:
                    lines.append("  - evidence: " + ", ".join(f"`{p}`" for p in ev))
                lines.append("")

        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    wrote = _write_text_if_changed(out_path, content)
    print(f"wrote: {wrote} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
