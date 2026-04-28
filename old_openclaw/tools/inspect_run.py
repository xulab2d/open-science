#!/usr/bin/env python3
"""
inspect_run.py — Compact status snapshot of active monitoring runs.

Designed for the LLM to read in <200 tokens. Shows:
  - Run identity, age, file count, gap since last file
  - Quality distribution (clean / warnings / errors)
  - Recent flags (deduped with counts)
  - Trend of key physics metrics over last N files

Usage:
  python3 tools/inspect_run.py                    # all active runs
  python3 tools/inspect_run.py --run-id <id>      # one run
  python3 tools/inspect_run.py --n 10             # show last 10 files' metrics
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.active_run import load_active_runs  # noqa: E402
from monitor.analyze import analyze_file  # noqa: E402
from monitor.poller import poll_new_files  # noqa: E402
from monitor.schemas import ActiveRun  # noqa: E402


def _minutes_ago(iso_str: str | None) -> int | None:
    if not iso_str:
        return None
    try:
        t = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        delta = now - t.replace(tzinfo=timezone.utc) if t.tzinfo is None else now - t
        return max(0, int(delta.total_seconds() / 60))
    except Exception:
        return None


def _trend(values: list, key: str, n: int = 5) -> str:
    """Format last N values of a metric as a short arrow-joined string."""
    recent = values[-n:]
    if not recent:
        return ""
    fmted = []
    for v in recent:
        if isinstance(v, float):
            fmted.append(f"{v:.4g}")
        else:
            fmted.append(str(v))
    return " → ".join(fmted)


def inspect_run(run: ActiveRun, n_trend: int = 5) -> str:
    """Return a compact text block describing the run state."""
    lines = []

    started_min = _minutes_ago(run.started_at)
    polled_min = _minutes_ago(run.last_polled_at)
    n_known = len(run.known_files)

    lines.append(f"Run {run.run_id[:8]}  |  {run.sample}  |  {run.modality}  |  {run.experimenter}")
    started_str = f"{started_min}m ago" if started_min is not None else run.started_at
    polled_str = f"{polled_min}m ago" if polled_min is not None else "never"
    lines.append(f"  Started: {started_str}  |  Last poll: {polled_str}  |  Files tracked: {n_known}")

    if run.context:
        lines.append(f"  Context: {run.context[:120]}")

    # Scan for new (unanalyzed) files
    new_events = poll_new_files(run)
    if new_events:
        lines.append(f"  Unanalyzed files since last poll: {len(new_events)}")

    # Re-analyze the last N known files for metrics trend
    # (most recent files, sorted by path — proxy for mtime order in known_files)
    local_dir = Path(run.local_dir)
    known_paths = sorted(
        [local_dir / f for f in run.known_files if (local_dir / f).exists()],
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
    )
    recent_paths = known_paths[-n_trend * 2:]  # take more than needed, filter below

    if recent_paths:
        from monitor.schemas import FileArrivedEvent as FAE  # noqa
        results = []
        flag_counts: Counter = Counter()
        clean = warn = error = 0

        for p in recent_paths:
            rel = str(p.relative_to(local_dir))
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
            evt = FAE(
                event_id=rel,
                run_id=run.run_id,
                filename=p.name,
                local_path=str(p),
                file_size_bytes=p.stat().st_size,
                mtime=mtime,
                inferred_modality=run.modality,
            )
            ar = analyze_file(evt)
            results.append(ar)
            for f in ar.quality_flags:
                flag_counts[f.split(":")[0]] += 1
            if ar.anomaly_score >= 0.5:
                error += 1
            elif ar.anomaly_score > 0:
                warn += 1
            else:
                clean += 1

        total = clean + warn + error
        lines.append(f"  Last {total} files: {clean} clean  {warn} warnings  {error} errors")

        if flag_counts:
            top = flag_counts.most_common(5)
            flag_str = "  |  ".join(f"{k}×{v}" for k, v in top)
            lines.append(f"  Flags: {flag_str}")

        # Metric trends — pick the most informative metrics per modality
        trend_keys = {
            "PL": ["peak_energy_eV", "peak_snr", "integrated_intensity"],
            "RMCD": ["coercive_field_T", "saturation_contrast", "rmcd_range"],
            "Reflectance": ["resonance_center_eV", "dRR_amplitude", "resonance_dip_depth"],
        }.get(run.modality, [])

        for key in trend_keys:
            vals = [r.metrics.get(key) for r in results if r.metrics.get(key) is not None]
            if len(vals) >= 2:
                t = _trend(vals, key, n_trend)
                lines.append(f"  {key}: {t}")

    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Compact status of active monitoring runs.")
    ap.add_argument("--run-id", default=None, help="Show only this run")
    ap.add_argument(
        "--state", default="state/active_runs.json",
        help="Path to active_runs.json"
    )
    ap.add_argument("--n", type=int, default=5, help="Number of recent files for metric trends")
    ap.add_argument("--json", action="store_true", dest="output_json",
                    help="Output as JSON (for machine reading)")
    args = ap.parse_args()

    cwd = Path.cwd()
    state_path = (cwd / args.state).resolve()
    runs = load_active_runs(state_path=state_path)
    if args.run_id:
        runs = [r for r in runs if r.run_id.startswith(args.run_id)]

    if not runs:
        print("No active runs." if not args.run_id else f"No run matching {args.run_id}.")
        return

    if args.output_json:
        out = []
        for run in runs:
            out.append({
                "run_id": run.run_id,
                "sample": run.sample,
                "modality": run.modality,
                "experimenter": run.experimenter,
                "started_at": run.started_at,
                "last_polled_at": run.last_polled_at,
                "files_tracked": len(run.known_files),
                "context": run.context,
            })
        print(json.dumps(out, indent=2))
    else:
        for run in runs:
            print(inspect_run(run, n_trend=args.n))
            print()


if __name__ == "__main__":
    main()
