"""Deterministic hashing and repository snapshot helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json_dumps(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_lab_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    text = str(candidate)
    if text.startswith("lab_assistant/"):
        return REPO_ROOT / text
    return PACKAGE_ROOT / candidate


def relative_id(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def hash_paths(paths: list[str | Path]) -> str | None:
    records: list[dict[str, str | None]] = []
    for raw_path in sorted(str(item) for item in paths):
        path = resolve_lab_path(raw_path)
        records.append({"path": relative_id(path), "sha256": file_sha256(path)})
    if not records:
        return None
    return stable_hash(records)


def hash_glob(patterns: list[str]) -> str | None:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(PACKAGE_ROOT.glob(pattern))
    files = [path for path in paths if path.is_file()]
    if not files:
        return None
    return hash_paths(files)


def repo_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        return "unknown"
    return result.stdout.strip() or "unknown"


@dataclass(frozen=True)
class MemorySnapshot:
    fact_graph_hash: str | None
    context_policy_hash: str | None
    knowledge_index_hash: str | None
    project_registry_hash: str | None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)

    @property
    def snapshot_id(self) -> str:
        return stable_hash(self.to_dict())


def collect_memory_snapshot() -> MemorySnapshot:
    return MemorySnapshot(
        fact_graph_hash=hash_paths(
            [
                "graph/nodes.jsonl",
                "graph/edges.jsonl",
                "graph/schema.json",
            ]
        ),
        context_policy_hash=hash_paths(
            [
                "context_policy/default.yaml",
                "context_policy/task_routes.yaml",
                "integrations/context_files.json",
            ]
        ),
        knowledge_index_hash=hash_paths(["knowledge/INDEX.md"]),
        project_registry_hash=hash_paths(["context/projects/active_projects.md"]),
    )


def read_jsonish(path: Path) -> Any:
    """Read JSON-compatible YAML without adding a hard PyYAML dependency."""
    return json.loads(path.read_text(encoding="utf-8"))


def estimate_tokens(chars: int) -> int:
    return max(1, (chars + 3) // 4)
