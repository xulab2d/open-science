from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = ROOT / "lab_assistant" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import fact_graph  # noqa: E402
from lab_assistant.runtime.context_pack import build_context_pack  # noqa: E402
from lab_assistant.runtime.metrics import (  # noqa: E402
    compare_metric_maps,
    jaccard_similarity,
    latency_summary,
    mean_reciprocal_rank,
    precision_at_k,
    recall_at_k,
)
from lab_assistant.runtime.mutation import (  # noqa: E402
    attach_eval_result,
    decide_candidate,
    propose_candidate,
    proposed_memory_mutation,
    validate_memory_mutation,
)
from lab_assistant.runtime.snapshot import hash_paths, stable_hash  # noqa: E402
from lab_assistant.runtime.trajectory import make_trajectory, validate_trajectory  # noqa: E402
from lab_assistant.science.hypothesis import (  # noqa: E402
    hypothesis_memory_mutation,
    scaffold_hypothesis,
    score_hypothesis,
    validate_hypothesis,
)


def test_trajectory_schema_and_hash_determinism():
    context_pack = {"context_pack_id": "pack1", "items": [], "excluded": []}
    left = make_trajectory(
        "claim_lookup",
        "RMCD hysteresis",
        context_pack=context_pack,
        trajectory_id="traj1",
        created_at="2026-01-01T00:00:00Z",
    )
    right = make_trajectory(
        "claim_lookup",
        "RMCD hysteresis",
        context_pack=context_pack,
        trajectory_id="traj1",
        created_at="2026-01-01T00:00:00Z",
    )
    assert validate_trajectory(left.to_dict()) == []
    assert left.trajectory_hash == right.trajectory_hash
    invalid = left.to_dict()
    invalid["task"]["type"] = "not_a_task"
    assert validate_trajectory(invalid)


def test_memory_snapshot_hash_changes_when_source_file_changes(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("first\n", encoding="utf-8")
    before = hash_paths([source])
    source.write_text("second\n", encoding="utf-8")
    after = hash_paths([source])
    assert before != after


def test_stable_hash_is_order_deterministic_for_dicts():
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_context_compiler_is_deterministic_and_task_routed():
    paper_pack_1, _ = build_context_pack(
        task_type="paper_lookup",
        query="moire exciton optical signatures",
        char_budget=14000,
        write=False,
    )
    paper_pack_2, _ = build_context_pack(
        task_type="paper_lookup",
        query="moire exciton optical signatures",
        char_budget=14000,
        write=False,
    )
    claim_pack, _ = build_context_pack(
        task_type="claim_lookup",
        query="moire exciton optical signatures",
        char_budget=14000,
        write=False,
    )
    assert paper_pack_1.context_pack_id == paper_pack_2.context_pack_id
    paper_ids = {item.id for item in paper_pack_1.items}
    claim_ids = {item.id for item in claim_pack.items}
    assert "skill_metadata:reference-retrieval" in paper_ids
    assert "skill_metadata:fact-graph" in claim_ids
    assert paper_ids != claim_ids


def test_context_budget_and_legacy_fallback():
    pack, _ = build_context_pack(
        task_type="paper_lookup",
        query="moire exciton optical signatures",
        char_budget=1000,
        write=False,
    )
    assert pack.excluded
    fallback, _ = build_context_pack(
        task_type="unknown_task",
        query="anything",
        char_budget=5000,
        legacy_fallback=True,
        write=False,
    )
    assert any(item.path == "lab_assistant/core/identity.md" for item in fallback.items)


def test_graph_adjacency_degree_and_task_search():
    assert fact_graph.validate() == 0
    _nodes, edges = fact_graph.load_graph()
    adjacency = fact_graph.build_adjacency(edges)
    degrees = fact_graph.degree_counts(edges)
    for node_id, neighbors in list(adjacency.items())[:20]:
        assert degrees[node_id] == len(neighbors)
    paper_hits = fact_graph.task_aware_search("moire exciton optical signatures", "paper_lookup", limit=5)
    assert paper_hits
    assert all(hit["type"] == "Paper" for hit in paper_hits)
    metrics = fact_graph.search_with_metrics("RMCD hysteresis", task_type="claim_lookup", limit=5)
    assert "latency_ms" in metrics["metrics"]
    assert metrics["hits"]


def test_core_metric_calculations_and_regression_flags():
    retrieved = ["a", "b", "c"]
    relevant = {"b", "d"}
    assert recall_at_k(retrieved, relevant, 2) == 0.5
    assert precision_at_k(retrieved, relevant, 2) == 0.5
    assert mean_reciprocal_rank(retrieved, relevant) == 0.5
    assert jaccard_similarity(["a", "b"], ["b", "c"]) == 1 / 3
    summary = latency_summary([10, 20, 30])
    assert summary["p50"] == 20
    _rows, regressions = compare_metric_maps(
        {"pass_rate": 1.0, "latency_ms_mean": 10.0},
        {"pass_rate": 0.9, "latency_ms_mean": 12.0},
        protected_metrics={"pass_rate", "latency_ms_mean"},
        lower_is_better={"latency_ms_mean"},
    )
    assert {item.metric for item in regressions} == {"pass_rate", "latency_ms_mean"}


def test_mutation_archive_lifecycle_and_direct_write_warning(tmp_path: Path):
    archive = tmp_path / "improvements"
    candidate = propose_candidate(
        name="retrieval_paper_first",
        from_trajectory="traj1",
        target_metrics=["retrieval_recall_at_5"],
        archive_root=archive,
        created_at="2026-01-01T00:00:00Z",
    )
    candidate_path = archive / "candidates" / f"{candidate.candidate_id}.json"
    assert candidate_path.exists()
    attach_eval_result(candidate.candidate_id, {"suite": "retrieval", "passed": True}, archive_root=archive)
    decided = decide_candidate(candidate.candidate_id, "promoted", "improved retrieval", archive_root=archive)
    promoted_path = archive / "promoted" / f"{candidate.candidate_id}.json"
    assert decided.decision == "promoted"
    assert promoted_path.exists()
    data = json.loads(promoted_path.read_text(encoding="utf-8"))
    assert data["eval_results"]

    mutation = proposed_memory_mutation(
        mutation_type="skill_edit",
        target_path="lab_assistant/skills/fact-graph.md",
        rationale="test",
        payload={"change": "x"},
    )
    valid, warnings = validate_memory_mutation(mutation)
    assert not valid
    assert warnings


def test_synthesis_object_scoring_and_candidate_mutation():
    hypothesis = scaffold_hypothesis("RMCD hysteresis magnetic transition")
    data = hypothesis.to_dict()
    assert validate_hypothesis(data) == []
    score = score_hypothesis(data)
    assert score["scores"]["groundedness"] >= 3
    weak = dict(data)
    weak["supporting_claims"] = []
    weak["provenance"] = []
    weak_score = score_hypothesis(weak)
    assert weak_score["scores"]["groundedness"] < score["scores"]["groundedness"]
    mutation = hypothesis_memory_mutation(hypothesis)
    assert mutation["status"] == "proposed"
    assert mutation["requires_candidate"] is True
