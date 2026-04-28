"""
Summarize a batch of FileAnalysisResults into a RunSummary for the LLM.

The summary is deliberately condensed:
  - No raw arrays
  - Numbers rounded to human-readable precision
  - Anomalies expressed as plain English sentences
  - Parameter progression expressed as ranges, not lists

The LLM receives this summary, not the individual file results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .schemas import FileAnalysisResult, RunSummary, ActiveRun


def _iso_to_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def build_run_summary(
    run: ActiveRun,
    new_results: list[FileAnalysisResult],
    all_known_files: list[str],
) -> RunSummary | None:
    """
    Build a RunSummary from the analysis results of newly-arrived files.
    Returns None if no new files were analyzed.
    """
    if not new_results:
        return None

    clean = [r for r in new_results if not r.quality_flags]
    warns = [r for r in new_results if r.quality_flags and r.anomaly_score < 0.4]
    errors = [r for r in new_results if r.anomaly_score >= 0.4]

    # Collect all anomaly descriptions, deduplicated
    seen_reasons: set[str] = set()
    anomalies: list[str] = []
    for r in new_results:
        for reason in r.anomaly_reasons:
            if reason not in seen_reasons:
                seen_reasons.add(reason)
                anomalies.append(f"{r.filename}: {reason}")

    # Parameter progression summary
    metrics_summary = _aggregate_metrics(new_results)

    # Run age
    started = _iso_to_dt(run.started_at)
    run_age_hours = 0.0
    if started:
        run_age_hours = (datetime.now(timezone.utc) - started).total_seconds() / 3600.0

    # Gap since last file (use mtime of the latest new file)
    gap_min = 0.0
    latest_mtime = _iso_to_dt(run.last_polled_at)
    if latest_mtime:
        gap_min = (datetime.now(timezone.utc) - latest_mtime).total_seconds() / 60.0

    summary = RunSummary(
        run_id=run.run_id,
        dropbox_dir=run.dropbox_dir,
        modality=run.modality,
        sample=run.sample,
        experimenter=run.experimenter,
        context=run.context,
        new_files_count=len(new_results),
        new_filenames=[r.filename for r in new_results],
        files_clean=len(clean),
        files_with_warnings=len(warns),
        files_with_errors=len(errors),
        anomalies=anomalies,
        metrics_summary=metrics_summary,
        run_age_hours=round(run_age_hours, 2),
        gap_since_last_file_min=round(gap_min, 1),
    )
    # Attach raw results so format_summary_for_llm can access corpus data.
    # Not a dataclass field — just a runtime attribute for this session.
    summary._raw_results = new_results  # type: ignore[attr-defined]
    return summary


def _aggregate_metrics(results: list[FileAnalysisResult]) -> dict[str, Any]:
    """Aggregate per-file metrics into a run-level summary."""
    import math

    agg: dict[str, Any] = {}
    num_fields: dict[str, list[float]] = {}

    for r in results:
        for k, v in r.metrics.items():
            if isinstance(v, (int, float)) and math.isfinite(float(v)):
                num_fields.setdefault(k, []).append(float(v))

    # For each numeric field, report min/max/last (last = most recent file)
    for k, vals in num_fields.items():
        if len(vals) == 1:
            agg[k] = round(vals[0], 4)
        else:
            agg[f"{k}_range"] = [round(min(vals), 4), round(max(vals), 4)]
            agg[f"{k}_last"] = round(vals[-1], 4)

    # Count modality types seen
    modalities = [r.modality for r in results]
    if len(set(modalities)) > 1:
        from collections import Counter
        agg["modality_mix"] = dict(Counter(modalities))

    return agg


def format_summary_for_llm(summary: RunSummary) -> str:
    """
    Render a RunSummary as plain text for the LLM adjudication prompt.
    Follows OpenClaw style: concise, science-first, short bullets.
    """
    lines = [
        f"Run: {summary.run_id}  |  Sample: {summary.sample}  |  Modality: {summary.modality}",
        f"Experimenter: {summary.experimenter}",
        f"Directory: {summary.dropbox_dir}",
        f"Run age: {summary.run_age_hours:.1f}h  |  Gap since last file: {summary.gap_since_last_file_min:.0f} min",
    ]

    if summary.context:
        lines.append(f"Context: {summary.context}")

    lines.append("")
    lines.append(f"New files this poll: {summary.new_files_count}")
    if summary.new_filenames:
        # Show up to 5 filenames
        shown = summary.new_filenames[:5]
        if len(summary.new_filenames) > 5:
            shown.append(f"... (+{len(summary.new_filenames) - 5} more)")
        for fn in shown:
            lines.append(f"  - {fn}")

    lines.append(
        f"\nQuality: {summary.files_clean} clean, "
        f"{summary.files_with_warnings} warnings, "
        f"{summary.files_with_errors} errors"
    )

    if summary.anomalies:
        lines.append("\nAnomalies detected:")
        for a in summary.anomalies[:8]:  # cap at 8 to keep tokens low
            lines.append(f"  ! {a}")
    else:
        lines.append("\nNo anomalies detected.")

    if summary.metrics_summary:
        lines.append("\nKey metrics from new files:")
        for k, v in list(summary.metrics_summary.items())[:12]:
            lines.append(f"  {k}: {v}")

    # Corpus outliers — highlight any files that were unusual vs historical data
    corpus_outliers = [
        r for r in getattr(summary, "_raw_results", [])
        if r.corpus_result and r.corpus_result.get("is_outlier")
    ]
    if corpus_outliers:
        lines.append("\nCorpus comparison (unusual vs historical data):")
        for r in corpus_outliers[:4]:
            cr = r.corpus_result
            sim = cr.get("nearest_sim", "?")
            feats = cr.get("outlier_features", [])
            if feats:
                lines.append(f"  {r.filename}: features out of range: {', '.join(feats)}")
            else:
                lines.append(f"  {r.filename}: globally unusual (nearest_sim={sim:.3f})")

    return "\n".join(lines)
