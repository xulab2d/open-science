#!/usr/bin/env python3
"""Generate the prompt for the mandatory daily OpenScience Codex overview."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "lab_assistant" / "daemon" / "config.json"
DEFAULT_REPORTS = REPO_ROOT / "lab_assistant" / "daemon" / "reports"
DEFAULT_HEALTH = REPO_ROOT / "lab_assistant" / "daemon" / "health"
DEFAULT_OUT = REPO_ROOT / "lab_assistant" / "daemon" / "out"
DEFAULT_CONTEXT_MANIFEST = REPO_ROOT / "lab_assistant" / "integrations" / "context_files.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def recent_files(path: Path, pattern: str, limit: int = 8) -> list[Path]:
    files = sorted(path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def recent_pulse_summaries(reports_dir: Path, since: datetime, limit: int = 60) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in sorted(reports_dir.glob("pulse_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone()
        if mtime < since:
            continue
        data = load_json(path, {})
        changes = data.get("changes", [])

        def change_priority(change: dict[str, Any]) -> int:
            rel = str(change.get("record", {}).get("relpath") or change.get("path", "")).lower()
            priority = int(change.get("score", 0))
            if "paperfigs" in rel or "figure" in rel:
                priority += 3
            if "hysteresis" in rel or "dualgate" in rel or "plot" in rel:
                priority += 2
            if rel.endswith((".pdf", ".png", ".jpg", ".tif", ".tiff")):
                priority += 1
            if "labonematlab" in rel or rel.endswith(("readme.txt", "contents.m", "ziaddpath.m", "bash.env")):
                priority -= 5
            return priority

        top_changes = [
            {
                "project": change.get("project_name") or change.get("project_id"),
                "rel": change.get("record", {}).get("relpath") or change.get("path"),
                "score": change.get("score", 0),
                "priority": change_priority(change),
                "reasons": change.get("reasons", []),
            }
            for change in sorted(
                changes,
                key=lambda item: (-change_priority(item), -int(item.get("score", 0)), str(item.get("record", {}).get("relpath") or item.get("path", ""))),
            )[:12]
        ]
        summaries.append(
            {
                "path": str(path),
                "timestamp": data.get("timestamp"),
                "summary": data.get("summary", {}),
                "top_changes": top_changes,
            }
        )
        if len(summaries) >= limit:
            break
    return list(reversed(summaries))


def read_text_truncated(path: Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"[unavailable: {exc}]"
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[truncated]"


def render_context_bundle(manifest_path: Path) -> str:
    manifest = load_json(manifest_path, {"always_include": [], "max_total_chars": 0})
    remaining = int(manifest.get("max_total_chars", 0))
    sections: list[str] = []
    for item in manifest.get("always_include", []):
        rel_path = item.get("path")
        if not rel_path or remaining <= 0:
            continue
        label = item.get("label", rel_path)
        max_chars = min(int(item.get("max_chars", remaining)), remaining)
        path = REPO_ROOT / rel_path
        body = read_text_truncated(path, max_chars)
        section = f"[{label} | {rel_path}]\n{body}"
        sections.append(section)
        remaining -= len(body)
    return "\n\n".join(sections)


def write_prompt(args: argparse.Namespace) -> Path:
    now = datetime.now(timezone.utc).astimezone()
    since = now - timedelta(hours=24)
    config = load_json(args.config, {})
    pulses = recent_pulse_summaries(args.reports_dir, since)
    health_reports = recent_files(args.health_dir, "daily_check_*.md", limit=3)
    context_bundle = render_context_bundle(args.context_manifest)

    prompt_path = args.out_dir / f"daily_overview_prompt_{now.strftime('%Y-%m-%d_%H%M%S_%Z')}.md"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    watched_roots = "\n".join(
        f"- {root['name']} ({root['project_id']}): `{root['path']}`"
        for root in config.get("roots", [])
    )
    pulse_lines = "\n".join(
        "- {timestamp}: changes={total}, high_value={high}, projects={projects}, "
        "scan_failed={scan_failed}, sync_backfill={sync}, review={review}, report=`{path}`".format(
            timestamp=pulse.get("timestamp", "unknown"),
            total=pulse.get("summary", {}).get("total_changes", "unknown"),
            high=pulse.get("summary", {}).get("high_value_changes", "unknown"),
            projects=pulse.get("summary", {}).get("projects_touched", "unknown"),
            scan_failed=pulse.get("summary", {}).get("scan_failed", "unknown"),
            sync=pulse.get("summary", {}).get("sync_backfill_likely", "unknown"),
            review=pulse.get("summary", {}).get("codex_review_recommended", "unknown"),
            path=pulse.get("path", "unknown"),
        )
        for pulse in pulses
    ) or "- No pulse reports found in the last 24 hours."
    significant_pulse_lines = []
    for pulse in pulses:
        summary = pulse.get("summary", {})
        if not summary.get("codex_review_recommended") and not summary.get("high_value_changes"):
            continue
        significant_pulse_lines.append(
            "- {timestamp}: report=`{path}`, high_value={high}, projects={projects}".format(
                timestamp=pulse.get("timestamp", "unknown"),
                path=pulse.get("path", "unknown"),
                high=summary.get("high_value_changes", "unknown"),
                projects=summary.get("projects_touched", "unknown"),
            )
        )
        for change in pulse.get("top_changes", []):
            reasons = ", ".join(change.get("reasons", []))
            significant_pulse_lines.append(
                "  - {project}: `{rel}`; score={score}; reasons={reasons}".format(
                    project=change.get("project") or "unknown project",
                    rel=change.get("rel") or "unknown path",
                    score=change.get("score", 0),
                    reasons=reasons or "none",
                )
            )
    significant_pulses = "\n".join(significant_pulse_lines) or "- No high-signal pulse details found in the last 24 hours."
    health_lines = "\n".join(f"- `{path}`" for path in health_reports) or "- No health reports found."

    prompt = f"""# Daily OpenScience Reasoned Overview

You are OpenScience, the Xu Lab Codex-based scientific assistant.

Task:
- Produce the daily forward-facing research overview for lab data/project cataloguing.
- This daily overview always runs, even when no individual catalog pulse crossed the review threshold.
- Audience: PI and lab members who want to know what changed scientifically in the last 24 hours.
- Be concise, evidence-first, and practical. Lead with research signal, not daemon mechanics.

Use these standing files first:
- `lab_assistant/skills/background-cataloguing.md`
- `lab_assistant/memory/project_pulse.md`
- `lab_assistant/context/projects/active_projects.md`
- `lab_assistant/context/interesting_features.md`
- `lab_assistant/context/plot_preferences.md`
- `lab_assistant/knowledge/INDEX.md`

Shared lab context bundle:
{context_bundle}

Watched roots:
{watched_roots}

Recent pulse summaries:
{pulse_lines}

High-signal pulse details:
{significant_pulses}

Recent health reports:
{health_lines}

Instructions:
1. Inspect the latest health report and relevant recent pulse reports.
2. Distinguish operational status from scientific activity.
3. During NAS Dropbox backfill, avoid treating broad file churn as new science.
4. If there are high-signal changes, map them to project context, inspect targeted NAS context when useful, and explain what likely changed scientifically.
5. Prefer plot-first communication when new data or new analysis exists. If useful plots already exist, convert/copy them into the OpenScience workspace when needed and embed them as Markdown images. If a quick plot can be generated safely from processed data, generate it in the OpenScience workspace and embed it. If plotting is not useful or not feasible, proceed text-only without forcing a figure.
6. Use bounded NAS inspection: prefer relevant scripts, filenames, small text notes, summary decks, processed figure names, and directory-local listings. Avoid broad `find` over large roots.
7. Do not open large raw `.mat`/binary files during the scheduled overview unless the specific task is clearly worth the cost and can complete quickly.
8. If there are no high-signal changes, say that plainly and focus on what remained stable, what is ready for follow-up, and any monitoring improvements.
9. If owner input would materially improve interpretation, use Slack as part of the loop. Send one concise clarification with enough context using `lab_assistant/integrations/slack/post_clarification.py`, unless the question is too speculative or low value.
10. For project-specific questions, DM the mapped project owners first. Use `#open-science` only when the answer should be shared lab-wide immediately, ownership is unclear, or a DM-first route is not appropriate.
11. If a durable lesson emerges, update the smallest canonical file (`memory/project_pulse.md`, `knowledge/projects/`, `knowledge/syntheses/`, or a skill). Do not update files just to look productive.
12. Do not mutate NAS data.
13. Keep the output forward-facing. Operational details belong after the research update and should be brief.

Output format:
- Write a concise, paper-like lab note for lab members: short headings, claim/evidence paragraphs, and compact bullets only where they improve scanability.
- Do not create a detached figure-link appendix. Interleave figures with the text that interprets them.
- Figures should be real Markdown image embeds (`![caption](path)`), not plain links to PDFs. Convert PDF figures to local PNG previews when needed.
- Use each figure immediately after the paragraph that introduces the result; follow it with one or two sentences explaining the takeaway and caveat.
- If you sent or recommend a Slack clarification, include it briefly in `## Recommended next actions` or `## Operational note`.
- End with `## Recommended next actions`, `## Operational note`, and `## Memory/skill updates`.
"""
    prompt_path.write_text(prompt, encoding="utf-8")
    return prompt_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write a daily Codex overview prompt.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--health-dir", type=Path, default=DEFAULT_HEALTH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--context-manifest", type=Path, default=DEFAULT_CONTEXT_MANIFEST)
    return parser.parse_args()


def main() -> int:
    print(write_prompt(parse_args()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
