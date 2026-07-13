#!/usr/bin/env python3
"""Hard RAG quality benchmark for OpenScience.

This benchmark is intentionally answer-level and presentation-oriented. It uses
common RAG evaluation dimensions from BEIR/KILT/RAGAS/ARES/ALCE/AIS/FActScore:

- retrieval ranking quality: recall@k, precision@k, MRR, nDCG@k, hard negatives
- context quality: context recall and context precision over packed chunks
- generation quality: concept coverage, abstention/caution behavior, citation use
- attribution/factuality: LLM-judge faithfulness plus a lightweight support proxy

The goal is not to certify truth. It is to expose where the current RAG system
fails before a scientist relies on it.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "lab_assistant"
SCRIPTS_DIR = PACKAGE_ROOT / "scripts"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lab_assistant.runtime.context_pack import build_context_pack  # noqa: E402

import fact_graph  # noqa: E402


try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
except Exception:  # pragma: no cover
    plt = None


LITERATURE_NOTES = [
    {
        "name": "RAGAS",
        "url": "https://arxiv.org/abs/2309.15217",
        "local_use": "separate retrieval/context quality from generation faithfulness and answer relevance",
    },
    {
        "name": "BEIR",
        "url": "https://arxiv.org/abs/2104.08663",
        "local_use": "ranked retrieval metrics and hard out-of-domain/alias pressure, with lexical baseline awareness",
    },
    {
        "name": "KILT",
        "url": "https://arxiv.org/abs/2009.02252",
        "local_use": "downstream answer quality plus provenance, not retrieval alone",
    },
    {
        "name": "ALCE",
        "url": "https://arxiv.org/abs/2305.14627",
        "local_use": "citation quality and automatic citation support checks",
    },
    {
        "name": "AIS",
        "url": "https://arxiv.org/abs/2112.12870",
        "local_use": "whether generated statements are attributable to identified sources",
    },
    {
        "name": "FActScore",
        "url": "https://aclanthology.org/2023.emnlp-main.741/",
        "local_use": "atomic factuality framing: score supported factual claims, not just whole answers",
    },
    {
        "name": "ARES",
        "url": "https://arxiv.org/abs/2311.09476",
        "local_use": "LLM-judge dimensions: context relevance, answer faithfulness, answer relevance",
    },
]


def normalize(value: str) -> str:
    value = value.lower()
    value = (
        value.replace("₂", "2")
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace("ν", "nu")
        .replace("é", "e")
        .replace("í", "i")
    )
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return " ".join(value.split())


def contains_any(text: str, options: list[str] | tuple[str, ...]) -> bool:
    norm = normalize(text)
    return any(normalize(option) in norm for option in options)


def group_hit(text: str, group: list[str]) -> bool:
    return contains_any(text, group)


def task_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:96]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list, tuple)) else value
                    for key, value in row.items()
                }
            )


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    if len(values) == 1:
        return values[0]
    index = (len(values) - 1) * pct / 100.0
    low = int(index)
    high = min(low + 1, len(values) - 1)
    weight = index - low
    return values[low] * (1 - weight) + values[high] * weight


@dataclass(frozen=True)
class HardTask:
    id: str
    family: str
    task_type: str
    question: str
    expected_behavior: str = "answer"  # answer, caution, abstain
    required_evidence: list[list[str]] = field(default_factory=list)
    required_answer_concepts: list[list[str]] = field(default_factory=list)
    forbidden_answer_terms: list[str] = field(default_factory=list)
    forbidden_retrieval_terms: list[str] = field(default_factory=list)
    must_cite_like: list[str] = field(default_factory=list)
    evaluator_note: str = ""


TASKS: tuple[HardTask, ...] = (
    HardTask(
        id="d93_nu_minus2_hysteresis_caution",
        family="uncertainty",
        task_type="claim_lookup",
        question="Do we have enough local evidence to claim D93 has a robust hysteretic nu=-2 magnetic state?",
        expected_behavior="caution",
        required_evidence=[["D93 Run2", "D93"], ["no clear hysteresis", "without robust hysteresis", "lacks clear hysteresis"]],
        required_answer_concepts=[["not enough", "insufficient", "not settled", "not enough local evidence"], ["D93"], ["hysteresis"]],
        forbidden_answer_terms=["definitively robust", "settled robust hysteretic"],
        must_cite_like=["question:promoted_d93", "claim:promoted_deck_d93", "D93"],
        evaluator_note="High score requires caution, not just retrieval of D93.",
    ),
    HardTask(
        id="moire_exciton_exclude_polariton",
        family="hard_negative",
        task_type="paper_lookup",
        question="Find the key local references for moire exciton optical signatures, but exclude exciton-polariton or waveguide papers unless they directly address moire trapping.",
        expected_behavior="answer",
        required_evidence=[["moire exciton", "moiré exciton"], ["trapped valley exciton", "moiré-trapped valley excitons"]],
        required_answer_concepts=[["moire exciton", "moiré exciton"], ["optical", "PL", "photoluminescence"], ["exclude", "not use", "distractor"]],
        forbidden_retrieval_terms=["polariton", "waveguide"],
        forbidden_answer_terms=["Nano-optical imaging of the tailored exciton-polariton transport", "Metasurface Integrated Monolayer Exciton Polariton"],
        must_cite_like=["paper:", "knowledge/papers/moire_excitons_and_optics.md"],
        evaluator_note="Tests negative retrieval and citation discipline.",
    ),
    HardTask(
        id="a5_dot_project_context",
        family="project_context",
        task_type="project_status",
        question="For the A5 dot optical project, what local context should be loaded before interpreting PL dispersion or peak-tracking analysis?",
        expected_behavior="answer",
        required_evidence=[["A5 dot"], ["PL dispersion", "peak-tracking", "peak tracking"]],
        required_answer_concepts=[["A5 dot"], ["PL dispersion", "peak tracking"], ["context/projects", "knowledge/projects", "project"]],
        must_cite_like=["project:a5_dot", "context/projects/a5_dot.md", "knowledge/projects/a5_dot.md"],
        evaluator_note="Tests project-context retrieval rather than global moire paper retrieval.",
    ),
    HardTask(
        id="b79_project_context",
        family="project_context",
        task_type="project_status",
        question="For B79, what local project context and measurement observables should be consulted before answering RMCD/PL questions?",
        expected_behavior="answer",
        required_evidence=[["B79"], ["RMCD", "PL", "photoluminescence"]],
        required_answer_concepts=[["B79"], ["RMCD"], ["PL", "photoluminescence"], ["context/projects", "knowledge/projects", "project"]],
        must_cite_like=["project:b79", "context/projects/b79.md", "knowledge/projects/b79.md"],
        evaluator_note="Tests whether project-specific routing survives common optical keywords.",
    ),
    HardTask(
        id="fci_evidence_hierarchy",
        family="multi_hop",
        task_type="synthesis",
        question="Rank evidence types for a fractional Chern insulator and explain what each rules out: transport, compressibility, local probe, optical/RMCD/PL, and thermodynamics.",
        expected_behavior="answer",
        required_evidence=[["fractional Chern"], ["transport"], ["compressibility"], ["local probe"], ["optical", "RMCD", "PL"]],
        required_answer_concepts=[["transport"], ["compressibility"], ["local"], ["optical", "RMCD", "PL"], ["failure mode", "rules out", "artifact"]],
        must_cite_like=["paper:", "claim:", "phenomenon:fqah"],
        evaluator_note="Tests multi-hop synthesis and evidence hierarchy.",
    ),
    HardTask(
        id="optical_control_chern_states",
        family="multi_hop",
        task_type="synthesis",
        question="Summarize what the local knowledge net says about optical control of integer and fractional Chern states. Distinguish passive optical probes from active optical control.",
        expected_behavior="answer",
        required_evidence=[["optical control"], ["optical pumping", "pumping"], ["integer and fractional Chern"], ["passive probe", "primary evidence", "PL", "RMCD"]],
        required_answer_concepts=[["optical control", "active control"], ["optical pumping", "pumping"], ["PL", "RMCD", "probe"], ["integer", "fractional"]],
        must_cite_like=["paper:optical_control", "claim:optical", "claim:promoted"],
        evaluator_note="Tests whether the answer separates probing from manipulation.",
    ),
    HardTask(
        id="minus_one_third_interpretation",
        family="uncertainty",
        task_type="synthesis",
        question="For nu=-1/3 optical FQAH signatures, what competing interpretations or artifacts should be considered, and what evidence would separate them?",
        expected_behavior="caution",
        required_evidence=[["nu=-1/3", "minus one third", "-1/3"], ["PL", "RMCD"], ["topological", "fractional Chern", "FQAH"]],
        required_answer_concepts=[["nu=-1/3", "-1/3"], ["PL", "RMCD"], ["uncertain", "distinguish", "separate"], ["artifact", "inhomogeneity", "CDW", "trivial"]],
        must_cite_like=["claim:promoted_2602", "paper:", "claim:"],
        evaluator_note="Tests uncertainty around optical topological interpretation.",
    ),
    HardTask(
        id="displacement_field_topology",
        family="multi_hop",
        task_type="synthesis",
        question="How does displacement field tune topology in MoTe2/WSe2 or twisted MoTe2 systems, and which observables distinguish QAH, AFM, valley-coherent, and trivial regimes?",
        expected_behavior="answer",
        required_evidence=[["displacement field"], ["QAH"], ["AFM", "antiferromagnetic"], ["valley-coherent", "valley coherent"], ["observable", "RMCD", "transport"]],
        required_answer_concepts=[["displacement field"], ["QAH"], ["AFM", "antiferromagnetic"], ["valley"], ["RMCD", "transport", "PL"]],
        must_cite_like=["claim:", "paper:", "observable:"],
        evaluator_note="Tests mechanism + observable synthesis.",
    ),
    HardTask(
        id="low_conf_superconductivity_arxiv",
        family="freshness",
        task_type="synthesis",
        question="Which low-confidence arXiv leads on superconductivity near fractional Chern states are worth promotion, and what source-reading is required before treating them as lab knowledge?",
        expected_behavior="caution",
        required_evidence=[["superconduct"], ["fractional Chern"], ["low", "arXiv", "promotion"]],
        required_answer_concepts=[["low-confidence", "low confidence", "arXiv"], ["read", "source", "promotion"], ["not settled", "caution", "uncertain"]],
        forbidden_answer_terms=["settled fact", "confirmed lab knowledge"],
        must_cite_like=["paper:arxiv", "question:", "claim:"],
        evaluator_note="Tests freshness, low-confidence handling, and promotion discipline.",
    ),
    HardTask(
        id="b79_exact_curie_temperature_abstain",
        family="abstention",
        task_type="project_status",
        question="What exact Curie temperature did B79 show in the latest local project notes?",
        expected_behavior="abstain",
        required_evidence=[["B79"]],
        required_answer_concepts=[["insufficient", "not enough", "cannot determine", "not in the supplied context"], ["B79"]],
        forbidden_answer_terms=["K", "kelvin", "Curie temperature was"],
        must_cite_like=["B79", "context/projects/b79.md", "knowledge/projects/b79.md"],
        evaluator_note="High score requires abstaining from inventing a numeric temperature.",
    ),
)


def hit_text(hit: dict[str, Any]) -> str:
    return f"{hit.get('id', '')} {hit.get('type', '')} {hit.get('label', '')} {hit.get('summary', '')}"


def dcg(binary_rels: list[int]) -> float:
    return sum((2**rel - 1) / math.log2(rank + 1) for rank, rel in enumerate(binary_rels, start=1))


def retrieval_metrics(task: HardTask, k: int) -> dict[str, Any]:
    started = time.perf_counter()
    hits = fact_graph.task_aware_search(task.question, task_type=task.task_type, limit=max(k, 10))
    latency_ms = (time.perf_counter() - started) * 1000.0
    top = hits[:k]
    matched_groups: set[int] = set()
    hit_rels = []
    first_relevant = None
    forbidden_hits = []

    for rank, hit in enumerate(top, start=1):
        text = hit_text(hit)
        groups_here = [idx for idx, group in enumerate(task.required_evidence) if group_hit(text, group)]
        if groups_here:
            matched_groups.update(groups_here)
            if first_relevant is None:
                first_relevant = rank
        hit_rels.append(1 if groups_here else 0)
        for forbidden in task.forbidden_retrieval_terms:
            if normalize(forbidden) in normalize(text):
                forbidden_hits.append({"rank": rank, "term": forbidden, "id": hit.get("id"), "label": hit.get("label")})

    ideal_rels = [1] * min(len(task.required_evidence), k)
    ndcg = dcg(hit_rels) / dcg(ideal_rels) if ideal_rels else 1.0
    ndcg = min(1.0, ndcg)
    relevant_hits = sum(hit_rels)
    return {
        "latency_ms": latency_ms,
        "hits": hits,
        "recall_at_k": len(matched_groups) / len(task.required_evidence) if task.required_evidence else 1.0,
        "precision_at_k": relevant_hits / len(top) if top else 0.0,
        "mrr": 1.0 / first_relevant if first_relevant else 0.0,
        "ndcg_at_k": ndcg,
        "first_relevant_rank": first_relevant,
        "matched_evidence_groups": sorted(matched_groups),
        "missed_evidence_groups": [idx for idx in range(len(task.required_evidence)) if idx not in matched_groups],
        "forbidden_retrieval_hits": forbidden_hits,
        "top_hit_labels": [hit.get("label") for hit in top],
    }


def context_metrics(task: HardTask, char_budget: int) -> tuple[dict[str, Any], str, Any]:
    started = time.perf_counter()
    pack, markdown = build_context_pack(
        task_type=task.task_type,
        query=task.question,
        char_budget=char_budget,
        write=False,
    )
    latency_ms = (time.perf_counter() - started) * 1000.0
    matched_groups: set[int] = set()
    item_rels: list[int] = []
    relevant_precisions: list[float] = []
    relevant_so_far = 0

    for rank, item in enumerate(pack.items, start=1):
        text = f"{item.id} {item.path or ''} {item.content}"
        groups_here = [idx for idx, group in enumerate(task.required_evidence) if group_hit(text, group)]
        if groups_here:
            matched_groups.update(groups_here)
            item_rels.append(1)
            relevant_so_far += 1
            relevant_precisions.append(relevant_so_far / rank)
        else:
            item_rels.append(0)

    context_precision = statistics.mean(relevant_precisions) if relevant_precisions else 0.0
    context_recall = len(matched_groups) / len(task.required_evidence) if task.required_evidence else 1.0
    context_text = "\n".join(item.content for item in pack.items)
    return (
        {
            "latency_ms": latency_ms,
            "context_pack_id": pack.context_pack_id,
            "chars": pack.metrics["chars"],
            "token_estimate": pack.metrics["token_estimate"],
            "item_count": pack.metrics["item_count"],
            "excluded_count": pack.metrics["excluded_count"],
            "context_precision": context_precision,
            "context_recall": context_recall,
            "matched_evidence_groups": sorted(matched_groups),
            "missed_evidence_groups": [idx for idx in range(len(task.required_evidence)) if idx not in matched_groups],
            "kind_counts": dict(Counter(item.kind for item in pack.items)),
            "items": [item.public_dict() for item in pack.items],
            "context_refs": sorted(extract_refs(context_text) | {item.id for item in pack.items} | {item.path for item in pack.items if item.path}),
        },
        markdown,
        pack,
    )


REF_PATTERN = re.compile(
    r"\b(?:claim|paper|project|evidence|question|phenomenon|observable|mechanism|concept|edge):[A-Za-z0-9_.:-]+"
    r"|(?:lab_assistant/)?(?:knowledge|context|graph|skills)/[A-Za-z0-9_./#:-]+"
)


def extract_refs(text: str) -> set[str]:
    return {match.group(0).rstrip(".,);]") for match in REF_PATTERN.finditer(text)}


def split_claim_like_sentences(answer: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", answer.replace("\n", " "))
    out = []
    for sentence in sentences:
        clean = sentence.strip(" -*\t")
        if len(clean) < 35:
            continue
        if clean.lower().startswith(("uncertainty", "observation", "inference", "answer", "evidence")):
            continue
        out.append(clean)
    return out


STOPWORDS = {
    "the",
    "and",
    "that",
    "with",
    "this",
    "from",
    "into",
    "before",
    "after",
    "should",
    "would",
    "could",
    "there",
    "their",
    "about",
    "using",
    "only",
    "local",
    "context",
    "evidence",
    "claim",
    "answer",
}


def content_tokens(text: str) -> set[str]:
    return {token for token in normalize(text).split() if len(token) > 3 and token not in STOPWORDS}


def deterministic_answer_metrics(task: HardTask, answer: str, context_markdown: str, context_refs: set[str]) -> dict[str, Any]:
    concept_hits: set[int] = set()
    for idx, group in enumerate(task.required_answer_concepts):
        if group_hit(answer, group):
            concept_hits.add(idx)
    forbidden_hits = [term for term in task.forbidden_answer_terms if normalize(term) in normalize(answer)]
    citations = extract_refs(answer)
    citation_hits = [ref for ref in citations if ref in context_refs or ref.replace("lab_assistant/", "") in context_refs]
    citation_precision = len(citation_hits) / len(citations) if citations else 0.0
    must_cite_hits = [term for term in task.must_cite_like if normalize(term) in normalize(answer)]
    answer_norm = normalize(answer)
    caution_phrases = ["insufficient", "not enough", "uncertain", "cannot determine", "not settled", "requires follow up", "needs follow up"]
    behavior_ok = True
    if task.expected_behavior in {"caution", "abstain"}:
        behavior_ok = any(phrase in answer_norm for phrase in caution_phrases)
    if task.expected_behavior == "abstain":
        number_pattern = re.compile(r"\b\d+(?:\.\d+)?\s*(?:k|kelvin)\b", re.IGNORECASE)
        behavior_ok = behavior_ok and not bool(number_pattern.search(answer))

    context_tokens = content_tokens(context_markdown)
    claim_support_rows = []
    for sentence in split_claim_like_sentences(answer):
        tokens = content_tokens(sentence)
        overlap = len(tokens & context_tokens)
        has_ref = bool(extract_refs(sentence))
        supported = has_ref or (len(tokens) > 0 and overlap / max(1, min(len(tokens), 12)) >= 0.30)
        claim_support_rows.append({"sentence": sentence, "supported_proxy": supported, "overlap": overlap, "has_ref": has_ref})
    atomic_support_proxy = (
        sum(1 for row in claim_support_rows if row["supported_proxy"]) / len(claim_support_rows)
        if claim_support_rows
        else 0.0
    )

    return {
        "required_concept_coverage": len(concept_hits) / len(task.required_answer_concepts) if task.required_answer_concepts else 1.0,
        "matched_concept_groups": sorted(concept_hits),
        "missed_concept_groups": [idx for idx in range(len(task.required_answer_concepts)) if idx not in concept_hits],
        "forbidden_answer_hits": forbidden_hits,
        "citation_count": len(citations),
        "citation_precision_proxy": citation_precision,
        "citations": sorted(citations),
        "citation_hits": sorted(citation_hits),
        "must_cite_like_coverage": len(must_cite_hits) / len(task.must_cite_like) if task.must_cite_like else 1.0,
        "matched_must_cite_like": must_cite_hits,
        "behavior_ok": behavior_ok,
        "atomic_claim_count": len(claim_support_rows),
        "atomic_support_proxy": atomic_support_proxy,
        "claim_support_proxy_rows": claim_support_rows,
    }


JUDGE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "context_relevance": {"type": "integer", "minimum": 1, "maximum": 5},
        "answer_relevance": {"type": "integer", "minimum": 1, "maximum": 5},
        "faithfulness": {"type": "integer", "minimum": 1, "maximum": 5},
        "citation_quality": {"type": "integer", "minimum": 1, "maximum": 5},
        "scientific_correctness": {"type": "integer", "minimum": 1, "maximum": 5},
        "uncertainty_calibration": {"type": "integer", "minimum": 1, "maximum": 5},
        "actionability": {"type": "integer", "minimum": 1, "maximum": 5},
        "unsupported_claims_count": {"type": "integer", "minimum": 0},
        "critical_errors": {"type": "array", "items": {"type": "string"}},
        "missing_key_points": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": [
        "context_relevance",
        "answer_relevance",
        "faithfulness",
        "citation_quality",
        "scientific_correctness",
        "uncertainty_calibration",
        "actionability",
        "unsupported_claims_count",
        "critical_errors",
        "missing_key_points",
        "summary",
    ],
}


def codex_exec(prompt: str, output_path: Path, timeout_s: int, schema_path: Path | None = None) -> tuple[int | None, float, str, str]:
    cmd = [
        "codex",
        "-a",
        "never",
        "exec",
        "-C",
        str(PACKAGE_ROOT),
        "-s",
        "read-only",
        "--ephemeral",
        "-o",
        str(output_path),
    ]
    if schema_path is not None:
        cmd.extend(["--output-schema", str(schema_path)])
    cmd.append("-")
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            cwd=PACKAGE_ROOT,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return proc.returncode, elapsed_ms, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return None, elapsed_ms, exc.stdout or "", exc.stderr or f"timeout after {timeout_s}s"


def answer_prompt(task: HardTask, context_markdown: str) -> str:
    return f"""You are an OpenScience RAG answerer under evaluation.

Use only the supplied context. Do not run commands. Do not browse. If the context is insufficient, say so explicitly.
Keep the answer concise but complete enough for a lab PI.

Required style:
- Use three labeled sections: Observation, Inference, Uncertainty.
- Cite graph node IDs or local file paths for factual claims whenever possible.
- Separate evidence from inference.
- Do not invent numeric values, paper titles, project results, or source claims not present in the context.

Question:
{task.question}

Expected behavior for this evaluation: {task.expected_behavior}
Evaluator note: {task.evaluator_note}

<context>
{context_markdown[:22000]}
</context>
"""


def judge_prompt(task: HardTask, context_markdown: str, answer: str) -> str:
    return f"""You are a strict evaluator of a scientific RAG system.

Judge only against the supplied context and task rubric. Penalize unsupported claims, missing caveats, bad citations, and overconfident statements.
Use this 1-5 scale for each metric:
1 = poor / unsafe, 3 = partially acceptable but important gaps, 5 = strong.

Metrics:
- context_relevance: did retrieved context contain the needed evidence?
- answer_relevance: did the answer address the user question?
- faithfulness: were answer claims supported by the context?
- citation_quality: were citations specific, useful, and attached to the right claims?
- scientific_correctness: was the scientific interpretation defensible from context?
- uncertainty_calibration: did it avoid overclaiming and abstain when needed?
- actionability: did it give the next useful scientific action when appropriate?

Task ID: {task.id}
Question: {task.question}
Expected behavior: {task.expected_behavior}
Required answer concepts: {task.required_answer_concepts}
Forbidden answer terms: {task.forbidden_answer_terms}
Evaluator note: {task.evaluator_note}

<context>
{context_markdown[:18000]}
</context>

<answer>
{answer[:9000]}
</answer>

Return JSON matching the requested schema. No markdown.
"""


def parse_judge(path: Path, stdout: str) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else stdout
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "context_relevance": 1,
        "answer_relevance": 1,
        "faithfulness": 1,
        "citation_quality": 1,
        "scientific_correctness": 1,
        "uncertainty_calibration": 1,
        "actionability": 1,
        "unsupported_claims_count": 99,
        "critical_errors": ["judge output was not parseable JSON"],
        "missing_key_points": [],
        "summary": text[:500],
    }


def compute_scores(row: dict[str, Any]) -> dict[str, float]:
    retrieval = row["retrieval"]
    context = row["context"]
    answer = row["answer_metrics"]
    judge = row["judge"]
    no_retrieval_negatives = 1.0 if not retrieval["forbidden_retrieval_hits"] else 0.0
    retrieval_score = statistics.mean(
        [
            min(1.0, retrieval["recall_at_k"]),
            min(1.0, retrieval["precision_at_k"]),
            min(1.0, retrieval["mrr"]),
            min(1.0, retrieval["ndcg_at_k"]),
            no_retrieval_negatives,
        ]
    )
    context_score = statistics.mean([min(1.0, context["context_recall"]), min(1.0, context["context_precision"])])
    no_answer_forbidden = 1.0 if not answer["forbidden_answer_hits"] else 0.0
    answer_score = statistics.mean(
        [
            answer["required_concept_coverage"],
            answer["citation_precision_proxy"],
            answer["must_cite_like_coverage"],
            1.0 if answer["behavior_ok"] else 0.0,
            answer["atomic_support_proxy"],
            no_answer_forbidden,
        ]
    )
    judge_metrics = [
        "context_relevance",
        "answer_relevance",
        "faithfulness",
        "citation_quality",
        "scientific_correctness",
        "uncertainty_calibration",
        "actionability",
    ]
    judge_score = statistics.mean(float(judge.get(metric, 1)) / 5.0 for metric in judge_metrics)
    overall = statistics.mean([retrieval_score, context_score, answer_score, judge_score])
    return {
        "retrieval_score": retrieval_score,
        "context_score": context_score,
        "answer_deterministic_score": answer_score,
        "judge_score": judge_score,
        "overall_score": overall,
    }


def run_task(task: HardTask, output_dir: Path, top_k: int, char_budget: int, timeout_s: int, schema_path: Path) -> dict[str, Any]:
    slug = task_slug(task.id)
    task_dir = output_dir / "raw" / "tasks" / slug
    task_dir.mkdir(parents=True, exist_ok=True)

    retrieval = retrieval_metrics(task, top_k)
    context, context_markdown, pack = context_metrics(task, char_budget)
    (task_dir / "context.md").write_text(context_markdown, encoding="utf-8")
    write_json(task_dir / "retrieval.json", retrieval)
    write_json(task_dir / "context.json", {k: v for k, v in context.items() if k != "items"})

    answer_path = task_dir / "answer.md"
    answer_stdout = task_dir / "answer.stdout.txt"
    answer_stderr = task_dir / "answer.stderr.txt"
    returncode, answer_latency_ms, stdout, stderr = codex_exec(
        answer_prompt(task, context_markdown),
        answer_path,
        timeout_s=timeout_s,
    )
    answer_stdout.write_text(stdout, encoding="utf-8")
    answer_stderr.write_text(stderr, encoding="utf-8")
    answer = answer_path.read_text(encoding="utf-8", errors="replace") if answer_path.exists() else stdout
    answer_metrics = deterministic_answer_metrics(task, answer, context_markdown, set(context["context_refs"]))

    judge_path = task_dir / "judge.json"
    judge_stdout = task_dir / "judge.stdout.txt"
    judge_stderr = task_dir / "judge.stderr.txt"
    judge_returncode, judge_latency_ms, judge_out, judge_err = codex_exec(
        judge_prompt(task, context_markdown, answer),
        judge_path,
        timeout_s=timeout_s,
        schema_path=schema_path,
    )
    judge_stdout.write_text(judge_out, encoding="utf-8")
    judge_stderr.write_text(judge_err, encoding="utf-8")
    judge = parse_judge(judge_path, judge_out)
    scores = compute_scores(
        {
            "retrieval": retrieval,
            "context": context,
            "answer_metrics": answer_metrics,
            "judge": judge,
        }
    )

    row = {
        "id": task.id,
        "family": task.family,
        "task_type": task.task_type,
        "question": task.question,
        "expected_behavior": task.expected_behavior,
        "evaluator_note": task.evaluator_note,
        "retrieval": {k: v for k, v in retrieval.items() if k != "hits"},
        "context": {k: v for k, v in context.items() if k not in {"items", "context_refs"}},
        "answer_metrics": answer_metrics,
        "judge": judge,
        "scores": scores,
        "answer_returncode": returncode,
        "judge_returncode": judge_returncode,
        "answer_latency_ms": answer_latency_ms,
        "judge_latency_ms": judge_latency_ms,
        "answer_path": str(answer_path.relative_to(output_dir)),
        "judge_path": str(judge_path.relative_to(output_dir)),
        "context_path": str((task_dir / "context.md").relative_to(output_dir)),
    }
    write_json(task_dir / "record.json", row)
    return row


def run_task_repeat(
    task: HardTask,
    output_dir: Path,
    top_k: int,
    char_budget: int,
    timeout_s: int,
    schema_path: Path,
    run_index: int,
    repeats: int,
) -> dict[str, Any]:
    """Run one task once, storing artifacts under a repeat-specific directory."""
    if repeats <= 1:
        return run_task(task, output_dir, top_k, char_budget, timeout_s, schema_path)

    slug = task_slug(task.id)
    task_dir = output_dir / "raw" / "tasks" / slug / f"run_{run_index:03d}"
    task_dir.mkdir(parents=True, exist_ok=True)

    retrieval = retrieval_metrics(task, top_k)
    context, context_markdown, _pack = context_metrics(task, char_budget)
    (task_dir / "context.md").write_text(context_markdown, encoding="utf-8")
    write_json(task_dir / "retrieval.json", retrieval)
    write_json(task_dir / "context.json", {k: v for k, v in context.items() if k != "items"})

    answer_path = task_dir / "answer.md"
    answer_stdout = task_dir / "answer.stdout.txt"
    answer_stderr = task_dir / "answer.stderr.txt"
    returncode, answer_latency_ms, stdout, stderr = codex_exec(
        answer_prompt(task, context_markdown),
        answer_path,
        timeout_s=timeout_s,
    )
    answer_stdout.write_text(stdout, encoding="utf-8")
    answer_stderr.write_text(stderr, encoding="utf-8")
    answer = answer_path.read_text(encoding="utf-8", errors="replace") if answer_path.exists() else stdout
    answer_metrics = deterministic_answer_metrics(task, answer, context_markdown, set(context["context_refs"]))

    judge_path = task_dir / "judge.json"
    judge_stdout = task_dir / "judge.stdout.txt"
    judge_stderr = task_dir / "judge.stderr.txt"
    judge_returncode, judge_latency_ms, judge_out, judge_err = codex_exec(
        judge_prompt(task, context_markdown, answer),
        judge_path,
        timeout_s=timeout_s,
        schema_path=schema_path,
    )
    judge_stdout.write_text(judge_out, encoding="utf-8")
    judge_stderr.write_text(judge_err, encoding="utf-8")
    judge = parse_judge(judge_path, judge_out)
    scores = compute_scores(
        {
            "retrieval": retrieval,
            "context": context,
            "answer_metrics": answer_metrics,
            "judge": judge,
        }
    )

    row = {
        "id": task.id,
        "run_index": run_index,
        "run_id": f"{task.id}__run_{run_index:03d}",
        "family": task.family,
        "task_type": task.task_type,
        "question": task.question,
        "expected_behavior": task.expected_behavior,
        "evaluator_note": task.evaluator_note,
        "retrieval": {k: v for k, v in retrieval.items() if k != "hits"},
        "context": {k: v for k, v in context.items() if k not in {"items", "context_refs"}},
        "answer_metrics": answer_metrics,
        "judge": judge,
        "scores": scores,
        "answer_returncode": returncode,
        "judge_returncode": judge_returncode,
        "answer_latency_ms": answer_latency_ms,
        "judge_latency_ms": judge_latency_ms,
        "answer_path": str(answer_path.relative_to(output_dir)),
        "judge_path": str(judge_path.relative_to(output_dir)),
        "context_path": str((task_dir / "context.md").relative_to(output_dir)),
    }
    write_json(task_dir / "record.json", row)
    return row


def mean_stats(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None, "std": None, "ci95": None, "min": None, "max": None}
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    ci95 = 1.96 * std / math.sqrt(len(values)) if len(values) > 1 else 0.0
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "std": std,
        "ci95": ci95,
        "min": min(values),
        "max": max(values),
    }


def failure_flags(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "retrieval_miss": row["retrieval"]["recall_at_k"] < 1,
        "hard_negative_leak": bool(row["retrieval"]["forbidden_retrieval_hits"]),
        "context_miss": row["context"]["context_recall"] < 1,
        "answer_concept_miss": row["answer_metrics"]["required_concept_coverage"] < 1,
        "bad_abstention_or_caution": not row["answer_metrics"]["behavior_ok"],
        "weak_citation_precision_proxy": row["answer_metrics"]["citation_precision_proxy"] < 0.8,
        "judge_faithfulness_under_4": row["judge"].get("faithfulness", 1) < 4,
        "judge_citation_under_4": row["judge"].get("citation_quality", 1) < 4,
        "judge_critical_errors": bool(row["judge"].get("critical_errors")),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    family_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    task_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        family_rows[row["family"]].append(row)
        task_rows[row["id"]].append(row)
    score_keys = ["overall_score", "retrieval_score", "context_score", "answer_deterministic_score", "judge_score"]
    summary = {
        "runs": len(rows),
        "unique_tasks": len(task_rows),
        "repeats_per_task": {task_id: len(group) for task_id, group in sorted(task_rows.items())},
        "overall_mean": statistics.mean(row["scores"]["overall_score"] for row in rows) if rows else 0.0,
        "overall_median": statistics.median(row["scores"]["overall_score"] for row in rows) if rows else 0.0,
        "overall": mean_stats([row["scores"]["overall_score"] for row in rows]),
        "score_means": {
            key: statistics.mean(row["scores"][key] for row in rows) if rows else 0.0
            for key in score_keys
        },
        "judge_metric_means": {
            metric: statistics.mean(float(row["judge"].get(metric, 1)) for row in rows) if rows else 0.0
            for metric in [
                "context_relevance",
                "answer_relevance",
                "faithfulness",
                "citation_quality",
                "scientific_correctness",
                "uncertainty_calibration",
                "actionability",
            ]
        },
        "by_family": {},
        "by_task": {},
        "failure_counts": Counter(),
        "failure_rates": {},
        "latency": {
            "answer_p50_s": percentile([row["answer_latency_ms"] / 1000 for row in rows], 50),
            "answer_p95_s": percentile([row["answer_latency_ms"] / 1000 for row in rows], 95),
            "judge_p50_s": percentile([row["judge_latency_ms"] / 1000 for row in rows], 50),
            "judge_p95_s": percentile([row["judge_latency_ms"] / 1000 for row in rows], 95),
        },
    }
    for family, group in sorted(family_rows.items()):
        summary["by_family"][family] = {
            "runs": len(group),
            "unique_tasks": len({row["id"] for row in group}),
            **{key: statistics.mean(row["scores"][key] for row in group) for key in score_keys},
        }
    for task_id, group in sorted(task_rows.items()):
        task_failure_counts: Counter[str] = Counter()
        for row in group:
            for key, value in failure_flags(row).items():
                if value:
                    task_failure_counts[key] += 1
        summary["by_task"][task_id] = {
            "runs": len(group),
            "family": group[0]["family"],
            "task_type": group[0]["task_type"],
            "score_stats": {key: mean_stats([row["scores"][key] for row in group]) for key in score_keys},
            "judge_metric_stats": {
                metric: mean_stats([float(row["judge"].get(metric, 1)) for row in group])
                for metric in [
                    "context_relevance",
                    "answer_relevance",
                    "faithfulness",
                    "citation_quality",
                    "scientific_correctness",
                    "uncertainty_calibration",
                    "actionability",
                ]
            },
            "failure_counts": dict(task_failure_counts),
            "failure_rates": {key: value / len(group) for key, value in sorted(task_failure_counts.items())},
            "answer_latency_s": mean_stats([row["answer_latency_ms"] / 1000 for row in group]),
            "judge_latency_s": mean_stats([row["judge_latency_ms"] / 1000 for row in group]),
        }
    for row in rows:
        for key, value in failure_flags(row).items():
            if value:
                summary["failure_counts"][key] += 1
    summary["failure_counts"] = dict(summary["failure_counts"])
    summary["failure_rates"] = {key: value / len(rows) for key, value in summary["failure_counts"].items()} if rows else {}
    return summary


def plot_bar(path: Path, labels: list[str], values: list[float], title: str, ylabel: str, ylim: tuple[float, float] | None = None, color: str = "#3969ac") -> None:
    if plt is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 0.62), 4.6))
    ax.bar(labels, values, color=color)
    ax.set_title(title, fontsize=14)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(axis="y", alpha=0.22)
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def make_plots(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    if plt is None:
        return
    plot_dir = output_dir / "plots"
    task_ids = list(summary["by_task"].keys())
    task_labels = [task_id.replace("_", "\n") for task_id in task_ids]
    means = [summary["by_task"][task_id]["score_stats"]["overall_score"]["mean"] for task_id in task_ids]
    cis = [summary["by_task"][task_id]["score_stats"]["overall_score"]["ci95"] for task_id in task_ids]
    fig, ax = plt.subplots(figsize=(max(9.5, len(task_ids) * 0.78), 5.0))
    ax.bar(task_labels, means, yerr=cis, color="#3969ac", capsize=3)
    ax.set_title("Hard RAG Quality Score by Task")
    ax.set_ylabel("mean score (0-1), 95% CI")
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.22)
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    fig.tight_layout()
    fig.savefig(plot_dir / "overall_quality_by_task.png", dpi=220)
    plt.close(fig)

    grouped_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped_rows[row["id"]].append(row)
    fig, ax = plt.subplots(figsize=(max(9.5, len(task_ids) * 0.78), 5.0))
    ax.boxplot(
        [[row["scores"]["overall_score"] for row in grouped_rows[task_id]] for task_id in task_ids],
        tick_labels=task_labels,
        showfliers=False,
    )
    ax.set_title("Hard RAG Quality Score Distribution by Task")
    ax.set_ylabel("score (0-1)")
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.22)
    ax.tick_params(axis="x", rotation=35, labelsize=8)
    fig.tight_layout()
    fig.savefig(plot_dir / "overall_quality_distribution_by_task.png", dpi=220)
    plt.close(fig)

    layer_labels = ["retrieval", "context", "answer", "judge"]
    layer_values = [
        summary["score_means"]["retrieval_score"],
        summary["score_means"]["context_score"],
        summary["score_means"]["answer_deterministic_score"],
        summary["score_means"]["judge_score"],
    ]
    plot_bar(
        plot_dir / "pipeline_layer_scores.png",
        layer_labels,
        layer_values,
        "Mean Score by RAG Pipeline Layer",
        "score (0-1)",
        (0, 1.0),
        "#4b8f8c",
    )

    judge_metrics = [
        "context_relevance",
        "answer_relevance",
        "faithfulness",
        "citation_quality",
        "scientific_correctness",
        "uncertainty_calibration",
        "actionability",
    ]
    fig, ax = plt.subplots(figsize=(9.6, max(5, len(task_ids) * 0.42)))
    matrix = [
        [summary["by_task"][task_id]["judge_metric_stats"][metric]["mean"] for metric in judge_metrics]
        for task_id in task_ids
    ]
    cmap = LinearSegmentedColormap.from_list("quality", ["#cc503e", "#f1d36b", "#4b8f8c"])
    im = ax.imshow(matrix, vmin=1, vmax=5, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(judge_metrics)), [metric.replace("_", "\n") for metric in judge_metrics], fontsize=8)
    ax.set_yticks(range(len(task_ids)), task_ids, fontsize=8)
    ax.set_title("Mean LLM Judge Scores by Task")
    for y, row_vals in enumerate(matrix):
        for x, value in enumerate(row_vals):
            ax.text(x, y, f"{value:.1f}", ha="center", va="center", fontsize=7, color="black")
    fig.colorbar(im, ax=ax, label="judge score (1-5)")
    fig.tight_layout()
    fig.savefig(plot_dir / "judge_metric_heatmap.png", dpi=220)
    plt.close(fig)

    failure_counts = summary["failure_counts"]
    plot_bar(
        plot_dir / "failure_taxonomy.png",
        list(failure_counts.keys()),
        [float(value) for value in failure_counts.values()],
        "Failure Taxonomy Across Hard Runs",
        "run count",
        None,
        "#cc503e",
    )

    failure_keys = sorted(summary["failure_counts"])
    if failure_keys:
        fig, ax = plt.subplots(figsize=(max(9.5, len(task_ids) * 0.8), max(4.8, len(failure_keys) * 0.36)))
        matrix = [
            [summary["by_task"][task_id]["failure_rates"].get(key, 0.0) for key in failure_keys]
            for task_id in task_ids
        ]
        cmap = LinearSegmentedColormap.from_list("failures", ["#f7f7f7", "#f1d36b", "#cc503e"])
        im = ax.imshow(matrix, vmin=0, vmax=1, cmap=cmap, aspect="auto")
        ax.set_xticks(range(len(failure_keys)), [key.replace("_", "\n") for key in failure_keys], fontsize=7)
        ax.set_yticks(range(len(task_ids)), task_ids, fontsize=8)
        ax.set_title("Failure Rate by Task")
        for y, row_vals in enumerate(matrix):
            for x, value in enumerate(row_vals):
                if value:
                    ax.text(x, y, f"{value:.0%}", ha="center", va="center", fontsize=7, color="black")
        fig.colorbar(im, ax=ax, label="failure rate")
        fig.tight_layout()
        fig.savefig(plot_dir / "failure_rate_by_task.png", dpi=220)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.scatter(
        [row["context"]["context_recall"] for row in rows],
        [float(row["judge"].get("faithfulness", 1)) / 5.0 for row in rows],
        s=42,
        color="#3969ac",
        alpha=0.42,
    )
    ax.set_xlabel("context recall")
    ax.set_ylabel("judge faithfulness (0-1)")
    ax.set_title("Context Recall vs Answer Faithfulness")
    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(0, 1.04)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(plot_dir / "context_recall_vs_faithfulness.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(max(9.5, len(task_ids) * 0.78), 5.0))
    positions = []
    data = []
    labels = []
    for idx, task_id in enumerate(task_ids, start=1):
        positions.extend([idx * 3 - 1, idx * 3])
        data.extend(
            [
                [row["answer_latency_ms"] / 1000 for row in grouped_rows[task_id]],
                [row["judge_latency_ms"] / 1000 for row in grouped_rows[task_id]],
            ]
        )
        labels.extend(["answer", "judge"])
    bp = ax.boxplot(data, positions=positions, widths=0.7, patch_artist=True, showfliers=False)
    for patch, label in zip(bp["boxes"], labels):
        patch.set_facecolor("#3969ac" if label == "answer" else "#cc503e")
        patch.set_alpha(0.75)
    ax.set_xticks([idx * 3 - 0.5 for idx in range(1, len(task_ids) + 1)], task_labels, rotation=35, fontsize=7)
    ax.set_ylabel("seconds")
    ax.set_title("Codex Answer and Judge Latency by Task")
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(plot_dir / "answer_judge_latency.png", dpi=220)
    plt.close(fig)

    score_keys = ["retrieval_score", "context_score", "answer_deterministic_score", "judge_score"]
    fig, ax = plt.subplots(figsize=(max(9.5, len(task_ids) * 0.8), 5.4))
    x = range(len(task_ids))
    width = 0.18
    colors = ["#3969ac", "#4b8f8c", "#f1d36b", "#cc503e"]
    for offset, (score_key, color) in enumerate(zip(score_keys, colors)):
        ax.bar(
            [val + (offset - 1.5) * width for val in x],
            [summary["by_task"][task_id]["score_stats"][score_key]["mean"] for task_id in task_ids],
            width=width,
            label=score_key.replace("_score", ""),
            color=color,
        )
    ax.set_xticks(list(x), task_labels, rotation=35, fontsize=7)
    ax.set_ylabel("mean score (0-1)")
    ax.set_ylim(0, 1.0)
    ax.set_title("Pipeline Layer Scores by Task")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(plot_dir / "pipeline_layer_scores_by_task.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.hist(
        [row["scores"]["overall_score"] for row in rows],
        bins=12,
        color="#3969ac",
        alpha=0.82,
        edgecolor="white",
    )
    ax.set_xlabel("overall score")
    ax.set_ylabel("run count")
    ax.set_title("Overall Score Distribution Across Runs")
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(plot_dir / "overall_score_histogram.png", dpi=220)
    plt.close(fig)


def write_reports(output_dir: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Hard RAG Quality Benchmark",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## What This Measures",
        "- Retrieval ranking: recall@10, precision@10, MRR, nDCG@10, and hard-negative leakage.",
        "- Context quality: whether packed context contains the needed evidence and ranks relevant chunks early.",
        "- Answer quality: required scientific concepts, abstention/caution behavior, citation usage, and a lightweight atomic-support proxy.",
        "- Judge quality: Codex-as-judge scores for context relevance, answer relevance, faithfulness, citation quality, scientific correctness, uncertainty calibration, and actionability.",
        "",
        "## Literature Mapping",
    ]
    for item in LITERATURE_NOTES:
        lines.append(f"- [{item['name']}]({item['url']}): {item['local_use']}.")
    lines.extend(
        [
            "",
            "## Executive Summary",
            f"- Hard benchmark runs: {summary['runs']} total across {summary['unique_tasks']} unique tasks.",
            f"- Overall mean score: {summary['overall_mean']:.3f} +/- {summary['overall']['ci95']:.3f} 95% CI.",
            f"- Retrieval score: {summary['score_means']['retrieval_score']:.3f}",
            f"- Context score: {summary['score_means']['context_score']:.3f}",
            f"- Deterministic answer score: {summary['score_means']['answer_deterministic_score']:.3f}",
            f"- LLM judge score: {summary['score_means']['judge_score']:.3f}",
            f"- Answer latency p50/p95: {summary['latency']['answer_p50_s']:.1f}s / {summary['latency']['answer_p95_s']:.1f}s",
            f"- Judge latency p50/p95: {summary['latency']['judge_p50_s']:.1f}s / {summary['latency']['judge_p95_s']:.1f}s",
            "",
            "## Layer Scores",
        ]
    )
    for key, value in summary["score_means"].items():
        lines.append(f"- `{key}`: {value:.3f}")
    lines.extend(["", "## Judge Metric Means"])
    for key, value in summary["judge_metric_means"].items():
        lines.append(f"- `{key}`: {value:.2f}/5")
    lines.extend(["", "## Scores By Family"])
    for family, stats in summary["by_family"].items():
        lines.append(f"- `{family}` ({stats['runs']} runs, {stats['unique_tasks']} tasks): overall {stats['overall_score']:.3f}, retrieval {stats['retrieval_score']:.3f}, context {stats['context_score']:.3f}, answer {stats['answer_deterministic_score']:.3f}, judge {stats['judge_score']:.3f}")
    lines.extend(["", "## Failure Taxonomy"])
    for key, value in sorted(summary["failure_counts"].items()):
        lines.append(f"- `{key}`: {value}/{summary['runs']} runs ({value / summary['runs']:.1%})")
    lines.extend(["", "## Per-Task Aggregate Findings"])
    grouped_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped_rows[row["id"]].append(row)
    for task_id, stats in summary["by_task"].items():
        worst = min(grouped_rows[task_id], key=lambda row: row["scores"]["overall_score"])
        best = max(grouped_rows[task_id], key=lambda row: row["scores"]["overall_score"])
        overall = stats["score_stats"]["overall_score"]
        retrieval = stats["score_stats"]["retrieval_score"]
        context = stats["score_stats"]["context_score"]
        answer_score = stats["score_stats"]["answer_deterministic_score"]
        judge_score = stats["score_stats"]["judge_score"]
        lines.append(f"### {task_id}")
        lines.append(
            f"- Overall: {overall['mean']:.3f} +/- {overall['ci95']:.3f} 95% CI "
            f"(min {overall['min']:.3f}, max {overall['max']:.3f}, n={stats['runs']})."
        )
        lines.append(
            f"- Layers: retrieval {retrieval['mean']:.3f}, context {context['mean']:.3f}, "
            f"answer {answer_score['mean']:.3f}, judge {judge_score['mean']:.3f}."
        )
        if stats["failure_rates"]:
            failures = ", ".join(f"{key} {value:.0%}" for key, value in sorted(stats["failure_rates"].items()))
            lines.append(f"- Failure rates: {failures}.")
        else:
            lines.append("- Failure rates: none under current flags.")
        lines.append(
            f"- Judge means: faithfulness {stats['judge_metric_stats']['faithfulness']['mean']:.2f}/5, "
            f"citation {stats['judge_metric_stats']['citation_quality']['mean']:.2f}/5, "
            f"uncertainty {stats['judge_metric_stats']['uncertainty_calibration']['mean']:.2f}/5."
        )
        lines.append(f"- Worst run: `{worst.get('run_id', worst['id'])}` score {worst['scores']['overall_score']:.3f}; answer `{worst['answer_path']}`.")
        lines.append(f"- Best run: `{best.get('run_id', best['id'])}` score {best['scores']['overall_score']:.3f}; answer `{best['answer_path']}`.")
        lines.append("")
    lines.extend(
        [
            "## Presentation Plots",
            "- `plots/overall_quality_by_task.png`",
            "- `plots/overall_quality_distribution_by_task.png`",
            "- `plots/pipeline_layer_scores.png`",
            "- `plots/pipeline_layer_scores_by_task.png`",
            "- `plots/judge_metric_heatmap.png`",
            "- `plots/failure_taxonomy.png`",
            "- `plots/failure_rate_by_task.png`",
            "- `plots/context_recall_vs_faithfulness.png`",
            "- `plots/overall_score_histogram.png`",
            "- `plots/answer_judge_latency.png`",
        ]
    )
    (report_dir / "hard_quality_report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    slide_lines = [
        "# Presentation Outline: Current RAG Quality",
        "",
        "## Slide 1: Evaluation Design",
        "- Literature-inspired axes: retrieval ranking, context relevance/recall, faithfulness, citation support, abstention.",
        f"- {summary['runs']} answer-level runs across {summary['unique_tasks']} hard local scientific tasks spanning project context, hard negatives, multi-hop synthesis, freshness, and abstention.",
        "",
        "## Slide 2: Overall Pipeline Scores",
        "- Use `plots/pipeline_layer_scores.png`.",
        "- Takeaway: this separates retrieval failures from context and generation failures.",
        "",
        "## Slide 3: Task-Level Scorecard",
        "- Use `plots/overall_quality_by_task.png`.",
        "- Use error bars to show run-to-run variability.",
        "",
        "## Slide 4: Score Distributions",
        "- Use `plots/overall_quality_distribution_by_task.png` and `plots/overall_score_histogram.png`.",
        "- Highlight low-scoring tasks as concrete weak spots.",
        "",
        "## Slide 5: Judge Heatmap",
        "- Use `plots/judge_metric_heatmap.png`.",
        "- Discuss faithfulness/citation/uncertainty rather than only hit rate.",
        "",
        "## Slide 6: Failure Taxonomy",
        "- Use `plots/failure_taxonomy.png`.",
        "- Use `plots/failure_rate_by_task.png` for task-specific reliability.",
        "- Prioritize fixes by count and scientific risk.",
        "",
        "## Slide 7: Context Recall vs Faithfulness",
        "- Use `plots/context_recall_vs_faithfulness.png`.",
        "- Diagnose whether poor answers come from retrieval/context or answer synthesis.",
        "",
        "## Slide 8: Recommendations",
        "- Unify graph search and context-pack search.",
        "- Add negative filtering and project-aware routing.",
        "- Add citation-support grading and abstention tests to CI.",
        "- Expand gold hard tasks with human-reviewed expected evidence.",
    ]
    (report_dir / "presentation_outline.md").write_text("\n".join(slide_lines) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# Hard RAG Quality Benchmark\n\n"
        "Start with `reports/hard_quality_report.md` and `reports/presentation_outline.md`.\n"
        "Raw records are in `raw/`; presentation plots are in `plots/`.\n",
        encoding="utf-8",
    )


def flat_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        flat = {
            "id": row["id"],
            "run_id": row.get("run_id", row["id"]),
            "run_index": row.get("run_index", 0),
            "family": row["family"],
            "task_type": row["task_type"],
            "expected_behavior": row["expected_behavior"],
            "overall_score": row["scores"]["overall_score"],
            "retrieval_score": row["scores"]["retrieval_score"],
            "context_score": row["scores"]["context_score"],
            "answer_deterministic_score": row["scores"]["answer_deterministic_score"],
            "judge_score": row["scores"]["judge_score"],
            "retrieval_recall_at_10": row["retrieval"]["recall_at_k"],
            "retrieval_precision_at_10": row["retrieval"]["precision_at_k"],
            "retrieval_mrr": row["retrieval"]["mrr"],
            "retrieval_ndcg_at_10": row["retrieval"]["ndcg_at_k"],
            "context_recall": row["context"]["context_recall"],
            "context_precision": row["context"]["context_precision"],
            "answer_concept_coverage": row["answer_metrics"]["required_concept_coverage"],
            "citation_precision_proxy": row["answer_metrics"]["citation_precision_proxy"],
            "atomic_support_proxy": row["answer_metrics"]["atomic_support_proxy"],
            "behavior_ok": row["answer_metrics"]["behavior_ok"],
            "answer_latency_s": row["answer_latency_ms"] / 1000,
            "judge_latency_s": row["judge_latency_ms"] / 1000,
            "answer_path": row["answer_path"],
        }
        for key, value in row["judge"].items():
            if isinstance(value, (int, float, str)):
                flat[f"judge_{key}"] = value
        out.append(flat)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hard answer-level RAG quality benchmark.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--char-budget", type=int, default=18000)
    parser.add_argument("--timeout-s", type=int, default=360)
    parser.add_argument("--max-tasks", type=int, default=len(TASKS))
    parser.add_argument("--repeats", type=int, default=1, help="Number of answer/judge repeats per selected task.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = args.output_dir or (PACKAGE_ROOT / "outputs" / f"rag_hard_quality_{stamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)
    (output_dir / "plots").mkdir(exist_ok=True)
    (output_dir / "reports").mkdir(exist_ok=True)

    schema_path = output_dir / "raw" / "judge_schema.json"
    write_json(schema_path, JUDGE_SCHEMA)
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "package_root": str(PACKAGE_ROOT),
        "python": sys.version,
        "platform": platform.platform(),
        "top_k": args.top_k,
        "char_budget": args.char_budget,
        "max_tasks": args.max_tasks,
        "repeats": args.repeats,
        "literature_notes": LITERATURE_NOTES,
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=PACKAGE_ROOT, capture_output=True, text=True).stdout.strip(),
        "git_status_short": subprocess.run(["git", "status", "--short"], cwd=PACKAGE_ROOT, capture_output=True, text=True).stdout,
    }
    write_json(output_dir / "raw" / "manifest.json", manifest)

    rows: list[dict[str, Any]] = []
    selected_tasks = list(TASKS[: args.max_tasks])
    total_runs = len(selected_tasks) * args.repeats
    run_number = 0
    for task_index, task in enumerate(selected_tasks, start=1):
        for repeat_index in range(args.repeats):
            run_number += 1
            print(
                f"[{run_number}/{total_runs}] {task.id} repeat {repeat_index + 1}/{args.repeats}",
                flush=True,
            )
            rows.append(
                run_task_repeat(
                    task,
                    output_dir,
                    args.top_k,
                    args.char_budget,
                    args.timeout_s,
                    schema_path,
                    run_index=repeat_index,
                    repeats=args.repeats,
                )
            )
        write_jsonl(output_dir / "raw" / "partial_records.jsonl", rows)

    summary = summarize(rows)
    write_jsonl(output_dir / "raw" / "hard_quality_records.jsonl", rows)
    write_csv(output_dir / "raw" / "hard_quality_scores.csv", flat_rows(rows))
    write_json(output_dir / "raw" / "summary.json", summary)
    make_plots(output_dir, rows, summary)
    write_reports(output_dir, rows, summary)

    print(f"output: {output_dir}")
    print(f"runs: {summary['runs']} across {summary['unique_tasks']} tasks")
    print(f"overall mean: {summary['overall_mean']:.3f} +/- {summary['overall']['ci95']:.3f} 95% CI")
    print(f"report: {output_dir / 'reports' / 'hard_quality_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
