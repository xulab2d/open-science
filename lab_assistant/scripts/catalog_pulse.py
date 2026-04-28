#!/usr/bin/env python3
"""Deterministic NAS catalog pulse for OpenScience.

The scanner records file metadata, computes compact deltas, maps them to active
projects, and writes Markdown/JSON reports. It intentionally does not inspect
raw data payloads or mutate NAS files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "lab_assistant" / "daemon" / "config.json"
DEFAULT_STATE = REPO_ROOT / "lab_assistant" / "daemon" / "state" / "catalog_state.json"
DEFAULT_REPORTS = REPO_ROOT / "lab_assistant" / "daemon" / "reports"
DEFAULT_OUT = REPO_ROOT / "lab_assistant" / "daemon" / "out"


@dataclass(frozen=True)
class Change:
    kind: str
    path: str
    project_id: str
    project_name: str
    record: dict[str, Any]
    previous: dict[str, Any] | None
    score: int
    reasons: list[str]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def rel_display(path: str, root: str) -> str:
    try:
        return str(Path(path).relative_to(root))
    except ValueError:
        return path


def should_ignore(path: Path, config: dict[str, Any]) -> bool:
    ignored_names = set(config.get("ignore_names", []))
    ignored_suffixes = set(s.lower() for s in config.get("ignore_suffixes", []))
    if any(part in ignored_names for part in path.parts):
        return True
    return path.suffix.lower() in ignored_suffixes


def scan_root(root_cfg: dict[str, Any], config: dict[str, Any], max_files: int) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(root_cfg["path"])
    snapshot: dict[str, Any] = {}
    meta = {
        "root": str(root),
        "project_id": root_cfg["project_id"],
        "project_name": root_cfg["name"],
        "exists": root.exists(),
        "truncated": False,
        "files_seen": 0,
        "errors": [],
    }
    if not root.exists():
        return snapshot, meta

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    if should_ignore(path, config):
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(path)
                            continue
                        if not entry.is_file(follow_symlinks=False):
                            continue
                        stat = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        meta["errors"].append(f"{path}: {exc}")
                        continue

                    snapshot[str(path)] = {
                        "size": stat.st_size,
                        "mtime": int(stat.st_mtime),
                        "suffix": path.suffix.lower(),
                        "project_id": root_cfg["project_id"],
                        "project_name": root_cfg["name"],
                        "root": str(root),
                        "relpath": rel_display(str(path), str(root)),
                    }
                    meta["files_seen"] += 1
                    if meta["files_seen"] >= max_files:
                        meta["truncated"] = True
                        return snapshot, meta
        except OSError as exc:
            meta["errors"].append(f"{current}: {exc}")

    return snapshot, meta


def score_change(path: str, record: dict[str, Any], config: dict[str, Any], kind: str) -> tuple[int, list[str]]:
    suffix = record.get("suffix", "").lower()
    lower_path = path.lower()
    high_suffixes = set(s.lower() for s in config.get("high_value_suffixes", []))
    medium_suffixes = set(s.lower() for s in config.get("medium_value_suffixes", []))
    high_terms = [t.lower() for t in config.get("high_value_terms", [])]
    low_terms = [t.lower() for t in config.get("low_value_terms", [])]

    score = 0
    reasons: list[str] = []
    if kind == "deleted":
        score -= 1
        reasons.append("deleted")
    if suffix in high_suffixes:
        score += 3
        reasons.append(f"high-value suffix {suffix}")
    elif suffix in medium_suffixes:
        score += 1
        reasons.append(f"medium-value suffix {suffix}")
    for term in high_terms:
        if term in lower_path:
            score += 1
            reasons.append(f"term:{term}")
    for term in low_terms:
        if term in lower_path:
            score -= 2
            reasons.append(f"low-signal term:{term}")
    if record.get("size", 0) == 0:
        score -= 1
        reasons.append("empty file")
    if record.get("size", 0) > 2_000_000_000:
        score -= 1
        reasons.append("large raw-like file")
    return score, reasons or ["metadata change"]


def diff_snapshots(old: dict[str, Any], new: dict[str, Any], config: dict[str, Any]) -> list[Change]:
    changes: list[Change] = []
    old_files = old.get("files", {})
    new_files = new.get("files", {})

    for path, record in new_files.items():
        previous = old_files.get(path)
        if previous is None:
            kind = "new"
        elif previous.get("size") != record.get("size") or previous.get("mtime") != record.get("mtime"):
            kind = "modified"
        else:
            continue
        score, reasons = score_change(path, record, config, kind)
        changes.append(Change(kind, path, record["project_id"], record["project_name"], record, previous, score, reasons))

    for path, previous in old_files.items():
        if path in new_files:
            continue
        score, reasons = score_change(path, previous, config, "deleted")
        changes.append(Change("deleted", path, previous["project_id"], previous["project_name"], previous, previous, score, reasons))

    changes.sort(key=lambda c: (c.project_name, -c.score, c.path))
    return changes


def detect_sync_backfill(changes: list[Change], config: dict[str, Any]) -> tuple[bool, list[str]]:
    trigger = config.get("analysis_trigger", {})
    total_threshold = int(trigger.get("sync_backfill_total_changes", 300))
    project_threshold = int(trigger.get("sync_backfill_project_count", 4))
    project_count = len({c.project_id for c in changes})
    new_count = sum(1 for c in changes if c.kind == "new")
    reasons: list[str] = []
    if len(changes) >= total_threshold:
        reasons.append(f"{len(changes)} total changes")
    if project_count >= project_threshold:
        reasons.append(f"{project_count} projects touched")
    if new_count >= total_threshold:
        reasons.append(f"{new_count} new files")
    return bool(config.get("sync_grace_mode", True) and reasons), reasons


def group_changes(changes: list[Change]) -> dict[str, list[Change]]:
    grouped: dict[str, list[Change]] = {}
    for change in changes:
        grouped.setdefault(change.project_name, []).append(change)
    return grouped


def summarize(changes: list[Change], config: dict[str, Any], baseline_only: bool) -> dict[str, Any]:
    high_value = [c for c in changes if c.score >= 3 and c.kind != "deleted"]
    sync_like, sync_reasons = detect_sync_backfill(changes, config)
    trigger = config.get("analysis_trigger", {})
    needs_review = (
        not baseline_only
        and not sync_like
        and (
            len(high_value) >= int(trigger.get("min_high_value_changes", 3))
            or len(changes) >= int(trigger.get("min_total_changes", 25))
        )
    )
    return {
        "total_changes": len(changes),
        "high_value_changes": len(high_value),
        "projects_touched": len({c.project_id for c in changes}),
        "scan_failed": False,
        "state_preserved": False,
        "sync_backfill_likely": sync_like,
        "sync_backfill_reasons": sync_reasons,
        "codex_review_recommended": needs_review,
    }


def scan_failed(scan_meta: list[dict[str, Any]], previous_state: dict[str, Any], new_files: dict[str, Any]) -> bool:
    existing_roots = [m for m in scan_meta if m.get("exists")]
    errored_roots = [m for m in existing_roots if m.get("errors") and m.get("files_seen", 0) == 0]
    previous_files = previous_state.get("files", {})
    if not existing_roots:
        return True
    if len(errored_roots) == len(existing_roots):
        return True
    if previous_files and not new_files:
        return True
    return False


def render_markdown(
    timestamp: str,
    baseline_only: bool,
    summary: dict[str, Any],
    changes: list[Change],
    scan_meta: list[dict[str, Any]],
    config: dict[str, Any],
) -> str:
    lines = [
        f"# Catalog Pulse {timestamp}",
        "",
        f"- Mode: {'baseline only' if baseline_only else 'delta scan'}",
        f"- Total changes: {summary['total_changes']}",
        f"- High-value changes: {summary['high_value_changes']}",
        f"- Projects touched: {summary['projects_touched']}",
        f"- Scan failed: {summary['scan_failed']}",
        f"- Previous state preserved: {summary['state_preserved']}",
        f"- Sync backfill likely: {summary['sync_backfill_likely']}",
        f"- Codex review recommended: {summary['codex_review_recommended']}",
        "",
    ]
    if summary["scan_failed"]:
        lines.append("Operational issue:")
        lines.append("- Scan failed or returned an unsafe empty snapshot. No file deltas were interpreted.")
        if summary["state_preserved"]:
            lines.append("- Previous scanner state was preserved.")
        else:
            lines.append("- No previous scanner state was available to preserve.")
        lines.append("")

    if summary["sync_backfill_reasons"]:
        lines.append("Sync-backfill signals:")
        for reason in summary["sync_backfill_reasons"]:
            lines.append(f"- {reason}")
        lines.append("")

    missing = [m for m in scan_meta if not m["exists"]]
    errored = [m for m in scan_meta if m.get("errors")]
    truncated = [m for m in scan_meta if m["truncated"]]
    if missing or errored or truncated:
        lines.append("Scan caveats:")
        for item in missing:
            lines.append(f"- Missing root: {item['project_name']} `{item['root']}`")
        for item in errored:
            lines.append(f"- Scan errors for {item['project_name']}: {len(item['errors'])}")
        for item in truncated:
            lines.append(f"- Truncated root: {item['project_name']} after {item['files_seen']} files")
        lines.append("")

    lines.append("Scan coverage:")
    for item in scan_meta:
        status = "missing" if not item["exists"] else "ok"
        if item.get("errors"):
            status = "error"
        if item["truncated"]:
            status = "truncated"
        lines.append(f"- {item['project_name']}: {item['files_seen']} files, {status}")
    lines.append("")

    if baseline_only:
        lines.append("Baseline established. Changes were intentionally not interpreted.")
        lines.append("")
        return "\n".join(lines)

    max_items = int(config.get("max_report_items", 80))
    grouped = group_changes(changes)
    for project_name, project_changes in grouped.items():
        lines.append(f"## {project_name}")
        counts = {
            "new": sum(1 for c in project_changes if c.kind == "new"),
            "modified": sum(1 for c in project_changes if c.kind == "modified"),
            "deleted": sum(1 for c in project_changes if c.kind == "deleted"),
        }
        lines.append(f"- Counts: {counts['new']} new, {counts['modified']} modified, {counts['deleted']} deleted")
        shown = 0
        for change in sorted(project_changes, key=lambda c: (-c.score, c.kind, c.path)):
            if shown >= max_items:
                lines.append(f"- ... {len(project_changes) - shown} more changes omitted")
                break
            relpath = change.record.get("relpath", change.path)
            reason = "; ".join(change.reasons[:4])
            lines.append(f"- {change.kind}, score {change.score}: `{relpath}` ({reason})")
            shown += 1
        lines.append("")

    if not changes:
        lines.append("No file metadata changes detected in watched roots.")
        lines.append("")

    return "\n".join(lines)


def render_codex_prompt(report_path: Path, summary: dict[str, Any]) -> str:
    return f"""# OpenScience Catalog Review Request

Review the catalog pulse report:
- `{report_path}`

Use:
- `lab_assistant/skills/background-cataloguing.md`
- `lab_assistant/context/projects/active_projects.md`
- relevant `lab_assistant/knowledge/projects/*.md`
- `lab_assistant/context/interesting_features.md`
- `lab_assistant/context/plot_preferences.md`

Summary:
- Total changes: {summary['total_changes']}
- High-value changes: {summary['high_value_changes']}
- Sync backfill likely: {summary['sync_backfill_likely']}

Task:
1. Decide whether any changes deserve scientific follow-up.
2. Inspect only the most relevant files needed to answer that.
3. Update project knowledge or `memory/project_pulse.md` only if there is a durable lesson.
4. If the pulse is noisy, suggest a targeted config/scoring improvement.
"""


def append_log(reports_dir: Path, timestamp: str, summary: dict[str, Any], baseline_only: bool, md_path: Path) -> None:
    day = timestamp[:10]
    log_path = reports_dir / f"pulse_log_{day}.md"
    line = (
        f"- {timestamp}: mode={'baseline' if baseline_only else 'delta'}, "
        f"changes={summary['total_changes']}, high_value={summary['high_value_changes']}, "
        f"projects={summary['projects_touched']}, sync_backfill={summary['sync_backfill_likely']}, "
        f"review={summary['codex_review_recommended']}, report={md_path.name}\n"
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one OpenScience catalog pulse.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--baseline-only", action="store_true", help="Update state without interpreting all existing files as new.")
    parser.add_argument("--write-codex-prompt", action="store_true", help="Write a focused review prompt when review is recommended.")
    parser.add_argument("--max-files-per-root", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_json(args.config, {})
    max_files = args.max_files_per_root or int(config.get("max_files_per_root", 20000))
    timestamp_dt = datetime.now(timezone.utc).astimezone()
    timestamp = timestamp_dt.strftime("%Y-%m-%d_%H%M%S_%Z")

    files: dict[str, Any] = {}
    scan_meta: list[dict[str, Any]] = []
    for root_cfg in config.get("roots", []):
        root_snapshot, meta = scan_root(root_cfg, config, max_files)
        files.update(root_snapshot)
        scan_meta.append(meta)

    previous_state = load_json(args.state, {"files": {}})
    new_state = {
        "generated_at": timestamp_dt.isoformat(),
        "config_path": str(args.config),
        "files": files,
        "scan_meta": scan_meta,
    }
    failed_scan = scan_failed(scan_meta, previous_state, files)
    if failed_scan:
        changes = []
    elif args.baseline_only or not previous_state.get("files"):
        changes = []
    else:
        changes = diff_snapshots(previous_state, new_state, config)
    summary = summarize(changes, config, args.baseline_only)
    summary["scan_failed"] = failed_scan
    summary["state_preserved"] = bool(failed_scan and previous_state.get("files"))
    if failed_scan:
        summary["codex_review_recommended"] = False

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    stem = f"pulse_{timestamp}"
    md_path = args.reports_dir / f"{stem}.md"
    json_path = args.reports_dir / f"{stem}.json"
    md_text = render_markdown(timestamp, args.baseline_only, summary, changes, scan_meta, config)
    md_path.write_text(md_text, encoding="utf-8")
    save_json_atomic(
        json_path,
        {
            "timestamp": timestamp_dt.isoformat(),
            "baseline_only": args.baseline_only,
            "summary": summary,
            "scan_meta": scan_meta,
            "changes": [
                {
                    "kind": c.kind,
                    "path": c.path,
                    "project_id": c.project_id,
                    "project_name": c.project_name,
                    "score": c.score,
                    "reasons": c.reasons,
                    "record": c.record,
                }
                for c in changes
            ],
        },
    )
    if not failed_scan:
        save_json_atomic(args.state, new_state)
    append_log(args.reports_dir, timestamp, summary, args.baseline_only, md_path)

    prompt_path = None
    if args.write_codex_prompt and summary["codex_review_recommended"]:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = args.out_dir / f"codex_review_{timestamp}.md"
        prompt_path.write_text(render_codex_prompt(md_path, summary), encoding="utf-8")

    print(f"report: {md_path}")
    print(f"json: {json_path}")
    print(f"changes: {summary['total_changes']}")
    print(f"codex_review_recommended: {summary['codex_review_recommended']}")
    if prompt_path:
        print(f"codex_prompt: {prompt_path}")
    return 2 if failed_scan else 0


if __name__ == "__main__":
    sys.exit(main())
