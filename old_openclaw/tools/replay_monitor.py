#!/usr/bin/env python3
"""
Replay a historical experiment run through the monitoring pipeline.

Given a local directory containing .mat files from a past experiment,
processes them in chronological order (mtime) to evaluate what the
monitor would have flagged.

Usage:
  # Dry-run (no LLM calls):
  python3 tools/replay_monitor.py \
    --dir "data/dropbox_cache/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3" \
    --modality RMCD --sample D93 --experimenter Yifan

  # With real LLM adjudication:
  ANTHROPIC_API_KEY=sk-... python3 tools/replay_monitor.py \
    --dir "data/dropbox_cache/..." --modality RMCD --no-dry-run -v

  # JSON output for downstream evaluation:
  python3 tools/replay_monitor.py --dir "..." --json > out/replay_result.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.replay import replay_run  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Replay a past experiment run.")
    ap.add_argument(
        "--dir", required=True,
        help="Local directory containing .mat files (absolute or relative to workspace)"
    )
    ap.add_argument(
        "--modality", default="unknown",
        choices=["PL", "RMCD", "Reflectance", "Transport", "PumpProbe", "unknown"],
    )
    ap.add_argument("--sample", default="unknown")
    ap.add_argument("--experimenter", default="unknown")
    ap.add_argument("--context", default="")
    ap.add_argument("--no-dry-run", action="store_true",
                    help="Make real LLM API calls")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--json", action="store_true", dest="output_json")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    local_dir = Path(args.dir)
    if not local_dir.is_absolute():
        local_dir = (_WORKSPACE / local_dir).resolve()

    if not local_dir.exists():
        print(f"ERROR: directory not found: {local_dir}", file=sys.stderr)
        sys.exit(1)

    corpus_dir = _WORKSPACE / "state" / "corpus"

    result = replay_run(
        local_dir=local_dir,
        modality=args.modality,
        sample=args.sample,
        experimenter=args.experimenter,
        context=args.context,
        model=args.model,
        dry_run=not args.no_dry_run,
        verbose=args.verbose,
        corpus_dir=corpus_dir if corpus_dir.exists() else None,
    )

    if args.output_json:
        print(json.dumps(dataclasses.asdict(result), indent=2, default=str))
    else:
        print()
        print("=" * 60)
        print("  REPLAY RESULT")
        print("=" * 60)
        print(f"  Directory:      {result.local_dir}")
        print(f"  Modality:       {result.modality}")
        print(f"  Files replayed: {result.files_replayed}")
        print(f"  Files w/flags:  {result.files_with_flags}")
        print(f"  Anomaly cands:  {result.anomaly_candidates}")
        print(f"  LLM decisions:  {len(result.decisions)}")
        print(f"  Alerts issued:  {result.alerts_issued}")
        print(f"  Duration:       {result.duration_seconds:.1f}s")
        print(f"  Est. LLM cost:  ${result.estimated_llm_cost_usd:.4f}")
        print("=" * 60)

        if result.decisions:
            print("\nDecisions:")
            for d in result.decisions:
                sym = {"alert": "[ALERT]", "watch": "[watch]", "suppress": "[ ok ]"}.get(
                    d.decision, "[?]"
                )
                print(f"  {sym}  {d.likely_cause}: {d.reasoning[:80]}")
                if d.slack_message:
                    print(f"         Slack: {d.slack_message[:100]}")


if __name__ == "__main__":
    main()
