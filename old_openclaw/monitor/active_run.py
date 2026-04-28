"""
Active run registry management.

Reads and writes state/active_runs.json — the source of truth for which
experiments are currently being monitored.
"""

from __future__ import annotations

import dataclasses
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .schemas import ActiveRun

_DEFAULT_STATE_PATH = Path("state/active_runs.json")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_state(state_path: Path) -> list[dict]:
    if not state_path.exists():
        return []
    try:
        with open(state_path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_state(state_path: Path, runs: list[dict]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(runs, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )


def _run_to_dict(run: ActiveRun) -> dict:
    return dataclasses.asdict(run)


def _dict_to_run(d: dict) -> ActiveRun:
    return ActiveRun(**{k: d.get(k) for k in ActiveRun.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def register_run(
    dropbox_dir: str,
    local_dir: str,
    modality: str,
    sample: str,
    experimenter: str,
    context: str = "",
    state_path: Path = _DEFAULT_STATE_PATH,
) -> ActiveRun:
    """
    Register a new active run. Returns the created ActiveRun.
    Safe to call from the OpenClaw agent when a Slack trigger fires.
    """
    run = ActiveRun(
        run_id=str(uuid.uuid4())[:8],
        dropbox_dir=dropbox_dir,
        local_dir=local_dir,
        modality=modality,
        sample=sample,
        experimenter=experimenter,
        context=context,
        started_at=_iso_now(),
        last_polled_at=None,
        status="active",
        known_files=[],
    )
    runs = _read_state(state_path)
    runs.append(_run_to_dict(run))
    _write_state(state_path, runs)
    return run


def stop_run(run_id: str, state_path: Path = _DEFAULT_STATE_PATH) -> bool:
    """Mark a run as stopped. Returns True if found."""
    runs = _read_state(state_path)
    changed = False
    for r in runs:
        if r.get("run_id") == run_id:
            r["status"] = "stopped"
            changed = True
    if changed:
        _write_state(state_path, runs)
    return changed


def load_active_runs(state_path: Path = _DEFAULT_STATE_PATH) -> list[ActiveRun]:
    """Return all runs with status == 'active'."""
    return [
        _dict_to_run(r)
        for r in _read_state(state_path)
        if r.get("status") == "active"
    ]


def update_run(run: ActiveRun, state_path: Path = _DEFAULT_STATE_PATH) -> None:
    """Persist changes to an existing run (e.g., known_files, last_polled_at)."""
    runs = _read_state(state_path)
    for i, r in enumerate(runs):
        if r.get("run_id") == run.run_id:
            runs[i] = _run_to_dict(run)
            break
    _write_state(state_path, runs)


def get_run(run_id: str, state_path: Path = _DEFAULT_STATE_PATH) -> ActiveRun | None:
    for r in _read_state(state_path):
        if r.get("run_id") == run_id:
            return _dict_to_run(r)
    return None
