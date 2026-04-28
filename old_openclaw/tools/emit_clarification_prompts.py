#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


CATEGORY_IMPACT = {
    "ownership": 1.0,
    "naming": 0.9,
    "instrument": 0.8,
    "analysis": 0.6,
    "schema": 0.6,
}


def _iso_now() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _parse_iso(value: str) -> dt.datetime | None:
    try:
        d = dt.datetime.fromisoformat(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
        return d
    except Exception:
        return None


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


def _load_people(path: Path) -> dict[str, dict[str, Any]]:
    people: dict[str, dict[str, Any]] = {}
    for rec in _read_jsonl(path):
        if rec.get("type") == "meta":
            continue
        pk = rec.get("person_key")
        if isinstance(pk, str) and pk:
            people[pk] = rec
    return people


def _slack_mention_for_person(person_key: str, people: dict[str, dict[str, Any]]) -> str:
    rec = people.get(person_key) or {}
    slack_id = rec.get("slack_user_id")
    if isinstance(slack_id, str) and slack_id.strip():
        return f"<@{slack_id.strip()}>"
    return f"`{person_key}`"


def _score_question(item: dict[str, Any], now: dt.datetime) -> float:
    category = item.get("category") if isinstance(item.get("category"), str) else "analysis"
    impact = float(item.get("impact") or 0) if isinstance(item.get("impact"), (int, float)) else CATEGORY_IMPACT.get(category, 0.6)

    confidence = item.get("confidence") if isinstance(item.get("confidence"), (int, float)) else 0.5
    confidence = max(0.0, min(1.0, float(confidence)))

    created_at = item.get("created_at") if isinstance(item.get("created_at"), str) else ""
    created_dt = _parse_iso(created_at) if created_at else None
    if created_dt is None:
        recency = 0.5
    else:
        age_hours = max(0.0, (now - created_dt).total_seconds() / 3600.0)
        recency = max(0.0, 1.0 - (age_hours / 72.0))  # 3-day window

    has_assignee = 1.0 if (isinstance(item.get("suggested_assignees"), list) and item.get("suggested_assignees")) else 0.0
    has_slack_target = 1.0 if item.get("slack_target") not in (None, "") else 0.0

    # Prefer: high impact, recent, low confidence, already-routed.
    return 2.0 * impact + 1.0 * recency + 1.0 * (1.0 - confidence) + 0.2 * has_assignee + 0.1 * has_slack_target


def _created_ts(item: dict[str, Any], now: dt.datetime) -> float:
    created_at = item.get("created_at") if isinstance(item.get("created_at"), str) else ""
    created_dt = _parse_iso(created_at) if created_at else None
    if created_dt is None:
        return 0.0
    # In case clocks are weird, clamp to <= now.
    return min(created_dt.timestamp(), now.timestamp())


def _write_text_if_changed(path: Path, content: str) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if existing == content:
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _sha1_hex(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _norm_rel(value: str) -> str:
    s = str(value).strip().replace("\\", "/")
    while s.startswith("./"):
        s = s[2:]
    return s.strip("/")


def _changed_prefixes_from_manifest(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        obj = _load_json(path)
    except Exception:
        return []
    if not isinstance(obj, dict):
        return []
    changed = obj.get("changed_directories")
    if not isinstance(changed, list):
        return []

    def _as_dir_prefix(rel: str) -> str:
        # Some manifests incorrectly contain file paths. Convert to parent-dir prefixes.
        s = _norm_rel(rel)
        try:
            if Path(s).suffix:
                s = _norm_rel(str(Path(s).parent))
        except Exception:
            pass
        return s

    out: list[str] = []
    for item in changed:
        if not isinstance(item, dict):
            continue
        p = item.get("path")
        if isinstance(p, str) and p.strip():
            out.append(_as_dir_prefix(p))
    out = sorted({p for p in out if p})
    return out


def _evidence_rel_paths(item: dict[str, Any]) -> list[str]:
    ev = item.get("evidence_paths") if isinstance(item.get("evidence_paths"), list) else []
    out: list[str] = []
    for p in ev:
        s = str(p).strip().replace("\\", "/")
        if s.startswith("data::"):
            s = s[len("data::") :].lstrip("/")
        elif s.startswith("data/"):
            s = s[len("data/") :].lstrip("/")
        out.append(_norm_rel(s))
    return [p for p in out if p]


def _question_matches_prefixes(item: dict[str, Any], prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    rels = _evidence_rel_paths(item)
    if not rels:
        return False
    for rel in rels:
        for pref in prefixes:
            if rel == pref or rel.startswith(pref + "/"):
                return True
    return False


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Select top open questions and format Slack-ready prompts (no API calls).")
    ap.add_argument("--queue", default="index/open_questions.jsonl", help="Questions queue JSONL")
    ap.add_argument("--people", default="index/people.jsonl", help="People index JSONL (for Slack mentions)")
    ap.add_argument("--out", default="out/slack_questions_to_ask.md", help="Output markdown file")
    ap.add_argument("--delta-manifest", default=None, help="Optional delta manifest; filter questions to today's changed directories")
    ap.add_argument("--max-questions", type=int, default=3, help="Max questions to include (default: 3)")
    ap.add_argument("--max-evidence", type=int, default=3, help="Max evidence paths per question (default: 3)")
    args = ap.parse_args(argv)

    cwd = Path.cwd().resolve()
    queue_path = (cwd / args.queue).resolve()
    people_path = (cwd / args.people).resolve()
    out_path = (cwd / args.out).resolve()

    people = _load_people(people_path) if people_path.exists() else {}

    prefixes: list[str] = []
    if args.delta_manifest:
        dm = Path(args.delta_manifest).expanduser()
        if not dm.is_absolute():
            dm = (cwd / dm).resolve()
        prefixes = _changed_prefixes_from_manifest(dm)

    records = _read_jsonl(queue_path)
    open_items: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("type") == "meta":
            continue
        if rec.get("status") != "open":
            continue
        if _question_matches_prefixes(rec, prefixes):
            open_items.append(rec)

    now = dt.datetime.now().astimezone()

    ranked = sorted(
        open_items,
        key=lambda r: (
            -_score_question(r, now),
            -_created_ts(r, now),
            str(r.get("id") or ""),
        ),
    )

    selected = ranked[: max(0, args.max_questions)]

    lines: list[str] = []
    lines.append(f"# Slack questions to ask ({dt.date.today().isoformat()})")
    lines.append("")
    stable_payload = json.dumps(
        [
            {
                "id": str(i.get("id") or ""),
                "category": str(i.get("category") or ""),
                "created_at": str(i.get("created_at") or ""),
            }
            for i in selected
        ],
        sort_keys=True,
    )
    prompt_id = _sha1_hex(stable_payload)[:12]
    lines.append(f"- prompt_id: `{prompt_id}`")
    lines.append(f"- open_questions_total: `{len(open_items)}`")
    lines.append(f"- selected: `{len(selected)}`")
    if prefixes:
        lines.append(f"- delta_manifest_filter: `{len(prefixes)}` dirs")
    lines.append("")

    if not selected:
        lines.append("_No open questions to ask right now._")
        lines.append("")
        content = "\n".join(lines)
        wrote = _write_text_if_changed(out_path, content + "\n")
        print(f"wrote: {wrote} -> {out_path}")
        return 0

    for idx, item in enumerate(selected, start=1):
        qid = item.get("id") if isinstance(item.get("id"), str) else ""
        category = item.get("category") if isinstance(item.get("category"), str) else "analysis"
        text = item.get("question_text") if isinstance(item.get("question_text"), str) else ""
        evidence = item.get("evidence_paths") if isinstance(item.get("evidence_paths"), list) else []
        evidence = [str(p) for p in evidence][: max(0, args.max_evidence)]
        assignees = item.get("suggested_assignees") if isinstance(item.get("suggested_assignees"), list) else []
        assignees = [str(a) for a in assignees if isinstance(a, str) and a.strip()]

        lines.append(f"## {idx}. {category} — `{qid}`")
        lines.append("")
        if assignees:
            mentions = ", ".join(_slack_mention_for_person(a, people) for a in assignees[:3])
            lines.append(f"- suggested: {mentions}")
        else:
            lines.append("- suggested: _(unassigned)_")
        if evidence:
            lines.append("- evidence: " + ", ".join(f"`{p}`" for p in evidence))
        lines.append("")
        lines.append(text.strip())
        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    wrote = _write_text_if_changed(out_path, content)
    print(f"wrote: {wrote} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
