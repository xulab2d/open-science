"""Candidate archive for measured self-improvement."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .snapshot import PACKAGE_ROOT, stable_hash, utc_now


ARCHIVE_ROOT = PACKAGE_ROOT / "improvements"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value or "candidate"


@dataclass
class Candidate:
    candidate_id: str
    created_at: str
    created_by_trajectory: str
    hypothesis: str
    target_metrics: list[str]
    protected_metrics: list[str]
    files_touched: list[str]
    patch_path: str | None = None
    eval_results: list[dict[str, Any]] = field(default_factory=list)
    decision: str = "proposed"
    decision_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def candidate_path(candidate_id: str, archive_root: Path = ARCHIVE_ROOT) -> Path | None:
    for folder in ("candidates", "promoted", "rejected"):
        path = archive_root / folder / f"{candidate_id}.json"
        if path.exists():
            return path
    return None


def validate_candidate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "candidate_id",
        "created_at",
        "created_by_trajectory",
        "hypothesis",
        "target_metrics",
        "protected_metrics",
        "files_touched",
        "eval_results",
        "decision",
        "decision_reason",
    ]
    for key in required:
        if key not in data:
            errors.append(f"missing {key}")
    if data.get("decision") not in {"proposed", "promoted", "rejected"}:
        errors.append("invalid decision")
    for key in ("target_metrics", "protected_metrics", "files_touched", "eval_results"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} must be list")
    return errors


def write_candidate(candidate: Candidate, archive_root: Path = ARCHIVE_ROOT, folder: str = "candidates") -> Path:
    path = archive_root / folder / f"{candidate.candidate_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(candidate.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_candidate(candidate_id_or_path: str, archive_root: Path = ARCHIVE_ROOT) -> Candidate:
    raw_path = Path(candidate_id_or_path)
    path = raw_path if raw_path.exists() else candidate_path(candidate_id_or_path, archive_root)
    if path is None:
        raise FileNotFoundError(candidate_id_or_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_candidate(data)
    if errors:
        raise ValueError("; ".join(errors))
    return Candidate(**data)


def propose_candidate(
    *,
    name: str,
    from_trajectory: str = "manual",
    hypothesis: str | None = None,
    target_metrics: list[str] | None = None,
    protected_metrics: list[str] | None = None,
    files_touched: list[str] | None = None,
    patch_path: str | None = None,
    archive_root: Path = ARCHIVE_ROOT,
    created_at: str | None = None,
) -> Candidate:
    base = {
        "name": name,
        "from_trajectory": from_trajectory,
        "hypothesis": hypothesis or f"{name} should improve measured agent behavior.",
        "files_touched": files_touched or [],
    }
    candidate_id = f"cand_{slugify(name)}_{stable_hash(base)[:10]}"
    candidate = Candidate(
        candidate_id=candidate_id,
        created_at=created_at or utc_now(),
        created_by_trajectory=from_trajectory,
        hypothesis=hypothesis or f"{name} should improve measured agent behavior.",
        target_metrics=target_metrics or ["task_success"],
        protected_metrics=protected_metrics or ["replay_stability", "paper_lookup_precision"],
        files_touched=files_touched or [],
        patch_path=patch_path,
    )
    write_candidate(candidate, archive_root=archive_root)
    return candidate


def attach_eval_result(candidate_id: str, result: dict[str, Any], archive_root: Path = ARCHIVE_ROOT) -> Candidate:
    candidate = load_candidate(candidate_id, archive_root=archive_root)
    candidate.eval_results.append(result)
    folder = "candidates" if candidate.decision == "proposed" else candidate.decision
    if folder == "promoted":
        folder = "promoted"
    if folder == "rejected":
        folder = "rejected"
    write_candidate(candidate, archive_root=archive_root, folder=folder)
    return candidate


def decide_candidate(candidate_id: str, decision: str, reason: str, archive_root: Path = ARCHIVE_ROOT) -> Candidate:
    if decision not in {"promoted", "rejected"}:
        raise ValueError("decision must be promoted or rejected")
    candidate = load_candidate(candidate_id, archive_root=archive_root)
    old_path = candidate_path(candidate.candidate_id, archive_root=archive_root)
    candidate.decision = decision
    candidate.decision_reason = reason
    target_folder = "promoted" if decision == "promoted" else "rejected"
    new_path = write_candidate(candidate, archive_root=archive_root, folder=target_folder)
    if old_path and old_path != new_path and old_path.exists():
        old_path.unlink()
    return candidate


def proposed_memory_mutation(
    *,
    mutation_type: str,
    target_path: str,
    rationale: str,
    payload: dict[str, Any],
    candidate_id: str | None = None,
) -> dict[str, Any]:
    return {
        "mutation_id": stable_hash(
            {
                "mutation_type": mutation_type,
                "target_path": target_path,
                "rationale": rationale,
                "payload": payload,
                "candidate_id": candidate_id,
            }
        ),
        "mutation_type": mutation_type,
        "target_path": target_path,
        "rationale": rationale,
        "payload": payload,
        "candidate_id": candidate_id,
        "status": "proposed",
        "requires_candidate": candidate_id is None,
    }


def validate_memory_mutation(mutation: dict[str, Any]) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if not mutation.get("candidate_id"):
        warnings.append("durable memory mutation has no candidate_id")
    if not mutation.get("rationale"):
        warnings.append("mutation rationale missing")
    if not mutation.get("target_path"):
        warnings.append("target_path missing")
    return not warnings, warnings


def _candidate_summary_from_results(path: Path) -> dict[str, Any]:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    passed = sum(1 for record in records if record.get("passed") is True)
    return {"path": str(path), "tasks": len(records), "passed": passed, "pass_rate": passed / len(records) if records else 0.0}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage candidate self-improvement records.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    propose = sub.add_parser("propose")
    propose.add_argument("--name", required=True)
    propose.add_argument("--from-trajectory", default="manual")
    propose.add_argument("--hypothesis", default=None)
    propose.add_argument("--target-metric", action="append", default=[])
    propose.add_argument("--protected-metric", action="append", default=[])
    propose.add_argument("--file-touched", action="append", default=[])
    propose.add_argument("--patch-path", default=None)

    validate = sub.add_parser("validate")
    validate.add_argument("--candidate", required=True)
    validate.add_argument("--suite", default=None)
    validate.add_argument("--output", default=None)

    decide = sub.add_parser("decide")
    decide.add_argument("--candidate", required=True)
    group = decide.add_mutually_exclusive_group(required=True)
    group.add_argument("--promote", action="store_true")
    group.add_argument("--reject", action="store_true")
    decide.add_argument("--reason", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cmd == "propose":
        candidate = propose_candidate(
            name=args.name,
            from_trajectory=args.from_trajectory,
            hypothesis=args.hypothesis,
            target_metrics=args.target_metric or None,
            protected_metrics=args.protected_metric or None,
            files_touched=args.file_touched or None,
            patch_path=args.patch_path,
        )
        print(json.dumps(candidate.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "validate":
        candidate = load_candidate(args.candidate)
        errors = validate_candidate(candidate.to_dict())
        if errors:
            print("\n".join(errors))
            return 1
        if args.suite:
            from lab_assistant.evals.run_evals import run_suites, write_results

            output = Path(args.output) if args.output else PACKAGE_ROOT / "evals" / "results" / f"{candidate.candidate_id}.jsonl"
            records = run_suites(args.suite)
            write_results(records, output)
            attach_eval_result(candidate.candidate_id, _candidate_summary_from_results(output))
        print(f"ok: {candidate.candidate_id}")
        return 0
    if args.cmd == "decide":
        decision = "promoted" if args.promote else "rejected"
        candidate = decide_candidate(args.candidate, decision, args.reason)
        print(json.dumps(candidate.to_dict(), indent=2, sort_keys=True))
        return 0
    raise SystemExit(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
