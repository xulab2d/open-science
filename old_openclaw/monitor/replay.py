"""
Replay runner for back-testing the monitor against a historical experiment.

Given a local directory that already contains .mat files from a past run,
replays them in chronological order (by mtime) through the full pipeline.
Useful for:
  - Validating the analysis tools against known data
  - Estimating LLM cost for a real run
  - Tuning anomaly thresholds
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .analyze import analyze_file
from .adjudicate import adjudicate
from .schemas import (
    ActiveRun,
    FileArrivedEvent,
    ReplayResult,
)
from .summarize import build_run_summary, format_summary_for_llm

_DATA_EXTENSIONS = {".mat", ".csv", ".h5", ".hdf5", ".npy"}
_HAIKU_COST_PER_1K_INPUT = 0.001
_HAIKU_COST_PER_1K_OUTPUT = 0.005

# How many files to batch into one RunSummary / LLM call
_BATCH_SIZE = 5


def replay_run(
    local_dir: str | Path,
    modality: str = "unknown",
    sample: str = "unknown",
    experimenter: str = "unknown",
    context: str = "",
    model: str = "claude-haiku-4-5-20251001",
    dry_run: bool = True,
    verbose: bool = False,
    corpus_dir: "Path | None" = None,
) -> ReplayResult:
    """
    Replay all data files in local_dir through the monitoring pipeline.

    Files are processed in mtime order (oldest first), in batches of
    _BATCH_SIZE, producing one RunSummary + LLM decision per batch.
    """
    t0 = time.time()
    local_dir = Path(local_dir)

    # Collect all data files, sorted by mtime
    files = sorted(
        [p for p in local_dir.rglob("*")
         if p.is_file() and p.suffix.lower() in _DATA_EXTENSIONS],
        key=lambda p: p.stat().st_mtime,
    )

    if not files:
        return ReplayResult(
            run_id="none",
            local_dir=str(local_dir),
            modality=modality,
            files_replayed=0,
            files_with_flags=0,
            anomaly_candidates=0,
            decisions=[],
            alerts_issued=0,
            duration_seconds=time.time() - t0,
            estimated_llm_cost_usd=0.0,
        )

    run_id = str(uuid.uuid4())[:8]
    # Synthetic ActiveRun (not persisted to state)
    run = ActiveRun(
        run_id=run_id,
        dropbox_dir=str(local_dir),
        local_dir=str(local_dir),
        modality=modality,
        sample=sample,
        experimenter=experimenter,
        context=context,
        started_at=datetime.now(timezone.utc).isoformat(),
        last_polled_at=None,
        status="active",
        known_files=[],
    )

    total_flagged = 0
    total_anomaly_candidates = 0
    all_decisions = []
    total_input_tokens = 0
    total_output_tokens = 0

    if verbose:
        print(f"Replaying {len(files)} files from {local_dir}")
        print(f"Modality: {modality}  Sample: {sample}")
        print()

    # Process in batches
    for batch_start in range(0, len(files), _BATCH_SIZE):
        batch = files[batch_start: batch_start + _BATCH_SIZE]

        events = []
        results = []
        for f in batch:
            evt = FileArrivedEvent(
                event_id=str(uuid.uuid4())[:8],
                run_id=run_id,
                local_path=str(f),
                filename=f.name,
                file_size_bytes=f.stat().st_size,
                mtime=datetime.fromtimestamp(
                    f.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                inferred_modality=modality,
            )
            events.append(evt)
            result = analyze_file(
                evt,
                corpus_dir=corpus_dir,
                corpus_sample=sample,
            )
            results.append(result)

            if result.quality_flags:
                total_flagged += 1
            if result.anomaly_score >= 0.25:
                total_anomaly_candidates += 1

            if verbose:
                flag_str = ", ".join(result.quality_flags) or "ok"
                print(f"  {f.name[:50]:50s}  score={result.anomaly_score:.2f}  [{flag_str}]")

        summary = build_run_summary(run, results, run.known_files)
        if summary is None:
            continue

        if verbose:
            print(f"\n--- Batch {batch_start // _BATCH_SIZE + 1} summary ---")
            print(format_summary_for_llm(summary))
            print()

        # Only call LLM if there are anomalies or errors
        should_adjudicate = summary.files_with_errors > 0 or summary.anomalies
        if should_adjudicate:
            decision = adjudicate(summary, model=model, dry_run=dry_run)
            total_input_tokens += decision.prompt_tokens
            total_output_tokens += decision.completion_tokens
            all_decisions.append(decision)

            if verbose:
                symbol = {"alert": "[ALERT]", "watch": "[watch]", "suppress": "[ ok ]"}.get(
                    decision.decision, "[?]"
                )
                print(f"{symbol} {decision.likely_cause}: {decision.reasoning}")
                if decision.slack_message:
                    print(f"  Slack: {decision.slack_message}")
                print()

        # Update known_files to avoid re-processing
        for evt in events:
            rel = str(Path(evt.local_path).relative_to(local_dir))
            if rel not in run.known_files:
                run.known_files.append(rel)

    cost = (
        total_input_tokens / 1000 * _HAIKU_COST_PER_1K_INPUT
        + total_output_tokens / 1000 * _HAIKU_COST_PER_1K_OUTPUT
    )
    alerts = sum(1 for d in all_decisions if d.decision == "alert")

    return ReplayResult(
        run_id=run_id,
        local_dir=str(local_dir),
        modality=modality,
        files_replayed=len(files),
        files_with_flags=total_flagged,
        anomaly_candidates=total_anomaly_candidates,
        decisions=all_decisions,
        alerts_issued=alerts,
        duration_seconds=round(time.time() - t0, 2),
        estimated_llm_cost_usd=round(cost, 6),
    )
