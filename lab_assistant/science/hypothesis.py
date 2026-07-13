"""Structured scientific hypothesis objects and deterministic scoring."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import argparse
import json
from typing import Any

from lab_assistant.runtime.context_pack import _graph_search
from lab_assistant.runtime.mutation import proposed_memory_mutation
from lab_assistant.runtime.snapshot import stable_hash
from .rubrics import SYNTHESIS_RUBRIC_VERSION


CONFIDENCE_VALUES = {"low", "medium", "high"}


@dataclass
class HypothesisObject:
    hypothesis: str
    motivating_gap: str
    supporting_claims: list[str]
    contradicting_claims: list[str]
    mechanism: str
    prediction: str
    minimal_test: str
    falsifying_observation: str
    novelty_rationale: str
    uncertainty_reduction: str
    risks: list[str]
    confidence: str = "low"
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def hypothesis_id(self) -> str:
        return "hypothesis:" + stable_hash(self.to_dict())[:16]


def validate_hypothesis(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "hypothesis",
        "motivating_gap",
        "supporting_claims",
        "contradicting_claims",
        "mechanism",
        "prediction",
        "minimal_test",
        "falsifying_observation",
        "novelty_rationale",
        "uncertainty_reduction",
        "risks",
        "confidence",
    ]
    for key in required:
        if key not in data:
            errors.append(f"missing {key}")
    if data.get("confidence") not in CONFIDENCE_VALUES:
        errors.append("invalid confidence")
    for key in ("supporting_claims", "contradicting_claims", "risks", "provenance"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} must be list")
    return errors


def scaffold_hypothesis(query: str, limit: int = 5) -> HypothesisObject:
    supporting_nodes = _graph_search(query, {"Claim", "Evidence", "Paper", "Mechanism", "Observable"}, limit)
    contradiction_nodes = _graph_search(query, {"Contradiction", "OpenQuestion", "Assumption"}, 3)
    support_ids = [node["id"] for node in supporting_nodes]
    contradiction_ids = [node["id"] for node in contradiction_nodes]
    top_label = supporting_nodes[0]["label"] if supporting_nodes else query
    provenance = [
        {"source": node["id"], "method": "deterministic graph retrieval", "confidence": node.get("confidence")}
        for node in supporting_nodes[:3]
    ]
    return HypothesisObject(
        hypothesis=f"{query}: a testable mechanism may connect {top_label} to the observed regime boundary.",
        motivating_gap=f"The query '{query}' needs a grounded explanation that separates evidence from an untested mechanism.",
        supporting_claims=support_ids,
        contradicting_claims=contradiction_ids,
        mechanism="Candidate mechanism assembled from retrieved claims; requires human or LLM refinement before promotion.",
        prediction="A targeted sweep should change the relevant observable monotonically or reveal a reproducible threshold if the mechanism is correct.",
        minimal_test="Compile the closest existing project or paper evidence and compare the predicted observable trend against one representative sweep.",
        falsifying_observation="The predicted observable trend is absent in a comparable high-quality sweep, or the effect reverses under the stated conditions.",
        novelty_rationale="The scaffold links retrieved claims to a specific falsifiable next observation rather than restating a known result.",
        uncertainty_reduction="Testing would distinguish a mechanism-level explanation from coincidental retrieval overlap.",
        risks=["retrieval may miss unpublished project-specific evidence", "mechanism text is a scaffold, not a final scientific claim"],
        confidence="low",
        provenance=provenance,
    )


def score_hypothesis(data: dict[str, Any]) -> dict[str, Any]:
    errors = validate_hypothesis(data)
    support = data.get("supporting_claims", []) if isinstance(data.get("supporting_claims"), list) else []
    contradictions = data.get("contradicting_claims", []) if isinstance(data.get("contradicting_claims"), list) else []
    provenance = data.get("provenance", []) if isinstance(data.get("provenance"), list) else []
    has_prediction = bool(str(data.get("prediction", "")).strip())
    has_test = bool(str(data.get("minimal_test", "")).strip())
    has_falsifier = bool(str(data.get("falsifying_observation", "")).strip())
    scores = {
        "groundedness": min(5, 2 + len(support)) if support else 0,
        "falsifiability": 5 if has_prediction and has_test and has_falsifier else 2 if has_prediction else 0,
        "mechanism_clarity": 4 if len(str(data.get("mechanism", ""))) > 40 else 1,
        "contradiction_awareness": min(5, 2 + len(contradictions)) if contradictions else 1,
        "novelty_proxy": 4 if len(str(data.get("novelty_rationale", ""))) > 40 else 1,
        "actionability": 4 if len(str(data.get("minimal_test", ""))) > 40 else 1,
        "provenance_completeness": min(5, len(provenance) + 2) if provenance else 0,
    }
    if errors:
        scores = {key: min(value, 2) for key, value in scores.items()}
    return {
        "rubric_version": SYNTHESIS_RUBRIC_VERSION,
        "scores": scores,
        "mean_score": sum(scores.values()) / len(scores),
        "errors": errors,
        "rationale": "Deterministic scaffold rubric; use optional LLM judge only as an additional signal.",
    }


def hypothesis_memory_mutation(hypothesis: HypothesisObject, candidate_id: str | None = None) -> dict[str, Any]:
    payload = {
        "node_type": "Hypothesis",
        "status": "candidate",
        "hypothesis": hypothesis.to_dict(),
    }
    return proposed_memory_mutation(
        mutation_type="graph_hypothesis_proposal",
        target_path="lab_assistant/graph/nodes.jsonl",
        rationale="Hypotheses enter the graph only through candidate-gated memory mutation.",
        payload=payload,
        candidate_id=candidate_id,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or score a structured scientific hypothesis.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    scaffold = sub.add_parser("scaffold")
    scaffold.add_argument("--query", required=True)
    score = sub.add_parser("score")
    score.add_argument("path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cmd == "scaffold":
        hypothesis = scaffold_hypothesis(args.query)
        print(json.dumps(hypothesis.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.cmd == "score":
        with open(args.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        print(json.dumps(score_hypothesis(data), indent=2, sort_keys=True))
        return 0
    raise SystemExit(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
