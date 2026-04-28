"""
Core typed schemas for the active-run monitoring subsystem.
All objects use stdlib dataclasses — no extra dependencies.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Active run registry
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ActiveRun:
    """
    One registered active experiment, stored in state/active_runs.json.

    dropbox_dir:  Dropbox-relative path to watch, e.g.
                  "tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3"
    local_dir:    Absolute path to local cache equivalent
                  (= dropbox_root / dropbox_dir)
    modality:     "PL" | "RMCD" | "Reflectance" | "unknown"
    sample:       Short sample label, e.g. "D93"
    experimenter: Person running the measurement, e.g. "Yifan"
    context:      Free-text notes from the Slack trigger message
                  (conditions, what to watch for, expected parameter ranges)
    status:       "active" | "stopped"
    known_files:  Set of local relative paths already analyzed, so we only
                  process each file once.
    """
    run_id: str
    dropbox_dir: str
    local_dir: str
    modality: str
    sample: str
    experimenter: str
    context: str
    started_at: str           # ISO8601
    last_polled_at: Optional[str]
    status: str
    known_files: list[str]    # relative paths within local_dir


# ---------------------------------------------------------------------------
# File-level events
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class FileArrivedEvent:
    """A new data file detected in the active run directory."""
    event_id: str
    run_id: str
    local_path: str           # absolute local path
    filename: str
    file_size_bytes: int
    mtime: str                # ISO8601
    inferred_modality: str    # from filename/extension heuristics


# ---------------------------------------------------------------------------
# Per-file analysis
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class FileAnalysisResult:
    """
    Condensed output from analyzing one .mat data file.
    Contains structured numbers — not raw arrays.

    quality_flags examples:
      "load_failed", "missing_expected_var", "all_zeros:<var>",
      "all_nan:<var>", "low_snr", "degenerate_shape:<var>",
      "no_variation", "unexpected_file_size"

    anomaly_score: 0–1, higher = more suspicious
    """
    event_id: str
    filename: str
    local_path: str
    modality: str
    loadable: bool
    variables_found: list[str]
    quality_flags: list[str]
    metrics: dict[str, Any]      # modality-specific numbers (peak_nm, snr, loop_area, …)
    anomaly_score: float
    anomaly_reasons: list[str]   # human-readable explanations of any flags
    corpus_result: Optional[dict]  # from corpus.query_similar; None if corpus too small


# ---------------------------------------------------------------------------
# Run-level summary (fed to LLM)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class RunSummary:
    """
    Condensed state of a run over a polling interval.
    This is what gets passed to the LLM adjudication step.
    Everything is text or numbers — no arrays.
    """
    run_id: str
    dropbox_dir: str
    modality: str
    sample: str
    experimenter: str
    context: str                 # original Slack trigger context

    # What arrived since last poll
    new_files_count: int
    new_filenames: list[str]     # just names, not full paths

    # Aggregate quality
    files_clean: int             # no flags
    files_with_warnings: int     # minor flags
    files_with_errors: int       # serious flags (load failed, all-zeros, etc.)

    # Flagged findings (each is a 1-sentence description)
    anomalies: list[str]

    # Key metrics extracted from the new files (per-modality)
    metrics_summary: dict[str, Any]

    # Time since first file in this run
    run_age_hours: float
    # Gap since last file (useful for detecting stalls mid-run)
    gap_since_last_file_min: float


# ---------------------------------------------------------------------------
# LLM decision
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class AlertDecision:
    """
    LLM-generated decision on whether and how to respond to a RunSummary.

    decision:
      "alert"    — post to Slack now
      "suppress" — nothing noteworthy
      "watch"    — log but hold; check again next poll

    likely_cause:
      "instrument_issue", "data_quality", "interesting_physics",
      "routine_pause", "run_complete", "unknown"
    """
    run_id: str
    decided_at: str              # ISO8601
    decision: str
    likely_cause: str
    reasoning: str
    suggested_action: str
    slack_message: Optional[str] # ready-to-send Slack text if decision=="alert"
    confidence: float
    llm_model: str
    prompt_tokens: int
    completion_tokens: int


# ---------------------------------------------------------------------------
# Replay result
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ReplayResult:
    """Summary from replaying a past run through the full pipeline."""
    run_id: str
    local_dir: str
    modality: str
    files_replayed: int
    files_with_flags: int
    anomaly_candidates: int
    decisions: list[AlertDecision]
    alerts_issued: int
    duration_seconds: float
    estimated_llm_cost_usd: float
