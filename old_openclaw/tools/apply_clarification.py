#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from pathlib import Path
from typing import Any


ALIAS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(?P<term>[A-Z][A-Z0-9_/-]{1,24})\s*(?:=|->)\s*(?P<meaning>.+?)\s*$"),
    re.compile(r"^\s*(?P<term>[A-Z][A-Z0-9_/-]{1,24})\s+stands\s+for\s+(?P<meaning>.+?)\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?P<term>[A-Z][A-Z0-9_/-]{1,24})\s+means\s+(?P<meaning>.+?)\s*$", re.IGNORECASE),
]


def _iso_now() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _today_str() -> str:
    return dt.date.today().isoformat()


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


def _append_jsonl(path: Path, records: list[dict[str, Any]], *, dry_run: bool) -> int:
    if not records:
        return 0
    if dry_run:
        return len(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    return len(records)


def _write_text_if_changed(path: Path, content: str, *, dry_run: bool) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if existing == content:
            return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _normalize_paths(paths: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for p in paths:
        s = str(p).strip().replace(os.sep, "/")
        if s.startswith("./"):
            s = s[2:]
        s = s.rstrip("/")
        if not s:
            continue
        if s not in seen:
            out.append(s)
            seen.add(s)
    out.sort()
    return out


def _parse_evidence(value: str | None) -> list[str]:
    if not value:
        return []
    parts = [p.strip() for p in re.split(r"[,\n]+", value) if p.strip()]
    return _normalize_paths(parts)


def _extract_alias_updates(resolution_text: str) -> list[dict[str, str]]:
    """
    Conservative: only accept obvious term->meaning mappings.
    Returns list of {canonical_term, meaning}.
    """
    updates: list[dict[str, str]] = []
    for line in resolution_text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("alias:"):
            s = s.split(":", 1)[1].strip()
        for pat in ALIAS_PATTERNS:
            m = pat.match(s)
            if not m:
                continue
            term = m.group("term").strip()
            meaning = m.group("meaning").strip()
            if term and meaning:
                updates.append({"canonical_term": term, "meaning": meaning})
            break
    # Dedupe by term, keep first occurrence.
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for u in updates:
        t = u["canonical_term"]
        if t in seen:
            continue
        seen.add(t)
        out.append(u)
    return out


def _extract_people_updates(resolution_text: str) -> list[dict[str, Any]]:
    """
    Opt-in format (to avoid guessing):

      person: person_key | Display Name | U123ABC... | domains=PL,RMCD | notes=...

    Only person_key is required.
    """
    updates: list[dict[str, Any]] = []
    for line in resolution_text.splitlines():
        raw = line.strip()
        if not raw.lower().startswith("person:"):
            continue
        payload = raw.split(":", 1)[1].strip()
        parts = [p.strip() for p in payload.split("|")]
        if not parts or not parts[0]:
            continue
        person_key = parts[0]
        rec: dict[str, Any] = {"person_key": person_key}
        if len(parts) >= 2 and parts[1]:
            rec["display_name"] = parts[1]
        if len(parts) >= 3 and parts[2]:
            rec["slack_user_id"] = parts[2]
        domains: list[str] = []
        notes: str | None = None
        for p in parts[3:]:
            if p.lower().startswith("domains="):
                domains = [d.strip() for d in p.split("=", 1)[1].split(",") if d.strip()]
            elif p.lower().startswith("notes="):
                notes = p.split("=", 1)[1].strip()
        if domains:
            rec["domains"] = domains
        if notes:
            rec["notes"] = notes
        updates.append(rec)
    # Dedupe by person_key, keep first.
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for u in updates:
        pk = str(u.get("person_key") or "")
        if not pk or pk in seen:
            continue
        seen.add(pk)
        out.append(u)
    return out


def _load_latest_alias_meanings(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for rec in _read_jsonl(path):
        if rec.get("type") == "meta":
            continue
        term = rec.get("canonical_term")
        if isinstance(term, str) and term:
            latest[term] = rec
    return latest


def _load_latest_people(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for rec in _read_jsonl(path):
        if rec.get("type") == "meta":
            continue
        pk = rec.get("person_key")
        if isinstance(pk, str) and pk:
            latest[pk] = rec
    return latest


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Apply a Slack clarification to local OpenClaw indices (no network).")
    ap.add_argument("--question-id", required=True, help="Question id (q_...) in index/open_questions.jsonl")
    ap.add_argument("--resolution", required=True, help="Resolution text to store")
    ap.add_argument("--resolver", required=True, help="Who resolved it (person_key or free text)")
    ap.add_argument("--evidence", default=None, help="Optional evidence paths (comma/newline separated)")
    ap.add_argument("--queue", default="index/open_questions.jsonl", help="Questions queue JSONL")
    ap.add_argument("--aliases", default="index/aliases.jsonl", help="Aliases JSONL")
    ap.add_argument("--people", default="index/people.jsonl", help="People JSONL")
    ap.add_argument("--reports", default="reports", help="Reports directory")
    ap.add_argument("--dry-run", action="store_true", help="Do not write; print what would change")
    args = ap.parse_args(argv)

    cwd = Path.cwd().resolve()
    queue_path = (cwd / args.queue).resolve()
    aliases_path = (cwd / args.aliases).resolve()
    people_path = (cwd / args.people).resolve()
    reports_dir = (cwd / args.reports).resolve()

    qid = args.question_id.strip()
    resolution = args.resolution.strip()
    resolver = args.resolver.strip()
    extra_evidence = _parse_evidence(args.evidence)

    now = _iso_now()
    today = _today_str()

    # Update the queue item in-place.
    raw = _read_jsonl(queue_path)
    meta: dict[str, Any] | None = None
    items: list[dict[str, Any]] = []
    for rec in raw:
        if rec.get("type") == "meta" and meta is None:
            meta = rec
        else:
            items.append(rec)
    if meta is None:
        meta = {"type": "meta", "schema_version": 1, "created_at": now, "notes": "Structured open-questions queue"}

    target: dict[str, Any] | None = None
    for rec in items:
        if rec.get("id") == qid:
            target = rec
            break
    if target is None:
        raise SystemExit(f"Question id not found in queue: {qid}")

    queue_changed = False
    if target.get("status") != "resolved":
        target["status"] = "resolved"
        queue_changed = True
    if target.get("resolution") != resolution:
        target["resolution"] = resolution
        queue_changed = True
    if target.get("resolved_at") in (None, ""):
        target["resolved_at"] = now
        queue_changed = True
    if target.get("resolved_by") in (None, ""):
        target["resolved_by"] = resolver
        queue_changed = True

    # Keep evidence_paths stable (do not break dedupe), but if missing/invalid, set it.
    if not isinstance(target.get("evidence_paths"), list) and extra_evidence:
        target["evidence_paths"] = extra_evidence
        queue_changed = True

    # Conservative alias/person updates (append-only).
    alias_updates = _extract_alias_updates(resolution)
    people_updates = _extract_people_updates(resolution)

    alias_appended: list[dict[str, Any]] = []
    if alias_updates:
        existing_aliases = _load_latest_alias_meanings(aliases_path) if aliases_path.exists() else {}
        for u in alias_updates:
            term = u["canonical_term"]
            meaning = u["meaning"]
            prev = existing_aliases.get(term, {})
            prev_meaning = prev.get("meaning") if isinstance(prev.get("meaning"), str) else ""
            if prev_meaning and prev_meaning.strip():
                # Don't overwrite a meaning; log only.
                continue
            alias_appended.append(
                {
                    "canonical_term": term,
                    "observed_terms": [term],
                    "meaning": meaning,
                    "confidence": 0.8,
                    "evidence_paths": extra_evidence or (target.get("evidence_paths") or []),
                    "confirmed_by": resolver,
                    "notes": f"From clarification of {qid} at {now}.",
                    "recorded_at": now,
                }
            )

    people_appended: list[dict[str, Any]] = []
    if people_updates:
        existing_people = _load_latest_people(people_path) if people_path.exists() else {}
        for u in people_updates:
            pk = str(u.get("person_key") or "").strip()
            if not pk:
                continue
            prev = existing_people.get(pk, {})
            # Conservative: only append if new, or if previous record is missing slack_user_id/display_name.
            should_append = pk not in existing_people
            if not should_append:
                if u.get("slack_user_id") and not prev.get("slack_user_id"):
                    should_append = True
                if u.get("display_name") and not prev.get("display_name"):
                    should_append = True
            if not should_append:
                continue
            rec = {
                "person_key": pk,
                "display_name": u.get("display_name") or prev.get("display_name") or pk,
                "slack_user_id": u.get("slack_user_id") or prev.get("slack_user_id"),
                "domains": u.get("domains") or prev.get("domains") or [],
                "notes": u.get("notes") or prev.get("notes") or "",
                "confidence": 0.7,
                "recorded_at": now,
            }
            people_appended.append(rec)

    # Write queue file if changed.
    queue_wrote = False
    if queue_changed:
        lines = [json.dumps(meta, sort_keys=True)]
        for rec in items:
            lines.append(json.dumps(rec, sort_keys=True))
        content = "\n".join(lines) + "\n"
        queue_wrote = _write_text_if_changed(queue_path, content, dry_run=args.dry_run)

    aliases_added = _append_jsonl(aliases_path, alias_appended, dry_run=args.dry_run)
    people_added = _append_jsonl(people_path, people_appended, dry_run=args.dry_run)

    # Audit log
    log_path = reports_dir / f"slack_resolution_log_{today}.md"
    audit_lines: list[str] = []
    audit_lines.append(f"## {now}")
    audit_lines.append("")
    audit_lines.append(f"- question_id: `{qid}`")
    audit_lines.append(f"- resolver: `{resolver}`")
    audit_lines.append(f"- queue_updated: `{queue_wrote}`")
    audit_lines.append(f"- aliases_appended: `{aliases_added}`")
    audit_lines.append(f"- people_appended: `{people_added}`")
    if extra_evidence:
        audit_lines.append(f"- extra_evidence: " + ", ".join(f"`{p}`" for p in extra_evidence))
    audit_lines.append("")
    audit_lines.append("### Resolution")
    audit_lines.append("")
    audit_lines.append("```")
    audit_lines.append(resolution)
    audit_lines.append("```")
    audit_lines.append("")
    audit = "\n".join(audit_lines)

    changed_any = queue_wrote or aliases_added > 0 or people_added > 0

    if args.dry_run:
        print(audit)
    else:
        if changed_any:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.write_text("# Slack resolution log\n\n", encoding="utf-8")
            with log_path.open("a", encoding="utf-8") as f:
                f.write(audit + "\n")

    print(f"queue_wrote: {queue_wrote} -> {queue_path}")
    print(f"aliases_added: {aliases_added} -> {aliases_path}")
    print(f"people_added: {people_added} -> {people_path}")
    print(f"audit_log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
