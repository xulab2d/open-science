#!/usr/bin/env python3
"""
Single poll of all active runs.

Called by the OpenClaw agent every few minutes during an active experiment:
  python3 tools/poll_monitor.py [--run-id <id>] [--no-dry-run]

For each active run:
  1. Scans local_dir for new .mat files not yet analyzed
  2. Analyzes each new file (quality checks + modality-specific metrics)
  3. Builds a RunSummary and calls the LLM for an AlertDecision
  4. Prints a machine-readable summary the OpenClaw agent can read

The Dropbox sync (pulling fresh files from Dropbox) is the caller's
responsibility — run dropbox_sync.py --paths-only --path-dir <dir> first,
or rely on the standard heartbeat sync having just run.

Output format (stdout):
  One block per run, separated by "---".
  If decision == "alert", a "slack_message:" field is included.
  The OpenClaw agent reads this and posts the Slack message if present.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.active_run import load_active_runs, update_run  # noqa: E402
from monitor.adjudicate import adjudicate  # noqa: E402
from monitor.analyze import analyze_file  # noqa: E402
from monitor.poller import mark_files_known, poll_new_files  # noqa: E402
from monitor.schemas import ActiveRun  # noqa: E402
from monitor.summarize import build_run_summary, format_summary_for_llm  # noqa: E402


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def poll_one_run(
    run: ActiveRun,
    *,
    model: str,
    dry_run: bool,
    verbose: bool,
    state_path: Path,
) -> dict:
    """Poll a single run. Returns a result dict for output."""
    result: dict = {
        "run_id": run.run_id,
        "sample": run.sample,
        "modality": run.modality,
        "experimenter": run.experimenter,
    }

    # --- Detect new files ---
    new_events = poll_new_files(run)
    result["new_files"] = len(new_events)

    if not new_events:
        result["decision"] = "suppress"
        result["reason"] = "no new files"
        return result

    # --- Analyze each new file ---
    corpus_dir = state_path.parent / "corpus"
    analysis_results = []
    for evt in new_events:
        ar = analyze_file(
            evt,
            corpus_dir=corpus_dir if corpus_dir.exists() else None,
            corpus_sample=run.sample,
            add_to_corpus=True,
        )
        analysis_results.append(ar)
        if verbose:
            flags = ", ".join(ar.quality_flags) or "ok"
            print(f"  [{run.run_id}] {evt.filename[:50]:50s}  "
                  f"score={ar.anomaly_score:.2f}  [{flags}]",
                  file=sys.stderr)

    # --- Build summary ---
    summary = build_run_summary(run, analysis_results, run.known_files)
    if summary is None:
        result["decision"] = "suppress"
        result["reason"] = "no new files after analysis"
        return result

    result["files_clean"] = summary.files_clean
    result["files_with_warnings"] = summary.files_with_warnings
    result["files_with_errors"] = summary.files_with_errors
    result["anomalies"] = summary.anomalies

    if verbose:
        print(f"\n[{run.run_id}] Summary:", file=sys.stderr)
        print(format_summary_for_llm(summary), file=sys.stderr)

    # --- LLM adjudication (only if something may be wrong) ---
    has_issues = summary.files_with_errors > 0 or summary.files_with_warnings > 0 or summary.anomalies
    needs_llm = has_issues or summary.gap_since_last_file_min > 30

    if needs_llm:
        decision = adjudicate(summary, model=model, dry_run=dry_run)
        result["decision"] = decision.decision
        result["likely_cause"] = decision.likely_cause
        result["reasoning"] = decision.reasoning
        result["suggested_action"] = decision.suggested_action
        result["confidence"] = decision.confidence
        if decision.slack_message:
            result["slack_message"] = decision.slack_message
    else:
        result["decision"] = "suppress"
        result["reason"] = "all new files look clean"

    # --- Update run state ---
    mark_files_known(run, new_events)
    run.last_polled_at = _iso_now()
    update_run(run, state_path=state_path)

    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Poll all active runs for new files.")
    ap.add_argument("--run-id", default=None, help="Poll only this run_id")
    ap.add_argument(
        "--state", default="state/active_runs.json",
        help="Path to active_runs.json"
    )
    ap.add_argument(
        "--no-dry-run", action="store_true",
        help="Make real LLM API calls (requires ANTHROPIC_API_KEY)"
    )
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--json", action="store_true", dest="output_json",
                    help="Output results as JSON (default: human-readable)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    cwd = Path.cwd()
    state_path = (cwd / args.state).resolve()

    active_runs = load_active_runs(state_path=state_path)
    if args.run_id:
        active_runs = [r for r in active_runs if r.run_id == args.run_id]

    if not active_runs:
        if args.output_json:
            print(json.dumps({"active_runs": 0, "results": []}))
        else:
            print("No active runs registered.")
        return

    results = []
    for run in active_runs:
        r = poll_one_run(
            run,
            model=args.model,
            dry_run=not args.no_dry_run,
            verbose=args.verbose,
            state_path=state_path,
        )
        results.append(r)

    if args.output_json:
        print(json.dumps({"active_runs": len(active_runs), "results": results}, indent=2))
    else:
        print(f"Polled {len(active_runs)} active run(s)\n")
        for r in results:
            sep = "=" * 60
            print(sep)
            print(f"Run: {r['run_id']}  |  {r.get('sample')}  |  {r.get('modality')}")
            print(f"New files: {r.get('new_files', 0)}")
            print(f"Decision: {r.get('decision', '?').upper()}", end="")
            if r.get("likely_cause"):
                print(f"  ({r['likely_cause']})", end="")
            print()
            if r.get("reasoning"):
                print(f"Reasoning: {r['reasoning']}")
            if r.get("anomalies"):
                print("Anomalies:")
                for a in r["anomalies"]:
                    print(f"  ! {a}")
            if r.get("slack_message"):
                print(f"\nSlack message ready:\n{r['slack_message']}")
            print()


if __name__ == "__main__":
    main()
