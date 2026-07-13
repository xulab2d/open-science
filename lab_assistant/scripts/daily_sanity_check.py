#!/usr/bin/env python3
"""Daily operational sanity check for the OpenScience catalog daemon."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "lab_assistant" / "daemon" / "config.json"
DEFAULT_STATE = REPO_ROOT / "lab_assistant" / "daemon" / "state" / "catalog_state.json"
DEFAULT_REPORTS = REPO_ROOT / "lab_assistant" / "daemon" / "reports"
DEFAULT_HEALTH = REPO_ROOT / "lab_assistant" / "daemon" / "health"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def newest_json_report(reports_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    reports = sorted(reports_dir.glob("pulse_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in reports:
        try:
            return path, load_json(path, None)
        except json.JSONDecodeError:
            continue
    return None, None


def active_roots(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [root for root in config.get("roots", []) if root.get("active") is not False]


def recent_report_count(reports_dir: Path, since: datetime) -> int:
    count = 0
    for path in reports_dir.glob("pulse_*.json"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone()
        if mtime >= since:
            count += 1
    return count


def render_report(
    now: datetime,
    config: dict[str, Any],
    state: dict[str, Any],
    newest_path: Path | None,
    newest_report: dict[str, Any] | None,
    issues: list[str],
    warnings: list[str],
    recent_count: int,
) -> str:
    lines = [
        f"# Daily Sanity Check {now.strftime('%Y-%m-%d_%H%M%S_%Z')}",
        "",
        "Purpose: operational health check for the OpenScience catalog daemon.",
        "",
        "Status:",
        f"- Issues: {len(issues)}",
        f"- Warnings: {len(warnings)}",
        f"- Pulse reports in last 24h: {recent_count}",
        f"- Latest pulse report: `{newest_path.name if newest_path else 'none'}`",
        f"- Snapshot file count: {len(state.get('files', {}))}",
        "",
    ]

    lines.append("Watched roots:")
    for root in active_roots(config):
        path = Path(root["path"])
        status = "ok" if path.exists() else "missing"
        lines.append(f"- {root['name']}: {status}, `{path}`")
    lines.append("")

    if newest_report:
        summary = newest_report.get("summary", {})
        lines.append("Latest pulse summary:")
        lines.append(f"- Total changes: {summary.get('total_changes', 'unknown')}")
        lines.append(f"- High-value changes: {summary.get('high_value_changes', 'unknown')}")
        lines.append(f"- Projects touched: {summary.get('projects_touched', 'unknown')}")
        lines.append(f"- Sync backfill likely: {summary.get('sync_backfill_likely', 'unknown')}")
        lines.append(f"- Codex review recommended: {summary.get('codex_review_recommended', 'unknown')}")
        lines.append("")

    if issues:
        lines.append("Issues:")
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("")

    if warnings:
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    if not issues and not warnings:
        lines.append("No operational problems detected.")
        lines.append("")

    lines.append("Next action:")
    if issues:
        lines.append("- Fix operational issues before adding more automation.")
    elif warnings:
        lines.append("- Review warnings and tune cadence/config if they repeat.")
    else:
        lines.append("- Continue observing signal/noise during NAS backfill.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one OpenScience daily daemon sanity check.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--health-dir", type=Path, default=DEFAULT_HEALTH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(timezone.utc).astimezone()
    yesterday = now - timedelta(hours=24)

    config = load_json(args.config, {})
    state = load_json(args.state, {})
    newest_path, newest_report = newest_json_report(args.reports_dir)
    recent_count = recent_report_count(args.reports_dir, yesterday)

    issues: list[str] = []
    warnings: list[str] = []

    if not args.state.exists():
        issues.append(f"Missing state file `{args.state}`; run a baseline pulse.")
    elif len(state.get("files", {})) == 0:
        issues.append("Catalog state contains zero files; run an interactive baseline pulse or fix NAS permissions.")
    if not newest_path:
        issues.append(f"No pulse JSON reports found in `{args.reports_dir}`.")
    if recent_count == 0:
        issues.append("No pulse reports were produced in the last 24 hours.")
    elif recent_count < 12:
        warnings.append("Fewer than 12 pulse reports in the last 24 hours; daemon may not be running at the expected cadence.")
    elif recent_count > 80:
        warnings.append("More than 80 pulse reports in the last 24 hours; cadence may be too aggressive.")

    for root in active_roots(config):
        if not Path(root["path"]).exists():
            issues.append(f"Missing watched root for {root['name']}: `{root['path']}`")

    generated_at = parse_timestamp(state.get("generated_at", ""))
    if generated_at and generated_at < yesterday:
        issues.append("Catalog state is older than 24 hours.")

    scan_meta = state.get("scan_meta", [])
    for item in scan_meta:
        if item.get("truncated"):
            warnings.append(f"Scan truncated for {item.get('project_name', 'unknown project')}.")
        if item.get("errors"):
            issues.append(f"Scan errors recorded for {item.get('project_name', 'unknown project')}: {len(item['errors'])}")

    if newest_report:
        summary = newest_report.get("summary", {})
        if summary.get("scan_failed"):
            issues.append("Latest pulse scan failed; check NAS access for the launchd process.")
        if summary.get("sync_backfill_likely"):
            warnings.append("Latest pulse looks like sync backfill; avoid scientific interpretation of bulk deltas.")
        if summary.get("codex_review_recommended"):
            warnings.append("Latest pulse recommends Codex review; inspect or generate a focused prompt.")

    args.health_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.health_dir / f"daily_check_{now.strftime('%Y-%m-%d_%H%M%S_%Z')}.md"
    out_path.write_text(
        render_report(now, config, state, newest_path, newest_report, issues, warnings, recent_count),
        encoding="utf-8",
    )

    print(f"health_report: {out_path}")
    print(f"issues: {len(issues)}")
    print(f"warnings: {len(warnings)}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
