"""Replay deterministic parts of a recorded trajectory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .context_pack import build_context_pack
from .metrics import jaccard_similarity
from .snapshot import PACKAGE_ROOT, stable_hash
from .trajectory import load_trajectory


def _resolve_trajectory(identifier: str) -> Path:
    path = Path(identifier)
    if path.exists():
        return path
    candidate = PACKAGE_ROOT / "runs" / f"{identifier}.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(identifier)


def replay_trajectory(identifier: str) -> dict[str, Any]:
    path = _resolve_trajectory(identifier)
    data = load_trajectory(path)
    task = data["task"]
    original_pack = data.get("context_pack", {})
    pack, _markdown = build_context_pack(
        task_type=task.get("type", "unknown"),
        query=task.get("input", ""),
        write=False,
    )
    original_items = [item["id"] for item in original_pack.get("items", [])]
    replay_items = [item.id for item in pack.items]
    result = {
        "trajectory_id": data["trajectory_id"],
        "original_context_pack_id": original_pack.get("context_pack_id"),
        "replay_context_pack_id": pack.context_pack_id,
        "same_context_pack_id": original_pack.get("context_pack_id") == pack.context_pack_id,
        "retrieved_item_jaccard": jaccard_similarity(original_items, replay_items),
        "original_item_hash": stable_hash(original_items),
        "replay_item_hash": stable_hash(replay_items),
        "trajectory_schema_valid": True,
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay an OpenScience trajectory.")
    parser.add_argument("--trajectory-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(replay_trajectory(args.trajectory_id), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
