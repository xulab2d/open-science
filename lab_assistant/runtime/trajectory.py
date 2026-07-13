"""Trajectory records for repeatable agent evaluation and replay."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .snapshot import PACKAGE_ROOT, collect_memory_snapshot, repo_commit, stable_hash, utc_now


TASK_TYPES = {
    "paper_lookup",
    "claim_lookup",
    "synthesis",
    "project_status",
    "memory_update",
    "code_patch",
    "hypothesis_generation",
    "unknown",
}

STEP_KINDS = {"retrieve", "context_compile", "llm", "tool", "eval", "memory_mutation"}


@dataclass
class TrajectoryStep:
    kind: str
    name: str
    input_hash: str
    output_hash: str
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trajectory:
    trajectory_id: str
    created_at: str
    repo_commit: str
    agent_variant: str
    task: dict[str, Any]
    memory_snapshot: dict[str, Any]
    context_pack: dict[str, Any]
    steps: list[dict[str, Any]]
    outputs: dict[str, Any]
    memory_mutations: list[dict[str, Any]]
    scores: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def trajectory_hash(self) -> str:
        return stable_hash(self.to_dict())


def empty_scores() -> dict[str, Any]:
    return {
        "task_success": None,
        "retrieval_recall_at_k": None,
        "mrr": None,
        "grounding": None,
        "context_relevance": None,
        "latency_ms": None,
        "token_estimate": None,
        "regression_count": None,
    }


def validate_trajectory(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "trajectory_id",
        "created_at",
        "repo_commit",
        "agent_variant",
        "task",
        "memory_snapshot",
        "context_pack",
        "steps",
        "outputs",
        "memory_mutations",
        "scores",
    ]
    for field_name in required:
        if field_name not in data:
            errors.append(f"missing {field_name}")
    task = data.get("task", {})
    if not isinstance(task, dict):
        errors.append("task must be object")
    else:
        if task.get("type") not in TASK_TYPES:
            errors.append(f"invalid task.type {task.get('type')}")
        if "input" not in task:
            errors.append("task.input missing")
        if "normalized_query" not in task:
            errors.append("task.normalized_query missing")
        if not isinstance(task.get("constraints", {}), dict):
            errors.append("task.constraints must be object")
    if not isinstance(data.get("steps", []), list):
        errors.append("steps must be list")
    else:
        for index, step in enumerate(data.get("steps", [])):
            if step.get("kind") not in STEP_KINDS:
                errors.append(f"steps[{index}].kind invalid")
            for name in ("name", "input_hash", "output_hash"):
                if name not in step:
                    errors.append(f"steps[{index}].{name} missing")
    context_pack = data.get("context_pack", {})
    if not isinstance(context_pack, dict) or "context_pack_id" not in context_pack:
        errors.append("context_pack.context_pack_id missing")
    return errors


def make_trajectory(
    task_type: str,
    task_input: str,
    *,
    agent_variant: str = "default",
    normalized_query: str | None = None,
    constraints: dict[str, Any] | None = None,
    context_pack: dict[str, Any] | None = None,
    steps: list[TrajectoryStep] | None = None,
    outputs: dict[str, Any] | None = None,
    memory_mutations: list[dict[str, Any]] | None = None,
    scores: dict[str, Any] | None = None,
    trajectory_id: str | None = None,
    created_at: str | None = None,
) -> Trajectory:
    snapshot = collect_memory_snapshot()
    pack = context_pack or {"context_pack_id": None, "items": [], "excluded": []}
    trajectory = Trajectory(
        trajectory_id=trajectory_id or str(uuid4()),
        created_at=created_at or utc_now(),
        repo_commit=repo_commit(),
        agent_variant=agent_variant,
        task={
            "type": task_type if task_type in TASK_TYPES else "unknown",
            "input": task_input,
            "normalized_query": normalized_query if normalized_query is not None else " ".join(task_input.lower().split()),
            "constraints": constraints or {},
        },
        memory_snapshot=snapshot.to_dict(),
        context_pack=pack,
        steps=[asdict(step) for step in steps] if steps else [],
        outputs=outputs or {"answer_hash": None, "files_changed": [], "artifacts": []},
        memory_mutations=memory_mutations or [],
        scores={**empty_scores(), **(scores or {})},
    )
    errors = validate_trajectory(trajectory.to_dict())
    if errors:
        raise ValueError("; ".join(errors))
    return trajectory


def write_trajectory(trajectory: Trajectory, output_dir: Path | None = None) -> Path:
    target_dir = output_dir or (PACKAGE_ROOT / "runs")
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{trajectory.trajectory_id}.json"
    payload = trajectory.to_dict()
    payload["trajectory_hash"] = trajectory.trajectory_hash
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_trajectory(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_trajectory(data)
    if errors:
        raise ValueError("; ".join(errors))
    return data


def _new_from_args(args: argparse.Namespace) -> int:
    from .context_pack import build_context_pack

    pack, _markdown = build_context_pack(
        task_type=args.task_type,
        query=args.input,
        latency_tier=args.latency_tier,
        char_budget=args.char_budget,
        write=False,
        legacy_fallback=args.legacy_fallback,
    )
    step = TrajectoryStep(
        kind="context_compile",
        name="runtime.context_pack.build_context_pack",
        input_hash=stable_hash({"task_type": args.task_type, "input": args.input}),
        output_hash=stable_hash(pack.to_summary_dict()),
        latency_ms=pack.metrics.get("latency_ms", 0),
        metadata={"context_pack_id": pack.context_pack_id},
    )
    trajectory = make_trajectory(
        args.task_type,
        args.input,
        agent_variant=args.agent_variant,
        context_pack=pack.to_trajectory_dict(),
        steps=[step],
        scores={"latency_ms": pack.metrics.get("latency_ms"), "token_estimate": pack.metrics.get("token_estimate")},
    )
    payload = trajectory.to_dict()
    payload["trajectory_hash"] = trajectory.trajectory_hash
    if args.dry_run:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    path = write_trajectory(trajectory, Path(args.output_dir) if args.output_dir else None)
    print(path)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and validate OpenScience trajectories.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    new = sub.add_parser("new")
    new.add_argument("--task-type", required=True, choices=sorted(TASK_TYPES))
    new.add_argument("--input", required=True)
    new.add_argument("--agent-variant", default="default")
    new.add_argument("--latency-tier", default="normal", choices=["direct", "fast", "normal", "deep", "self_improve"])
    new.add_argument("--char-budget", type=int, default=None)
    new.add_argument("--output-dir", default=None)
    new.add_argument("--dry-run", action="store_true")
    new.add_argument("--legacy-fallback", action="store_true")

    validate = sub.add_parser("validate")
    validate.add_argument("path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cmd == "new":
        return _new_from_args(args)
    if args.cmd == "validate":
        data = load_trajectory(Path(args.path))
        print(f"ok: {data['trajectory_id']}")
        return 0
    raise SystemExit(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
