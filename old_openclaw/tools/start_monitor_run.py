#!/usr/bin/env python3
"""
Register a new active experiment run for monitoring.

Called by the OpenClaw agent when someone announces an experiment on Slack:
  "Starting RMCD run on D93 at D=0.375, v=-2 (Yifan)"

Usage:
  python3 tools/start_monitor_run.py \
    --dropbox-dir "tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3/v = -2, D = 0.375 Curie Weiss" \
    --modality RMCD \
    --sample D93 \
    --experimenter Yifan \
    --context "Curie-Weiss sweep at v=-2, D=0.375. Watch for changes in coercive field."

This writes to state/active_runs.json and prints the run_id.
The OpenClaw agent should then start calling poll_monitor.py every few minutes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.active_run import register_run  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Register a new active run for monitoring.")
    ap.add_argument(
        "--dropbox-dir", required=True,
        help="Dropbox-relative directory to watch (e.g. tMoTe2_Measuring/...)"
    )
    ap.add_argument(
        "--modality", default="unknown",
        choices=["PL", "RMCD", "Reflectance", "Transport", "PumpProbe", "unknown"],
        help="Measurement modality"
    )
    ap.add_argument("--sample", default="unknown", help="Sample label (e.g. D93)")
    ap.add_argument("--experimenter", default="unknown", help="Who is running the experiment")
    ap.add_argument(
        "--context", default="",
        help="Free-text context from the Slack message (conditions, what to watch for)"
    )
    ap.add_argument(
        "--dropbox-root",
        default=None,
        help="Dropbox cache root (default: read from state/dropbox_config.json)"
    )
    ap.add_argument(
        "--state", default="state/active_runs.json",
        help="Path to active_runs.json state file"
    )
    ap.add_argument("--stop", action="store_true",
                    help="Stop monitoring an existing run (requires --run-id)")
    ap.add_argument("--run-id", default=None,
                    help="run_id to stop (used with --stop)")
    args = ap.parse_args()

    cwd = Path.cwd()
    state_path = (cwd / args.state).resolve()

    if args.stop:
        if not args.run_id:
            print("ERROR: --stop requires --run-id", file=sys.stderr)
            sys.exit(1)
        from monitor.active_run import stop_run
        ok = stop_run(args.run_id, state_path=state_path)
        if ok:
            print(f"run_id {args.run_id} stopped.")
        else:
            print(f"run_id {args.run_id} not found.", file=sys.stderr)
            sys.exit(1)
        return

    # Resolve local cache dir
    dropbox_root = _resolve_dropbox_root(cwd, args.dropbox_root)
    local_dir = str(dropbox_root / args.dropbox_dir)

    run = register_run(
        dropbox_dir=args.dropbox_dir,
        local_dir=local_dir,
        modality=args.modality,
        sample=args.sample,
        experimenter=args.experimenter,
        context=args.context,
        state_path=state_path,
    )

    print(f"run_id: {run.run_id}")
    print(f"dropbox_dir: {run.dropbox_dir}")
    print(f"local_dir: {run.local_dir}")
    print(f"modality: {run.modality}")
    print(f"sample: {run.sample}")
    print(f"experimenter: {run.experimenter}")
    print(f"started_at: {run.started_at}")
    print(f"state_file: {state_path}")
    print()
    print("Run registered. Start polling with:")
    print(f"  python3 tools/poll_monitor.py --run-id {run.run_id}")


def _resolve_dropbox_root(cwd: Path, override: str | None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    config_path = cwd / "state" / "dropbox_config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            root = cfg.get("dropbox_root")
            if root:
                return Path(root).expanduser().resolve()
        except Exception:
            pass
    return cwd / "data" / "dropbox_cache"


if __name__ == "__main__":
    main()
