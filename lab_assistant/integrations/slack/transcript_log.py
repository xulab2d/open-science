from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


INTEGRATION_DIR = Path(__file__).resolve().parent
LOG_DIR = INTEGRATION_DIR / "logs"


def _ensure_log_dir() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def _monthly_log_path(now: datetime) -> Path:
    return _ensure_log_dir() / f"slack_transcript_{now.strftime('%Y-%m')}.jsonl"


def append_transcript_entry(entry: dict[str, Any]) -> Path:
    now = datetime.now().astimezone()
    payload = {
        "logged_at": now.isoformat(),
        **entry,
    }
    path = _monthly_log_path(now)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
    return path
