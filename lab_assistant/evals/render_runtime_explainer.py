#!/usr/bin/env python3
"""Render a transparent HTML explainer for the scientific-agent runtime."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = PACKAGE_ROOT / "evals" / "results" / "latest.jsonl"
DEFAULT_SUMMARY = PACKAGE_ROOT / "evals" / "results" / "summary.json"
DEFAULT_FIXTURES = PACKAGE_ROOT / "evals" / "fixtures"
DEFAULT_VIEWS = PACKAGE_ROOT / "evals" / "views"
DEFAULT_OUTPUT = DEFAULT_VIEWS / "runtime_explainer.html"


SUITE_DESCRIPTIONS = {
    "retrieval": "Claim lookup over the fact graph: can the route retrieve expected claim-like records with provenance?",
    "paper_lookup": "Paper-first retrieval: can paper queries return Paper nodes before falling back to linked claims?",
    "context_pack": "Task-routed context compilation: does each task include required skills, graph items, and project/knowledge files inside budget?",
    "replay": "Repeatability: does a recorded task rebuild the same context pack and item set on the same memory snapshot?",
    "memory_write": "Candidate-gated durable memory: are proposed mutations linked to candidates, decisions, and provenance warnings?",
    "synthesis": "Structured hypothesis scaffold: does hypothesis generation produce required fields and pass a deterministic rubric?",
}


METRIC_DEFINITIONS = [
    ("recall@5", "Fraction of expected fixture labels/IDs found in the top 5 retrieved items. High means the expected evidence is present."),
    ("precision@5", "Fraction of top 5 retrieved items that match expected labels/IDs. Low values mean retrieval is broad or noisy."),
    ("MRR", "Mean reciprocal rank of the first relevant result. 1.0 means the first hit matched the expectation."),
    ("provenance coverage", "Fraction of retrieved eval hits carrying provenance metadata."),
    ("low-confidence unsupported use", "Fraction of low-confidence hits without provenance. Lower is better."),
    ("context relevance", "Coverage of required fixture paths, item IDs, and item kinds in a context pack."),
    ("context hash stability", "Whether the same task and snapshot produce the same context_pack_id."),
    ("retrieved-item Jaccard", "Overlap between original and replayed context item IDs."),
    ("invalid mutation rate", "Whether a memory mutation failed the candidate/provenance gate. For the missing-candidate fixture, failure is expected."),
    ("synthesis score", "Mean deterministic rubric score across groundedness, falsifiability, mechanism clarity, contradiction awareness, novelty, actionability, and provenance."),
]


MACHINERY = [
    (
        "Trajectory store",
        "Records what task was attempted, which memory/context snapshot was used, which context pack was compiled, what steps ran, and what scores were attached.",
        "This is the substrate for replay, debugging, and future optimization.",
    ),
    (
        "Dynamic context compiler",
        "Chooses compact context by task type instead of loading all canonical files. It records why each item was included or excluded.",
        "This makes context selection measurable and repeatable.",
    ),
    (
        "Belief/fact graph",
        "Keeps JSONL as source of truth while adding optional scientific status fields and task-aware search routes.",
        "This separates papers, claims, hypotheses, evidence, contradictions, and observables.",
    ),
    (
        "Candidate archive",
        "Creates proposed changes with lineage, target metrics, protected metrics, attached evals, and promote/reject decisions.",
        "This follows the archive-plus-evaluation pattern instead of direct self-editing.",
    ),
    (
        "Eval harness",
        "Runs structured fixtures and writes JSONL results, summary JSON, comparison output, and reports.",
        "This turns runtime changes into measurable deltas rather than anecdotes.",
    ),
    (
        "Structured synthesis scaffold",
        "Generates hypothesis objects with claims, contradictions, prediction, minimal test, falsifier, risks, confidence, and provenance.",
        "This is the first step toward generate -> critique -> evolve loops, but not the full loop yet.",
    ),
]


RECOMMENDATION_MAP = [
    (
        "Darwin Godel Machine / AlphaEvolve style archive + empirical eval",
        "Partially implemented",
        "Candidate records, attached eval results, promote/reject decisions, protected-regression comparison.",
        "No isolated worktree patch runner or automatic promotion gate yet.",
    ),
    (
        "Co-Scientist / AI Scientist generate -> critique -> evolve",
        "Scaffold only",
        "Structured hypothesis object and rubric exist.",
        "No real multi-round generation, critique, ranking, or evolution loop yet.",
    ),
    (
        "Mem0 / Zep / Graphiti selective temporal memory",
        "Partially implemented",
        "Task-routed context packs, provenance, graph status fields, memory snapshot hashes.",
        "No temporal consolidation daemon or stale-fact monitoring dashboard yet.",
    ),
    (
        "DSPy / GEPA measurable skills",
        "Partially implemented",
        "Skill YAML metadata with task types, inputs/outputs, latency budgets, eval suites.",
        "No prompt optimizer or skill variant search loop yet.",
    ),
    (
        "tau-bench trajectory evaluation",
        "Initial implementation",
        "Trajectory schema records context choices, steps, outputs, mutations, scores; replay evals exist.",
        "Production assistant calls are not yet fully instrumented step by step.",
    ),
]


LIMITATIONS = [
    "The current fixtures are smoke tests, not a trusted scientific benchmark. Several thresholds are intentionally permissive.",
    "The benchmark can be overfit because fixtures are local, visible, and small.",
    "Retrieval is lexical plus task-aware filtering; there is no BM25/FTS index, vector baseline, or large-graph benchmark yet.",
    "Context relevance checks required paths, item IDs, and item kinds, but not every included token's scientific utility.",
    "Synthesis scoring validates structure and provenance behavior, not scientific novelty or correctness.",
    "Candidate records exist, but candidate patches are not applied and tested in isolated worktrees.",
    "The trajectory runtime is used by evals and CLIs, but not yet automatically around every production assistant action.",
    "Latency measurements are local deterministic timings, not NAS-scale or LLM-in-the-loop timings.",
]


MONITORING_PLAN = [
    (
        "Knowledge coverage",
        "Track graph nodes/edges by type, confidence, status, project, source type, and last_validated_at.",
        "Shows whether the assistant is actually learning the lab corpus rather than only accumulating files.",
    ),
    (
        "Retrieval quality over time",
        "Maintain a growing benchmark from real lab questions; report recall@k, MRR, precision@k, provenance coverage, and contradiction awareness.",
        "Shows whether retrieval improves as memory grows or becomes noisier.",
    ),
    (
        "Context efficiency",
        "Track context chars/tokens, required-evidence coverage, excluded-relevant count, and irrelevant item rate by task type.",
        "Shows whether dynamic context compilation is getting leaner without losing evidence.",
    ),
    (
        "Memory mutation quality",
        "Track proposed, promoted, rejected, duplicate, contradicted, stale, and unprovenanced mutations.",
        "Shows whether self-improvement is selective and evidence-backed.",
    ),
    (
        "User correction loop",
        "Record corrections, repeated misses, re-asks, and accepted answers as trajectory-linked feedback.",
        "Shows whether the system is reducing repeated failures and capturing preferences durably.",
    ),
    (
        "Scientific synthesis utility",
        "Track hypotheses generated, critiqued, refined, linked to evidence, tested, supported, weakened, or rejected.",
        "Shows whether hypothesis machinery leads to testable progress rather than prose generation.",
    ),
    (
        "Project freshness",
        "Track project summaries, daemon reports, owner clarifications, and graph claims by freshness/staleness.",
        "Shows when the assistant is operating on old project context.",
    ),
    (
        "Regression protection",
        "Run baseline-vs-candidate comparisons on protected suites before promoting retrieval policy, skills, graph schema, or memory rules.",
        "Shows whether learning improves target metrics without damaging core behavior.",
    ),
]


STRESS_TESTS = [
    (
        "Holdout lab questions",
        "Create a blind set from real Slack/OpenScience questions not used while tuning policies.",
        "Prevents fixture overfitting.",
    ),
    (
        "Ambiguous shorthand",
        "Queries like D, PL, A5, C7, B79, hysteresis, 2s, v=-2, and filling.",
        "Tests routing and project disambiguation under realistic lab language.",
    ),
    (
        "Contradicted-memory retrieval",
        "Queries where supported, contested, and deprecated claims all match lexically.",
        "Tests whether status and provenance affect final context and answer framing.",
    ),
    (
        "Context budget squeeze",
        "Run same tasks at 3k, 6k, 12k, and 24k character budgets.",
        "Tests whether essential evidence survives direct/Slack-sized contexts.",
    ),
    (
        "Large synthetic graph",
        "Scale JSONL graph by 10x and 100x with distractor nodes/edges.",
        "Tests latency and ranking robustness.",
    ),
    (
        "Noisy low-confidence deck claims",
        "Add plausible but weak automatically extracted deck claims.",
        "Tests low-confidence unsupported-use controls.",
    ),
    (
        "Bad candidate patch",
        "Deliberately change retrieval routing to generic all-node search.",
        "Tests whether protected metrics reject a harmful self-improvement candidate.",
    ),
    (
        "Stale project summary",
        "Inject old project status that conflicts with a newer daemon report.",
        "Tests temporal memory and stale-fact handling.",
    ),
    (
        "Human correction replay",
        "Use a lab-member correction as a trajectory, then verify future similar tasks avoid the same mistake.",
        "Tests whether feedback becomes durable behavior.",
    ),
]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_jsonish(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_map(fixtures_dir: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(fixtures_dir.glob("*.yaml")):
        data = load_jsonish(path)
        fixtures = data.get("fixtures", data) if isinstance(data, dict) else data
        for fixture in fixtures:
            fixture = dict(fixture)
            fixture["_suite"] = path.stem
            records[fixture["id"]] = fixture
    return records


def svg(path: Path) -> str:
    if not path.exists():
        return f'<p class="missing">Missing visual: {esc(path.name)}</p>'
    return path.read_text(encoding="utf-8")


def compact_expected(fixture: dict[str, Any]) -> str:
    expected = fixture.get("expected", {})
    parts: list[str] = []
    if expected.get("must_retrieve_any"):
        labels = []
        for item in expected["must_retrieve_any"]:
            if "label_contains" in item:
                labels.append(f'label contains "{item["label_contains"]}"')
            elif "id" in item:
                labels.append(f'id={item["id"]}')
        parts.append("retrieve any: " + "; ".join(labels))
    if expected.get("must_retrieve_types"):
        parts.append("types: " + ", ".join(expected["must_retrieve_types"]))
    if expected.get("required_paths"):
        parts.append("paths: " + ", ".join(expected["required_paths"]))
    if expected.get("required_item_ids"):
        parts.append("item IDs: " + ", ".join(expected["required_item_ids"]))
    if expected.get("required_kinds"):
        parts.append("kinds: " + ", ".join(expected["required_kinds"]))
    if "same_context_pack_id" in expected:
        parts.append(f"same context pack: {expected['same_context_pack_id']}")
    if "valid_mutation" in expected:
        parts.append(f"valid mutation: {expected['valid_mutation']}")
    if not parts and fixture.get("metrics"):
        parts.append("rubric/threshold fixture")
    return " | ".join(parts) or "no explicit expected contract"


def compact_thresholds(fixture: dict[str, Any]) -> str:
    metrics = fixture.get("metrics", {})
    if not metrics:
        return "none"
    items = []
    for key, value in metrics.items():
        items.append(f"{key}={value}")
    if fixture.get("char_budget"):
        items.insert(0, f"char_budget={fixture['char_budget']}")
    return ", ".join(items)


def result_summary(record: dict[str, Any]) -> str:
    scores = record.get("scores", {})
    preferred = [
        "retrieval_recall_at_5",
        "precision_at_5",
        "mrr",
        "provenance_coverage",
        "low_confidence_unsupported_use",
        "context_relevance",
        "context_chars",
        "context_hash_stability",
        "retrieved_item_jaccard",
        "replay_context_hash_match",
        "invalid_mutation_rate",
        "provenance_completeness",
        "synthesis_mean_score",
        "latency_ms",
    ]
    parts = []
    for key in preferred:
        if key in scores:
            value = scores[key]
            if isinstance(value, float):
                parts.append(f"{key}={value:.3g}")
            else:
                parts.append(f"{key}={value}")
    return ", ".join(parts)


def retrieved_summary(record: dict[str, Any]) -> str:
    retrieved = record.get("retrieved", [])
    if not retrieved:
        return ""
    top = []
    for hit in retrieved[:3]:
        label = hit.get("label") or hit.get("id")
        top.append(f"{hit.get('type', '?')}: {label}")
    return "Top hits: " + " / ".join(top)


def suite_fixture_table(suite: str, records: list[dict[str, Any]], fixtures: dict[str, dict[str, Any]]) -> str:
    rows = []
    for record in records:
        fixture = fixtures.get(record["id"], {})
        rows.append(
            f"""
            <tr>
              <td><code>{esc(record["id"])}</code></td>
              <td>{esc(record.get("query", fixture.get("query", "")))}</td>
              <td>{esc(compact_expected(fixture))}</td>
              <td>{esc(compact_thresholds(fixture))}</td>
              <td><span class="pass">{esc(record.get("passed"))}</span><br>{esc(result_summary(record))}<br><span class="muted-small">{esc(retrieved_summary(record))}</span></td>
            </tr>
            """
        )
    return f"""
    <details class="fixture-details" open>
      <summary>{esc(suite)}: {len(records)} fixtures</summary>
      <p>{esc(SUITE_DESCRIPTIONS.get(suite, ""))}</p>
      <table class="fixture-table">
        <thead>
          <tr><th>Fixture</th><th>Task/query</th><th>Expected contract</th><th>Thresholds</th><th>Observed result</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </details>
    """


def metric_cards(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    cards = [
        ("Pass rate", f"{summary['pass_rate']:.3f}", "All smoke fixtures pass; not proof of scientific correctness."),
        ("Retrieval recall@5", f"{metrics['retrieval_recall_at_5_mean']:.3f}", "Expected evidence usually appears in top results."),
        ("MRR", f"{metrics['mrr_mean']:.3f}", "First expected hit is usually early."),
        ("Precision@5", f"{metrics['precision_at_5_mean']:.3f}", "Weakest retrieval metric; broad context remains noisy."),
        ("Provenance coverage", f"{metrics['provenance_coverage_mean']:.3f}", "Fixture hits carry provenance metadata."),
        ("Context stability", f"{metrics['context_hash_stability_mean']:.3f}", "Deterministic context pack IDs under same snapshot."),
        ("Replay Jaccard", f"{metrics['retrieved_item_jaccard_mean']:.3f}", "Replayed context item set matches original."),
        ("Latency p50/p95", f"{summary['latency_ms']['p50']:.1f}/{summary['latency_ms']['p95']:.1f} ms", "Local deterministic runs only."),
    ]
    return "".join(
        f"""
        <article class="card">
          <div class="card-label">{esc(label)}</div>
          <div class="card-value">{esc(value)}</div>
          <div class="card-note">{esc(note)}</div>
        </article>
        """
        for label, value, note in cards
    )


def simple_table(rows: list[tuple[str, ...]], headers: tuple[str, ...]) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def architecture_svg() -> str:
    boxes = [
        ("User / task", 30, 72),
        ("Memory snapshot", 198, 72),
        ("Context compiler", 366, 72),
        ("Graph + skills", 534, 72),
        ("Answer / action", 702, 72),
        ("Trajectory", 366, 190),
        ("Eval harness", 534, 190),
        ("Candidate archive", 702, 190),
        ("Promote / reject", 870, 190),
    ]
    rects = []
    for label, x, y in boxes:
        rects.append(f'<rect x="{x}" y="{y}" width="128" height="54" rx="7" fill="#ffffff" stroke="#cbd5e1"/>')
        rects.append(f'<text x="{x+64}" y="{y+32}" text-anchor="middle" font-family="Arial" font-size="13" fill="#111827">{esc(label)}</text>')
    arrows = [
        (158, 99, 198, 99),
        (326, 99, 366, 99),
        (494, 99, 534, 99),
        (662, 99, 702, 99),
        (766, 126, 430, 190),
        (494, 217, 534, 217),
        (662, 217, 702, 217),
        (830, 217, 870, 217),
        (934, 190, 598, 126),
    ]
    arrow_lines = []
    for x1, y1, x2, y2 in arrows:
        arrow_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>')
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="1030" height="280" viewBox="0 0 1030 280" role="img" aria-label="Runtime closed-loop architecture">
      <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#2563eb"/></marker></defs>
      <rect width="1030" height="280" fill="#ffffff"/>
      <text x="30" y="35" font-family="Arial" font-size="19" font-weight="700" fill="#111827">Closed-loop runtime machinery</text>
      {''.join(arrow_lines)}
      {''.join(rects)}
      <text x="366" y="262" font-family="Arial" font-size="12" fill="#4b5563">The loop is only trustworthy if trajectories, evals, candidate decisions, and memory snapshots stay linked.</text>
    </svg>
    """


def render_html(summary: dict[str, Any], records: list[dict[str, Any]], fixtures: dict[str, dict[str, Any]], views_dir: Path) -> str:
    by_suite: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_suite.setdefault(record["suite"], []).append(record)
    suite_sections = "\n".join(
        suite_fixture_table(suite, by_suite[suite], fixtures)
        for suite in sorted(by_suite)
    )
    recommendation_rows = [
        tuple(esc(cell) for cell in row)
        for row in RECOMMENDATION_MAP
    ]
    machinery_rows = [
        (esc(name), esc(what), esc(why))
        for name, what, why in MACHINERY
    ]
    metric_rows = [
        (f"<strong>{esc(name)}</strong>", esc(definition))
        for name, definition in METRIC_DEFINITIONS
    ]
    monitor_rows = [
        (f"<strong>{esc(name)}</strong>", esc(signal), esc(reason))
        for name, signal, reason in MONITORING_PLAN
    ]
    stress_rows = [
        (f"<strong>{esc(name)}</strong>", esc(test), esc(reason))
        for name, test, reason in STRESS_TESTS
    ]
    limitations = "".join(f"<li>{esc(item)}</li>" for item in LIMITATIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenScience Runtime Explainer</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --paper: #ffffff;
      --ink: #111827;
      --muted: #4b5563;
      --line: #d7dce6;
      --blue: #2563eb;
      --soft-blue: #eff6ff;
      --soft-yellow: #fffbeb;
      --yellow: #b45309;
      --green: #047857;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    main {{ max-width: 1220px; margin: 0 auto; padding: 34px 24px 60px; }}
    header, section {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 24px;
      margin: 18px 0;
    }}
    h1 {{ margin: 0 0 10px; font-size: clamp(32px, 4vw, 48px); line-height: 1.05; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 24px; letter-spacing: 0; }}
    h3 {{ margin: 18px 0 8px; font-size: 17px; letter-spacing: 0; }}
    p {{ margin: 0 0 12px; }}
    .lead {{ max-width: 960px; color: var(--muted); font-size: 17px; }}
    .callout {{
      border-left: 4px solid var(--blue);
      background: var(--soft-blue);
      padding: 14px 16px;
      border-radius: 8px;
      margin: 14px 0;
    }}
    .warning {{
      border-left: 4px solid var(--yellow);
      background: var(--soft-yellow);
      padding: 14px 16px;
      border-radius: 8px;
      margin: 14px 0;
    }}
    .status-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 11px;
      color: var(--muted);
      background: #fff;
      font-size: 13px;
      white-space: nowrap;
    }}
    .pill strong {{ color: var(--ink); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fff;
    }}
    .card-label {{ color: var(--muted); font-size: 13px; }}
    .card-value {{ font-size: 25px; font-weight: 750; margin: 3px 0 5px; }}
    .card-note {{ color: var(--muted); font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #fafbfc; color: var(--muted); font-weight: 700; }}
    code {{
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 4px;
      padding: 1px 4px;
      font-size: 12px;
    }}
    .visual {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      overflow: auto;
      background: #fff;
      margin-top: 12px;
    }}
    .visual svg {{ display: block; width: 100%; height: auto; min-width: 680px; }}
    .two-col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 16px;
    }}
    details.fixture-details {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin: 14px 0;
      background: #fff;
    }}
    details.fixture-details summary {{
      cursor: pointer;
      font-weight: 750;
      font-size: 16px;
    }}
    .fixture-table th:nth-child(1) {{ width: 16%; }}
    .fixture-table th:nth-child(2) {{ width: 18%; }}
    .fixture-table th:nth-child(3) {{ width: 27%; }}
    .fixture-table th:nth-child(4) {{ width: 17%; }}
    .fixture-table th:nth-child(5) {{ width: 22%; }}
    .pass {{ color: var(--green); font-weight: 700; }}
    .muted-small {{ color: var(--muted); font-size: 12px; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 7px 0; }}
    .commands {{
      background: #101827;
      color: #f9fafb;
      border-radius: 8px;
      padding: 14px;
      overflow: auto;
      font-size: 13px;
    }}
    @media (max-width: 760px) {{
      main {{ padding: 18px 12px 42px; }}
      header, section {{ padding: 16px; }}
      .two-col {{ grid-template-columns: 1fr; }}
      .visual svg {{ min-width: 560px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>OpenScience Runtime Explainer</h1>
    <p class="lead">This is not just a dashboard. It explains what the system is trying to do, what machinery now exists, what the current tests actually check, what those tests say, and how to monitor whether the assistant is genuinely learning the lab’s science and context.</p>
    <div class="status-row">
      <span class="pill"><strong>{summary['passed']}/{summary['tasks']}</strong> smoke fixtures passed</span>
      <span class="pill"><strong>{summary['metrics']['retrieval_recall_at_5_mean']:.3f}</strong> recall@5</span>
      <span class="pill"><strong>{summary['metrics']['precision_at_5_mean']:.3f}</strong> precision@5</span>
      <span class="pill"><strong>{summary['metrics']['context_hash_stability_mean']:.3f}</strong> context stability</span>
      <span class="pill"><strong>{summary['latency_ms']['p50']:.1f}/{summary['latency_ms']['p95']:.1f} ms</strong> p50/p95 local latency</span>
    </div>
  </header>

  <section>
    <h2>What The System Is Here To Do</h2>
    <div class="callout">
      <p>The goal is a provenance-aware scientific assistant that can retrieve lab and literature context, compile only the context needed for a task, preserve what happened as replayable trajectory data, propose improvements as candidates, and promote only changes that improve measured behavior without protected regressions.</p>
      <p>The current implementation is the measurement and safety substrate. It does not yet make the assistant scientifically autonomous. It makes future learning inspectable: what was retrieved, why it was included, what changed, whether it helped, and what regressed.</p>
    </div>
  </section>

  <section>
    <h2>Machinery Now In Place</h2>
    <div class="visual">{architecture_svg()}</div>
    {simple_table(machinery_rows, ("Component", "What it does", "Why it matters"))}
  </section>

  <section>
    <h2>How This Maps To The Recommendations</h2>
    <p>The implementation listened to the recommendations in the sense that it created the hooks for archive, trajectory, routed memory, and measured skills. Several recommendations are only partial, and that should be visible rather than hidden.</p>
    {simple_table(recommendation_rows, ("Recommendation", "Current status", "Implemented", "Still missing"))}
  </section>

  <section>
    <h2>Current Metrics At A Glance</h2>
    <div class="grid">{metric_cards(summary)}</div>
    <div class="two-col">
      <div class="visual">{svg(views_dir / 'runtime_suite_pass.svg')}</div>
      <div class="visual">{svg(views_dir / 'runtime_quality_metrics.svg')}</div>
      <div class="visual">{svg(views_dir / 'runtime_latency.svg')}</div>
    </div>
  </section>

  <section>
    <h2>What The Metrics Mean</h2>
    {simple_table(metric_rows, ("Metric", "Definition and trust boundary"))}
    <div class="warning">
      <p>The pass rate is not a claim that the assistant is scientifically reliable. It means the new runtime loops are measurable and currently satisfy a small set of explicit fixtures. The weakest aggregate signal is precision@5 = {summary['metrics']['precision_at_5_mean']:.3f}, which means retrieval often brings broad related material along with the expected hit.</p>
    </div>
  </section>

  <section>
    <h2>Test Transparency</h2>
    <p>Each row below shows the fixture contract, threshold, and observed result. This is the part that should make the tests less of a black box.</p>
    {suite_sections}
  </section>

  <section>
    <h2>What The Tests Say</h2>
    <div class="callout">
      <p><strong>Supported by current tests:</strong> the runtime can build deterministic context packs, replay context choices, route paper lookup differently from claim lookup, enforce candidate/provenance checks for memory proposals, and emit machine-readable metrics.</p>
      <p><strong>Not supported yet:</strong> robust scientific correctness, generalization to unseen lab questions, large-scale retrieval quality, temporal staleness handling, or real candidate self-improvement in isolated worktrees.</p>
    </div>
  </section>

  <section>
    <h2>Current Limitations</h2>
    <ul>{limitations}</ul>
  </section>

  <section>
    <h2>How To Monitor Learning And Efficacy</h2>
    <p>An adaptable lab assistant needs longitudinal monitoring, not one-time pass/fail tests. These are the progress signals that should be tracked as it learns the lab corpus and context.</p>
    {simple_table([(f"<strong>{esc(name)}</strong>", esc(signal), esc(reason)) for name, signal, reason in MONITORING_PLAN], ("Monitor", "Signal to track", "What it tells us"))}
  </section>

  <section>
    <h2>Stress Tests To Add Next</h2>
    {simple_table([(f"<strong>{esc(name)}</strong>", esc(test), esc(reason)) for name, test, reason in STRESS_TESTS], ("Stress test", "Test design", "Why it matters"))}
  </section>

  <section>
    <h2>Reproduce</h2>
    <pre class="commands">python3 lab_assistant/evals/run_evals.py --suite all --output lab_assistant/evals/results/latest.jsonl
python3 lab_assistant/evals/render_summary_assets.py --summary lab_assistant/evals/results/summary.json --output-dir lab_assistant/evals/views
python3 lab_assistant/evals/render_runtime_explainer.py --results lab_assistant/evals/results/latest.jsonl --summary lab_assistant/evals/results/summary.json --output lab_assistant/evals/views/runtime_explainer.html</pre>
  </section>
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render transparent runtime explainer HTML.")
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--views-dir", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = load_jsonl(args.results)
    summary = load_jsonish(args.summary)
    fixtures = fixture_map(args.fixtures_dir)
    html_text = render_html(summary, records, fixtures, args.views_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_text, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
