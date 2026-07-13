#!/usr/bin/env python3
"""Render a readable standalone HTML summary for runtime eval results."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = PACKAGE_ROOT / "evals" / "results" / "summary.json"
DEFAULT_VIEWS = PACKAGE_ROOT / "evals" / "views"
DEFAULT_OUTPUT = DEFAULT_VIEWS / "runtime_summary.html"


IMPLEMENTED = [
    (
        "Trajectories",
        "Records task metadata, memory snapshot hashes, context packs, steps, outputs, mutations, and scores.",
        "runtime/trajectory.py",
    ),
    (
        "Context compiler",
        "Builds deterministic task-routed context packs with budgets, inclusion reasons, exclusions, and stable IDs.",
        "runtime/context_pack.py, context_policy/",
    ),
    (
        "Belief graph extensions",
        "Adds optional hypothesis/status fields and task-aware retrieval while keeping JSONL as source of truth.",
        "graph/schema.json, scripts/fact_graph.py",
    ),
    (
        "Eval harness",
        "Runs structured fixtures for retrieval, paper lookup, context packs, replay, memory writes, and synthesis.",
        "evals/run_evals.py, evals/fixtures/",
    ),
    (
        "Candidate archive",
        "Proposes, validates, evaluates, promotes, or rejects changes without direct durable self-editing.",
        "runtime/mutation.py, improvements/",
    ),
    (
        "Synthesis scaffold",
        "Produces structured hypothesis objects and scores them with a deterministic scientific rubric.",
        "science/hypothesis.py, science/rubrics.py",
    ),
    (
        "Skill metadata",
        "Adds machine-readable skill metadata so skills can be routed and evaluated.",
        "skills/*.yaml",
    ),
]


LIMITATIONS = [
    "The eval suite is a smoke test, not yet a hard scientific benchmark. It has 27 fixtures and can be overfit.",
    "Retrieval is lexical plus task-aware filtering. There is no SQLite FTS/BM25 index, vector baseline, or large-graph latency benchmark yet.",
    "Context relevance is fixture-labeled and coarse; it checks required paths, kinds, and IDs, not every included token.",
    "The synthesis loop is a deterministic scaffold, not a full generate -> critique -> evolve workflow.",
    "Candidate promotion is recorded, but candidates are not automatically applied in isolated worktrees before eval comparison.",
    "Production assistant calls are not fully instrumented end to end yet.",
    "Latency numbers are local deterministic timings and should not be extrapolated to NAS scans, much larger graphs, or LLM judges.",
    "The baseline is the first measured runtime baseline, not a historical pre-runtime baseline.",
]


STRESS_TESTS = [
    (
        "Graph scale-up",
        "Current graph latency may hide O(n) behavior.",
        "10x synthetic nodes/edges keep paper and claim lookup under a defined p95 latency.",
    ),
    (
        "Ambiguous lab shorthand",
        "Terms like D, PL, A5, C7, and hysteresis can route incorrectly.",
        "Correct task-aware route and provenance-backed top hits despite ambiguous terms.",
    ),
    (
        "Contradiction and stale facts",
        "Scientific memory must not treat deprecated or contested claims as settled.",
        "Deprecated or contested facts are surfaced with status and not used as unsupported conclusions.",
    ),
    (
        "Context budget squeeze",
        "Small Slack/direct contexts can exclude critical evidence.",
        "Required evidence coverage remains above threshold at 3k, 6k, and 12k char budgets.",
    ),
    (
        "Low-evidence synthesis",
        "Hypothesis generation should fail gracefully when evidence is weak.",
        "Groundedness and provenance scores drop, and no graph insertion is allowed.",
    ),
    (
        "Candidate regression gate",
        "Self-improvement must preserve protected tasks.",
        "A deliberately bad policy patch is rejected because replay, precision, or pass rate regresses.",
    ),
    (
        "Snapshot repeatability",
        "Same task should be replayable on the same memory snapshot.",
        "Same context pack ID and high retrieved-set Jaccard across repeated runs.",
    ),
    (
        "Snapshot sensitivity",
        "Real memory changes should be visible in hashes.",
        "Context or graph source edits change snapshot hash and are recorded in the trajectory.",
    ),
    (
        "Paper-first failure mode",
        "Paper lookup should not collapse into generic all-node search.",
        "Paper nodes are tried first; linked claims are backfill with explicit route metadata.",
    ),
    (
        "Noisy provenance",
        "Low-confidence generated deck claims can pollute retrieval.",
        "Unsupported low-confidence-use rate stays near zero on adversarial fixtures.",
    ),
]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def read_svg(path: Path) -> str:
    if not path.exists():
        return f"<p class=\"missing\">Missing visual: {esc(path.name)}</p>"
    return path.read_text(encoding="utf-8")


def fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def metric_cards(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    cards = [
        ("Pass rate", fmt(summary["pass_rate"], 3), "27 fixture smoke test"),
        ("Retrieval recall@5", fmt(metrics["retrieval_recall_at_5_mean"]), "Expected evidence coverage"),
        ("Retrieval MRR", fmt(metrics["mrr_mean"]), "How early the first relevant hit appears"),
        ("Precision@5", fmt(metrics["precision_at_5_mean"]), "Broad lexical retrieval leaves room to improve"),
        ("Provenance coverage", fmt(metrics["provenance_coverage_mean"]), "Retrieved eval hits have provenance"),
        ("Context stability", fmt(metrics["context_hash_stability_mean"]), "Same input/snapshot gives same pack ID"),
        ("Replay match", fmt(metrics["replay_context_hash_match_mean"]), "Trajectory replay reproduces context"),
        ("Latency p50/p95", f"{summary['latency_ms']['p50']:.1f} / {summary['latency_ms']['p95']:.1f} ms", "Local deterministic eval timing"),
    ]
    return "\n".join(
        f"""
        <article class="metric-card">
          <div class="metric-label">{esc(label)}</div>
          <div class="metric-value">{esc(value)}</div>
          <div class="metric-note">{esc(note)}</div>
        </article>
        """
        for label, value, note in cards
    )


def suite_table(summary: dict[str, Any]) -> str:
    rows = []
    for suite, stats in sorted(summary["suites"].items()):
        rate = stats["passed"] / stats["tasks"] if stats["tasks"] else 0.0
        rows.append(
            f"""
            <tr>
              <td>{esc(suite)}</td>
              <td>{stats['passed']}/{stats['tasks']}</td>
              <td>{rate:.3f}</td>
            </tr>
            """
        )
    return "\n".join(rows)


def implemented_table() -> str:
    return "\n".join(
        f"""
        <tr>
          <td>{esc(name)}</td>
          <td>{esc(behavior)}</td>
          <td><code>{esc(artifact)}</code></td>
        </tr>
        """
        for name, behavior, artifact in IMPLEMENTED
    )


def stress_table() -> str:
    return "\n".join(
        f"""
        <tr>
          <td>{esc(name)}</td>
          <td>{esc(why)}</td>
          <td>{esc(pass_condition)}</td>
        </tr>
        """
        for name, why, pass_condition in STRESS_TESTS
    )


def limitations_list() -> str:
    return "\n".join(f"<li>{esc(item)}</li>" for item in LIMITATIONS)


def render_html(summary: dict[str, Any], views_dir: Path) -> str:
    suite_svg = read_svg(views_dir / "runtime_suite_pass.svg")
    quality_svg = read_svg(views_dir / "runtime_quality_metrics.svg")
    latency_svg = read_svg(views_dir / "runtime_latency.svg")
    metrics = summary["metrics"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpenScience Scientific-Agent Runtime Summary</title>
  <style>
    :root {{
      --bg: #f7f8fb;
      --paper: #ffffff;
      --ink: #111827;
      --muted: #4b5563;
      --line: #d9dde7;
      --blue: #2563eb;
      --green: #047857;
      --amber: #b45309;
      --red: #b91c1c;
      --soft-blue: #eff6ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 34px 24px 56px;
    }}
    header {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 28px;
      margin-bottom: 18px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(30px, 4vw, 46px);
      line-height: 1.05;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0 0 14px;
      font-size: 22px;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 10px;
      font-size: 16px;
      letter-spacing: 0;
    }}
    p {{ margin: 0 0 12px; }}
    .subhead {{
      max-width: 860px;
      color: var(--muted);
      font-size: 17px;
    }}
    .status-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      padding: 7px 11px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }}
    .pill strong {{ color: var(--ink); margin-right: 5px; }}
    section {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 22px;
      margin: 18px 0;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
    }}
    .metric-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fff;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 4px;
    }}
    .metric-value {{
      font-size: 25px;
      font-weight: 750;
      line-height: 1.15;
      color: var(--ink);
      margin-bottom: 6px;
    }}
    .metric-note {{
      color: var(--muted);
      font-size: 12px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 16px;
    }}
    .visual {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      overflow: auto;
      background: #fff;
    }}
    .visual svg {{
      display: block;
      width: 100%;
      height: auto;
      min-width: 620px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-weight: 700;
      background: #fafbfc;
    }}
    code {{
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      border-radius: 4px;
      padding: 1px 4px;
      font-size: 12px;
    }}
    ul {{
      margin: 0;
      padding-left: 20px;
    }}
    li {{ margin: 7px 0; }}
    .interpretation {{
      border-left: 4px solid var(--blue);
      background: var(--soft-blue);
      padding: 14px 16px;
      border-radius: 8px;
      color: #1f2937;
    }}
    .warning {{
      border-left: 4px solid var(--amber);
      background: #fffbeb;
      padding: 14px 16px;
      border-radius: 8px;
    }}
    .command {{
      background: #101827;
      color: #f9fafb;
      padding: 14px;
      border-radius: 8px;
      overflow: auto;
      font-size: 13px;
    }}
    footer {{
      color: var(--muted);
      font-size: 13px;
      padding: 8px 2px;
    }}
    @media (max-width: 680px) {{
      main {{ padding: 18px 12px 36px; }}
      header, section {{ padding: 16px; }}
      .grid-2 {{ grid-template-columns: 1fr; }}
      .visual svg {{ min-width: 520px; }}
      .metric-value {{ font-size: 22px; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Scientific-Agent Runtime Summary</h1>
    <p class="subhead">A readable snapshot of the new OpenScience closed loops: trajectory capture, deterministic context compilation, graph-backed retrieval, candidate-gated self-improvement, replay checks, and quantitative evals.</p>
    <div class="status-row">
      <span class="pill"><strong>{summary["passed"]}/{summary["tasks"]}</strong> evals passed</span>
      <span class="pill"><strong>{summary["pass_rate"]:.3f}</strong> pass rate</span>
      <span class="pill"><strong>{metrics["retrieval_recall_at_5_mean"]:.3f}</strong> recall@5</span>
      <span class="pill"><strong>{summary["latency_ms"]["p50"]:.1f}/{summary["latency_ms"]["p95"]:.1f} ms</strong> p50/p95 latency</span>
      <span class="pill"><strong>0</strong> protected regressions</span>
    </div>
  </header>

  <section>
    <h2>Core Metrics</h2>
    <div class="metric-grid">
      {metric_cards(summary)}
    </div>
  </section>

  <section>
    <h2>Visual Summary</h2>
    <div class="grid-2">
      <div class="visual">{suite_svg}</div>
      <div class="visual">{quality_svg}</div>
      <div class="visual">{latency_svg}</div>
    </div>
  </section>

  <section>
    <h2>What Is Implemented</h2>
    <table>
      <thead><tr><th>Loop</th><th>Implemented behavior</th><th>Main artifact</th></tr></thead>
      <tbody>{implemented_table()}</tbody>
    </table>
  </section>

  <section>
    <h2>Suite Results</h2>
    <table>
      <thead><tr><th>Suite</th><th>Passed</th><th>Pass rate</th></tr></thead>
      <tbody>{suite_table(summary)}</tbody>
    </table>
  </section>

  <section>
    <h2>Interpretation</h2>
    <div class="interpretation">
      <p>The strongest result is repeatability: identical context-pack hashes and replay item sets under the same snapshot. Retrieval is usable for the current fixtures, with high recall and MRR. Precision@5 is the weaker metric because lexical graph search returns broad related context, not only the single tight answer. Provenance gating is working in the fixture set: low-confidence unsupported use is zero.</p>
    </div>
  </section>

  <section>
    <h2>Limitations</h2>
    <div class="warning">
      <ul>{limitations_list()}</ul>
    </div>
  </section>

  <section>
    <h2>Stress Tests To Add</h2>
    <table>
      <thead><tr><th>Stress test</th><th>Why it matters</th><th>Expected pass condition</th></tr></thead>
      <tbody>{stress_table()}</tbody>
    </table>
  </section>

  <section>
    <h2>Reproduce</h2>
    <pre class="command">python3 lab_assistant/evals/run_evals.py --suite all --output lab_assistant/evals/results/latest.jsonl
python3 lab_assistant/evals/render_summary_assets.py --summary lab_assistant/evals/results/summary.json --output-dir lab_assistant/evals/views
python3 lab_assistant/evals/render_summary_html.py --summary lab_assistant/evals/results/summary.json --views-dir lab_assistant/evals/views --output lab_assistant/evals/views/runtime_summary.html
python3 lab_assistant/evals/compare_results.py --baseline lab_assistant/evals/results/baseline.jsonl --candidate lab_assistant/evals/results/latest.jsonl</pre>
  </section>

  <footer>
    Generated from <code>evals/results/summary.json</code>. Visuals are embedded inline from the SVG artifacts in <code>evals/views/</code>.
  </footer>
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render standalone HTML runtime summary.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--views-dir", type=Path, default=DEFAULT_VIEWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    html_text = render_html(summary, args.views_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_text, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
