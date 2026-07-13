#!/usr/bin/env python3
"""Render compact SVG visuals for the runtime summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = PACKAGE_ROOT / "evals" / "results" / "summary.json"
DEFAULT_OUTPUT_DIR = PACKAGE_ROOT / "evals" / "views"


COLORS = {
    "ink": "#111827",
    "muted": "#4b5563",
    "grid": "#e5e7eb",
    "good": "#2563eb",
    "warn": "#d97706",
    "bad": "#dc2626",
    "paper": "#ffffff",
}


def _svg_escape(value: Any) -> str:
    text = str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _text(x: float, y: float, value: Any, *, size: int = 13, weight: str = "400", color: str = "ink") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{COLORS[color]}">{_svg_escape(value)}</text>'
    )


def _bar(x: float, y: float, width: float, height: float, color: str, radius: int = 3) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(width, 0):.1f}" height="{height:.1f}" '
        f'rx="{radius}" fill="{COLORS[color]}"/>'
    )


def render_suite_pass(summary: dict[str, Any]) -> str:
    suites = sorted(summary["suites"].items())
    width = 900
    row_h = 42
    top = 84
    height = top + len(suites) * row_h + 42
    chart_x = 220
    chart_w = 540
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{COLORS["paper"]}"/>',
        _text(28, 34, "Eval Suite Pass Rates", size=20, weight="700"),
        _text(28, 58, f'{summary["passed"]}/{summary["tasks"]} tasks passed, pass rate {summary["pass_rate"]:.3f}', size=13, color="muted"),
        _text(chart_x, 78, "0", size=11, color="muted"),
        _text(chart_x + chart_w - 24, 78, "100%", size=11, color="muted"),
        f'<line x1="{chart_x}" y1="84" x2="{chart_x + chart_w}" y2="84" stroke="{COLORS["grid"]}" stroke-width="1"/>',
    ]
    for index, (suite, stats) in enumerate(suites):
        y = top + index * row_h
        rate = stats["passed"] / stats["tasks"] if stats["tasks"] else 0.0
        lines.append(_text(28, y + 20, suite, size=13, weight="700"))
        lines.append(_bar(chart_x, y + 5, chart_w, 18, "grid"))
        lines.append(_bar(chart_x, y + 5, chart_w * rate, 18, "good"))
        lines.append(_text(chart_x + chart_w + 18, y + 20, f'{stats["passed"]}/{stats["tasks"]}', size=13))
    lines.append("</svg>")
    return "\n".join(lines)


def render_quality_metrics(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    rows = [
        ("retrieval recall@5", metrics["retrieval_recall_at_5_mean"], 1.0),
        ("retrieval MRR", metrics["mrr_mean"], 1.0),
        ("precision@5", metrics["precision_at_5_mean"], 1.0),
        ("provenance coverage", metrics["provenance_coverage_mean"], 1.0),
        ("context relevance", metrics["context_relevance_mean"], 1.0),
        ("context hash stability", metrics["context_hash_stability_mean"], 1.0),
        ("replay hash match", metrics["replay_context_hash_match_mean"], 1.0),
        ("synthesis score", metrics["synthesis_mean_score_mean"], 5.0),
    ]
    width = 900
    row_h = 38
    top = 82
    height = top + len(rows) * row_h + 44
    chart_x = 250
    chart_w = 470
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{COLORS["paper"]}"/>',
        _text(28, 34, "Runtime Quality Metrics", size=20, weight="700"),
        _text(28, 58, "Bars are normalized to each metric scale; synthesis uses a 0-5 rubric.", size=13, color="muted"),
    ]
    for index, (label, value, scale) in enumerate(rows):
        y = top + index * row_h
        frac = min(max(value / scale, 0.0), 1.0)
        color = "good" if frac >= 0.8 else "warn" if frac >= 0.5 else "bad"
        suffix = f"{value:.3f}" if scale == 1.0 else f"{value:.2f}/5"
        lines.append(_text(28, y + 18, label, size=13, weight="700"))
        lines.append(_bar(chart_x, y + 4, chart_w, 17, "grid"))
        lines.append(_bar(chart_x, y + 4, chart_w * frac, 17, color))
        lines.append(_text(chart_x + chart_w + 18, y + 18, suffix, size=13))
    lines.append("</svg>")
    return "\n".join(lines)


def render_latency(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    rows = [
        ("overall p50", summary["latency_ms"]["p50"]),
        ("overall p95", summary["latency_ms"]["p95"]),
        ("overall mean", metrics["latency_ms_mean"]),
        ("graph search mean", metrics["graph_search_latency_ms_mean"]),
        ("context compile mean", metrics["context_compile_latency_ms_mean"]),
    ]
    max_value = max(value for _label, value in rows if value is not None)
    width = 900
    row_h = 42
    top = 82
    height = top + len(rows) * row_h + 44
    chart_x = 250
    chart_w = 470
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{COLORS["paper"]}"/>',
        _text(28, 34, "Latency Snapshot", size=20, weight="700"),
        _text(28, 58, "Milliseconds from deterministic eval runs; small timing drift is expected.", size=13, color="muted"),
    ]
    for index, (label, value) in enumerate(rows):
        y = top + index * row_h
        frac = value / max_value if max_value else 0.0
        lines.append(_text(28, y + 20, label, size=13, weight="700"))
        lines.append(_bar(chart_x, y + 5, chart_w, 18, "grid"))
        lines.append(_bar(chart_x, y + 5, chart_w * frac, 18, "good"))
        lines.append(_text(chart_x + chart_w + 18, y + 20, f"{value:.1f} ms", size=13))
    lines.append("</svg>")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render runtime summary SVG assets.")
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "runtime_suite_pass.svg": render_suite_pass(summary),
        "runtime_quality_metrics.svg": render_quality_metrics(summary),
        "runtime_latency.svg": render_latency(summary),
    }
    for name, content in outputs.items():
        (args.output_dir / name).write_text(content + "\n", encoding="utf-8")
        print(args.output_dir / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
