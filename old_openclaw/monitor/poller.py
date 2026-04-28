"""
File poller: detects new .mat (and .csv, .h5) files in an active run's
local cache directory and returns FileArrivedEvents for each new one.

This does NOT call the Dropbox API directly. The caller (poll_monitor.py)
is responsible for running dropbox_sync.py first to pull fresh files;
the poller then compares what's on disk to what was already known.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .schemas import ActiveRun, FileArrivedEvent

# Extensions we consider data files worth analyzing
_DATA_EXTENSIONS = {".mat", ".csv", ".h5", ".hdf5", ".npy"}

# Heuristic modality inference from filename
_MODALITY_PATTERNS: list[tuple[str, str]] = [
    ("rmcd", "RMCD"),
    ("refl", "Reflectance"),
    ("pl", "PL"),
    ("pumpprobe", "PumpProbe"),
    ("transport", "Transport"),
]


def _infer_modality(filename: str, run_modality: str) -> str:
    name_lower = filename.lower()
    for token, label in _MODALITY_PATTERNS:
        if token in name_lower:
            return label
    return run_modality  # fall back to run-level declaration


def _iso_from_mtime(path: Path) -> str:
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def poll_new_files(run: ActiveRun) -> list[FileArrivedEvent]:
    """
    Scan the run's local_dir for data files not yet in run.known_files.
    Returns one FileArrivedEvent per new file, sorted oldest-first by mtime.

    Call update_run() after processing to persist the new known_files list.
    """
    local_dir = Path(run.local_dir)
    if not local_dir.exists():
        return []

    known = set(run.known_files)
    new_events: list[tuple[float, FileArrivedEvent]] = []

    for path in local_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _DATA_EXTENSIONS:
            continue

        # Use path relative to local_dir as the stable key
        rel = str(path.relative_to(local_dir))
        if rel in known:
            continue

        mtime_ts = path.stat().st_mtime
        new_events.append((
            mtime_ts,
            FileArrivedEvent(
                event_id=str(uuid.uuid4())[:8],
                run_id=run.run_id,
                local_path=str(path),
                filename=path.name,
                file_size_bytes=path.stat().st_size,
                mtime=_iso_from_mtime(path),
                inferred_modality=_infer_modality(path.name, run.modality),
            )
        ))

    # Sort oldest first so we process files in arrival order
    new_events.sort(key=lambda t: t[0])
    return [evt for _, evt in new_events]


def mark_files_known(run: ActiveRun, events: list[FileArrivedEvent]) -> None:
    """Add the files from these events to run.known_files (mutates run in-place)."""
    local_dir = Path(run.local_dir)
    for evt in events:
        try:
            rel = str(Path(evt.local_path).relative_to(local_dir))
        except ValueError:
            rel = evt.local_path
        if rel not in run.known_files:
            run.known_files.append(rel)
