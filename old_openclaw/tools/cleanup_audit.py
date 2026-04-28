#!/usr/bin/env python3
"""Safe, report-only workspace cleanup audit.

Scans the OpenClaw *workspace* for likely-vestigial files and writes a dated report.

Safety:
- Never deletes anything.
- Never touches `data/` (read-only cache).
- Focuses on obvious junk (editor backups, pycache, .DS_Store, etc.) and large/old generated artifacts.

Outputs:
- reports/cleanup_audit_YYYY-MM-DD.md
- out/cleanup_candidates_YYYY-MM-DD.json

"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


JUNK_BASENAMES = {".DS_Store", "Thumbs.db"}
JUNK_SUFFIXES = {"~", ".swp", ".swo", ".tmp", ".bak"}
JUNK_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

SAFE_EXCLUDE_TOPLEVEL = {"data"}  # never scan inside data/


@dataclass
class Finding:
    path: str
    kind: str
    confidence: str  # high|medium|low
    rationale: str
    size_bytes: int | None = None
    mtime: str | None = None


def iso_date() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def iso_mtime(p: Path) -> str | None:
    try:
        return dt.datetime.fromtimestamp(p.stat().st_mtime).astimezone().replace(microsecond=0).isoformat()
    except Exception:
        return None


def should_skip_dir(p: Path, workspace: Path) -> bool:
    try:
        rel0 = p.relative_to(workspace).parts
    except Exception:
        return True
    if not rel0:
        return False
    if rel0[0] in SAFE_EXCLUDE_TOPLEVEL:
        return True
    if p.name in JUNK_DIRS:
        return True
    return False


def scan(workspace: Path, max_findings: int) -> list[Finding]:
    findings: list[Finding] = []

    for root, dirs, files in os.walk(workspace):
        root_p = Path(root)
        # prune dirs
        pruned = []
        for d in list(dirs):
            dp = root_p / d
            if should_skip_dir(dp, workspace):
                pruned.append(d)
        for d in pruned:
            dirs.remove(d)

        for fn in files:
            p = root_p / fn
            try:
                rel = p.relative_to(workspace).as_posix()
            except Exception:
                continue

            if p.name in JUNK_BASENAMES:
                findings.append(Finding(rel, "junk", "high", f"Known junk file basename: {p.name}", size_bytes=p.stat().st_size, mtime=iso_mtime(p)))
            elif any(p.name.endswith(suf) for suf in JUNK_SUFFIXES):
                findings.append(Finding(rel, "junk", "high", f"Editor/temporary suffix match ({', '.join(sorted(JUNK_SUFFIXES))})", size_bytes=p.stat().st_size, mtime=iso_mtime(p)))
            elif p.suffix == ".asv":
                findings.append(Finding(rel, "junk", "medium", "MATLAB autosave (.asv) — usually safe to delete if corresponding .m exists", size_bytes=p.stat().st_size, mtime=iso_mtime(p)))

            if len(findings) >= max_findings:
                return findings

    return findings


def write_report(workspace: Path, findings: list[Finding]) -> tuple[Path, Path]:
    date = iso_date()
    reports_dir = workspace / "reports"
    out_dir = workspace / "out"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"cleanup_audit_{date}.md"
    json_path = out_dir / f"cleanup_candidates_{date}.json"

    # json
    json_path.write_text(json.dumps([asdict(f) for f in findings], indent=2) + "\n", encoding="utf-8")

    # markdown
    lines = []
    lines.append(f"# Cleanup audit (report-only) — {date}\n")
    lines.append(f"Workspace: `{workspace}`")
    lines.append("\nSafety: report-only. No deletions performed. `data/` excluded.")
    lines.append(f"\nFindings: `{len(findings)}`")

    if findings:
        lines.append("\n## Candidates")
        for f in findings:
            sz = f.size_bytes
            sz_s = f"{sz} B" if isinstance(sz, int) else "(unknown size)"
            lines.append(f"- `{f.path}` — {f.kind} ({f.confidence}) — {f.rationale} — {sz_s} — mtime: {f.mtime or 'unknown'}")

    lines.append("\n## Suggested next step")
    lines.append("- Ask Isaac for approval to delete high-confidence junk categories (or keep report-only).")
    lines.append("- If approved, implement a *separate* delete script that only deletes the approved categories.")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return report_path, json_path


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Safe, report-only cleanup audit for OpenClaw workspace")
    ap.add_argument("--workspace", default=".", help="Workspace root (default: .)")
    ap.add_argument("--max-findings", type=int, default=5000)
    args = ap.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    findings = scan(workspace, max_findings=int(args.max_findings))
    report_path, json_path = write_report(workspace, findings)

    print(f"report: {report_path}")
    print(f"json: {json_path}")
    print(f"findings: {len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
