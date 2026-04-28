#!/usr/bin/env python3
"""Nightly maintenance review (directive coherence + codebase hygiene).

Intent: lightweight, rotating review of the workspace to catch drift/contradictions/vestigial code.

Triggering: meant to be called from the normal heartbeat runner when local time >= 02:00
and the maintenance for the local day hasn't run yet.

Safety:
- No deletions.
- Never touch `data/`.
- Writes a short report, and updates a gate state file.

State:
- state/nightly_maintenance_state.json

Outputs:
- reports/nightly_maintenance_YYYY-MM-DD.md

"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path


WORKSPACE_DEFAULT = Path(__file__).resolve().parents[1]
STATE_PATH_DEFAULT = Path("state/nightly_maintenance_state.json")

KEY_DIRECTIVES = [
    "HEARTBEAT.md",
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "USER.md",
    "OPERATING_MODEL.md",
]


def _now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def _today_local_str() -> str:
    return _now_local().date().isoformat()


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_head(p: Path, max_lines: int = 80) -> str:
    if not p.exists():
        return "[MISSING]"
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[:max_lines])


def run(workspace: Path, state_path: Path, rotate_seed: str | None = None) -> dict:
    """Run a short maintenance pass.

    Returns a dict summary including:
    - ran: bool
    - action_needed: bool
    - report_path: str
    - notes: list[str]
    """

    now = _now_local()
    today = now.date().isoformat()

    st = _load_json(state_path)
    if st.get("last_run_date") == today:
        return {"ran": False, "reason": "already_ran_today", "action_needed": False, "report_path": st.get("last_report")}

    # --- 1) Directive coherence quick scan ---
    notes: list[str] = []
    present = []
    missing = []
    for rel in KEY_DIRECTIVES:
        p = workspace / rel
        if p.exists():
            present.append(rel)
        else:
            missing.append(rel)
    if missing:
        notes.append(f"Missing directive files: {', '.join(missing)}")

    # Basic drift signals (very light heuristics)
    hb = _read_head(workspace / "HEARTBEAT.md")
    if "Route questions to experts" not in hb and "DM-first" not in hb:
        notes.append("HEARTBEAT.md may be out of date vs current DM-first routing expectations.")

    # --- 2) Rotating codebase slice: pick one tools/ file by date hash ---
    tools_dir = workspace / "tools"
    candidate = None
    if tools_dir.exists():
        py_files = sorted([p for p in tools_dir.glob("*.py") if p.is_file()])
        if py_files:
            idx = (hash(rotate_seed or today) % len(py_files))
            candidate = py_files[idx]
            head = _read_head(candidate, max_lines=120)
            # very simple flags
            if "TODO" in head or "FIXME" in head:
                notes.append(f"Check TODO/FIXME in {candidate.name} (rotating pick).")

    # --- 3) Write report ---
    reports_dir = workspace / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"nightly_maintenance_{today}.md"

    lines: list[str] = []
    lines.append(f"# Nightly maintenance — {today}\n")
    lines.append(f"Ran at: `{now.replace(microsecond=0).isoformat()}`")
    lines.append(f"Workspace: `{workspace}`\n")

    lines.append("## Scope")
    lines.append("- Directive coherence quick scan")
    lines.append("- Rotating codebase slice (one file per night)")
    lines.append("- Safety: report-only (no deletes), data/ untouched\n")

    lines.append("## Directive files")
    lines.append("- Present: " + (", ".join(f"`{x}`" for x in present) if present else "(none)"))
    lines.append("- Missing: " + (", ".join(f"`{x}`" for x in missing) if missing else "(none)"))

    if candidate:
        lines.append("\n## Rotating code slice")
        lines.append(f"- Selected: `{candidate.relative_to(workspace).as_posix()}`")

    lines.append("\n## Notes")
    if notes:
        for n in notes:
            lines.append(f"- {n}")
    else:
        lines.append("- No issues detected in this short pass.")

    action_needed = bool(notes)
    lines.append("\n## Action needed")
    lines.append(f"- `{action_needed}`")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    st["last_run_date"] = today
    st["last_run_ts"] = now.replace(microsecond=0).isoformat()
    st["last_report"] = str(report_path)
    st["last_action_needed"] = action_needed
    _write_json(state_path, st)

    return {
        "ran": True,
        "action_needed": action_needed,
        "report_path": str(report_path),
        "notes": notes,
        "rotating_file": str(candidate) if candidate else None,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Nightly maintenance (report-only)")
    ap.add_argument("--workspace", default=str(WORKSPACE_DEFAULT), help="Workspace root")
    ap.add_argument("--state", default=str(STATE_PATH_DEFAULT), help="State file path")
    ap.add_argument("--rotate-seed", default=None, help="Optional stable seed for rotation")
    args = ap.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    state_path = (workspace / args.state).resolve() if not Path(args.state).is_absolute() else Path(args.state).resolve()

    res = run(workspace, state_path, rotate_seed=args.rotate_seed)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(os.sys.argv[1:]))
