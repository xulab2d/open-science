#!/usr/bin/env python3
"""Render UW-styled review figures for the hard RAG quality benchmark."""

from __future__ import annotations

import argparse
import json
import math
import urllib.request
from pathlib import Path

import matplotlib as mpl
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap


UW_PURPLE = "#4B2E83"
UW_GOLD = "#B7A57A"
UW_METALLIC_GOLD = "#85754D"
UW_LIGHT_GOLD = "#E8E3D3"
INK = "#231F20"
MUTED = "#6B6570"
GRID = "#D9D2C4"
PAPER = "#FBFAF7"
WHITE = "#FFFFFF"

OPEN_SANS_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/opensans/OpenSans%5Bwdth%2Cwght%5D.ttf"

TASK_LABELS = {
    "a5_dot_project_context": "A5 dot\nproject context",
    "b79_exact_curie_temperature_abstain": "B79 Curie temp\nabstention",
    "b79_project_context": "B79\nproject context",
    "d93_nu_minus2_hysteresis_caution": "D93 nu=-2\ncaution",
    "displacement_field_topology": "Displacement-field\ntopology",
    "fci_evidence_hierarchy": "FCI evidence\nhierarchy",
    "low_conf_superconductivity_arxiv": "Low-conf arXiv\ncaution",
    "minus_one_third_interpretation": "-1/3\ninterpretation",
    "moire_exciton_exclude_polariton": "Moire exciton\nhard negative",
    "optical_control_chern_states": "Optical control\nof Chern states",
}

FAMILY_LABELS = {
    "abstention": "abstention",
    "freshness": "freshness",
    "hard_negative": "hard negative",
    "multi_hop": "multi-hop",
    "project_context": "project context",
    "uncertainty": "uncertainty",
}

FAMILY_COLORS = {
    "abstention": "#85754D",
    "freshness": "#8F7AB8",
    "hard_negative": "#4B2E83",
    "multi_hop": "#B7A57A",
    "project_context": "#6B4E9B",
    "uncertainty": "#C9B889",
}

SCORE_LABELS = {
    "overall_score": "Overall",
    "retrieval_score": "Retrieval",
    "context_score": "Context",
    "answer_deterministic_score": "Answer",
    "judge_score": "Judge",
}

JUDGE_LABELS = {
    "judge_context_relevance": "Context\nrelevance",
    "judge_answer_relevance": "Answer\nrelevance",
    "judge_faithfulness": "Faithfulness",
    "judge_citation_quality": "Citation\nquality",
    "judge_scientific_correctness": "Scientific\ncorrectness",
    "judge_uncertainty_calibration": "Uncertainty\ncalibration",
    "judge_actionability": "Actionability",
}

FAILURE_LABELS = {
    "answer_concept_miss": "Answer concept miss",
    "context_miss": "Context miss",
    "hard_negative_leak": "Hard-negative leak",
    "judge_citation_under_4": "Citation score < 4",
    "judge_critical_errors": "Judge critical errors",
    "judge_faithfulness_under_4": "Faithfulness score < 4",
    "retrieval_miss": "Retrieval miss",
    "weak_citation_precision_proxy": "Weak citation precision",
}


def find_or_fetch_open_sans(font_dir: Path) -> str:
    """Return a usable font family, preferring Open Sans."""
    available = {font.name for font in font_manager.fontManager.ttflist}
    if "Open Sans" in available:
        return "Open Sans"

    font_dir.mkdir(parents=True, exist_ok=True)
    font_path = font_dir / "OpenSans.ttf"
    if not font_path.exists():
        try:
            urllib.request.urlretrieve(OPEN_SANS_URL, font_path)
        except Exception:
            return "DejaVu Sans"

    try:
        font_manager.fontManager.addfont(str(font_path))
        return font_manager.FontProperties(fname=str(font_path)).get_name()
    except Exception:
        return "DejaVu Sans"


def apply_uw_style(font_family: str) -> None:
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 320,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.08,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "font.family": font_family,
            "font.size": 12,
            "axes.titlesize": 17,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.linewidth": 1.0,
            "axes.grid": False,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def save(fig: plt.Figure, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in (".png", ".pdf", ".svg"):
        path = stem.with_suffix(suffix)
        fig.savefig(path)
        paths.append(path)
    plt.close(fig)
    return paths


def clean_axis(ax: plt.Axes, *, grid_axis: str | None = "x") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid_axis:
        ax.grid(axis=grid_axis, alpha=0.75)
    ax.set_axisbelow(True)


def score_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "uw_score",
        ["#F6F2E8", "#D9C792", UW_GOLD, "#735AA3", UW_PURPLE],
    )


def failure_cmap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(
        "uw_failure",
        ["#FAF8F1", UW_LIGHT_GOLD, UW_GOLD, UW_METALLIC_GOLD, UW_PURPLE],
    )


def short_task(task_id: str) -> str:
    return TASK_LABELS.get(task_id, task_id.replace("_", "\n"))


def add_title(fig: plt.Figure, title: str, subtitle: str | None = None) -> None:
    fig.text(0.055, 0.955, title, ha="left", va="top", fontsize=21, weight="bold", color=UW_PURPLE)
    if subtitle:
        fig.text(0.055, 0.912, subtitle, ha="left", va="top", fontsize=11.5, color=MUTED)


def load_data(input_dir: Path) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(input_dir / "raw" / "hard_quality_scores.csv")
    with (input_dir / "raw" / "summary.json").open() as f:
        summary = json.load(f)
    return df, summary


def task_table(df: pd.DataFrame, summary: dict) -> pd.DataFrame:
    rows = []
    for task_id, task_summary in summary["by_task"].items():
        row = {
            "id": task_id,
            "label": short_task(task_id),
            "family": task_summary["family"],
            "runs": task_summary["runs"],
        }
        for key in [
            "overall_score",
            "retrieval_score",
            "context_score",
            "answer_deterministic_score",
            "judge_score",
        ]:
            stats = task_summary["score_stats"][key]
            row[f"{key}_mean"] = stats["mean"]
            row[f"{key}_ci95"] = stats["ci95"]
        rows.append(row)
    table = pd.DataFrame(rows)
    return table.sort_values("overall_score_mean", ascending=True).reset_index(drop=True)


def render_overview(output_dir: Path, df: pd.DataFrame, summary: dict) -> list[Path]:
    fig = plt.figure(figsize=(13.333, 7.5), constrained_layout=False)
    fig.patch.set_facecolor(PAPER)
    add_title(
        fig,
        "Hard RAG benchmark: current system state",
        "100 runs across 10 hard scientific tasks; error bars show repeat variability where applicable.",
    )

    overall = summary["overall"]
    layer_keys = ["retrieval_score", "context_score", "answer_deterministic_score", "judge_score"]
    layer_vals = [summary["score_means"][key] for key in layer_keys]

    ax_text = fig.add_axes([0.055, 0.19, 0.33, 0.62])
    ax_text.axis("off")
    ax_text.text(0, 0.88, "Overall quality", fontsize=13, color=MUTED, weight="bold")
    ax_text.text(0, 0.67, f"{overall['mean']:.3f}", fontsize=62, color=UW_PURPLE, weight="bold")
    ax_text.text(0.02, 0.57, f"+/- {overall['ci95']:.3f} 95% CI", fontsize=14, color=UW_METALLIC_GOLD, weight="bold")
    ax_text.text(0, 0.39, "Primary bottleneck", fontsize=13, color=MUTED, weight="bold")
    ax_text.text(0, 0.26, "Context assembly", fontsize=27, color=INK, weight="bold")
    ax_text.text(
        0,
        0.14,
        "Context score is the lowest layer mean,\nwhile answer behavior remains comparatively strong.",
        fontsize=12.5,
        color=MUTED,
        linespacing=1.35,
    )

    ax = fig.add_axes([0.45, 0.22, 0.47, 0.53])
    y = np.arange(len(layer_keys))
    colors = [UW_PURPLE, UW_GOLD, "#6B4E9B", UW_METALLIC_GOLD]
    ax.barh(y, layer_vals, color=colors, height=0.58)
    ax.set_yticks(y, [SCORE_LABELS[key] for key in layer_keys])
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Mean score (0-1)")
    ax.set_title("Pipeline layer scores", loc="left", pad=14)
    for idx, value in enumerate(layer_vals):
        ax.text(value + 0.018, idx, f"{value:.3f}", va="center", ha="left", fontsize=12, weight="bold", color=INK)
    clean_axis(ax)

    ax_note = fig.add_axes([0.45, 0.075, 0.47, 0.08])
    ax_note.axis("off")
    p50_answer = summary["latency"]["answer_p50_s"]
    p95_answer = summary["latency"]["answer_p95_s"]
    p50_judge = summary["latency"]["judge_p50_s"]
    p95_judge = summary["latency"]["judge_p95_s"]
    ax_note.text(
        0,
        0.5,
        f"Timing: answer p50/p95 {p50_answer:.1f}s/{p95_answer:.1f}s; judge p50/p95 {p50_judge:.1f}s/{p95_judge:.1f}s",
        fontsize=11.5,
        color=MUTED,
        va="center",
    )
    return save(fig, output_dir / "01_pipeline_overview")


def render_task_scorecard(output_dir: Path, tasks: pd.DataFrame, summary: dict) -> list[Path]:
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "Task-level quality", "Mean overall score over 10 repeats per task; whiskers are 95% confidence intervals.")
    fig.subplots_adjust(left=0.23, right=0.92, top=0.84, bottom=0.11)

    y = np.arange(len(tasks))
    colors = [FAMILY_COLORS.get(fam, UW_PURPLE) for fam in tasks["family"]]
    means = tasks["overall_score_mean"].to_numpy()
    cis = tasks["overall_score_ci95"].to_numpy()
    ax.barh(y, means, color=colors, height=0.58, alpha=0.95)
    ax.errorbar(means, y, xerr=cis, fmt="none", ecolor=INK, elinewidth=1.15, capsize=3)
    ax.axvline(summary["overall"]["mean"], color=UW_METALLIC_GOLD, linewidth=1.8, linestyle=(0, (4, 3)))
    ax.text(summary["overall"]["mean"] + 0.012, len(tasks) - 0.2, "overall mean", color=UW_METALLIC_GOLD, fontsize=10, weight="bold")
    ax.set_yticks(y, tasks["label"])
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("Overall score (0-1)")
    ax.set_title("Hard prompts separate robust wins from failure modes", loc="left", pad=14)
    for idx, value in enumerate(means):
        ax.text(value + 0.012, idx, f"{value:.3f}", va="center", fontsize=10.5, weight="bold")
    clean_axis(ax)

    handles = []
    for family in sorted(tasks["family"].unique()):
        handles.append(plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=FAMILY_COLORS.get(family, UW_PURPLE), markersize=9, label=FAMILY_LABELS.get(family, family)))
    ax.legend(handles=handles, frameon=False, loc="lower right", ncol=3)
    return save(fig, output_dir / "02_task_quality_scorecard")


def render_layer_heatmap(output_dir: Path, tasks: pd.DataFrame) -> list[Path]:
    layer_keys = ["retrieval_score", "context_score", "answer_deterministic_score", "judge_score"]
    matrix = tasks[[f"{key}_mean" for key in layer_keys]].to_numpy()

    fig, ax = plt.subplots(figsize=(11.5, 7.5))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "Where performance is won or lost", "Rows are tasks sorted by overall quality; columns split the RAG pipeline.")
    fig.subplots_adjust(left=0.28, right=0.86, top=0.84, bottom=0.13)
    im = ax.imshow(matrix, vmin=0, vmax=1, aspect="auto", cmap=score_cmap())
    ax.set_xticks(np.arange(len(layer_keys)), [SCORE_LABELS[key] for key in layer_keys])
    ax.set_yticks(np.arange(len(tasks)), tasks["label"])
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", length=0)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            val = matrix[row, col]
            color = WHITE if val >= 0.74 else INK
            ax.text(col, row, f"{val:.2f}", ha="center", va="center", fontsize=10.5, weight="bold", color=color)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Mean score")
    return save(fig, output_dir / "03_pipeline_layer_heatmap")


def render_failure_taxonomy(output_dir: Path, summary: dict) -> list[Path]:
    failures = pd.DataFrame(
        [
            {
                "key": key,
                "label": FAILURE_LABELS.get(key, key.replace("_", " ")),
                "count": count,
                "rate": summary["failure_rates"].get(key, count / summary["runs"]),
            }
            for key, count in summary["failure_counts"].items()
        ]
    ).sort_values("rate", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 6.8))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "Failure taxonomy", "Run-level failure rates across the 100 hard RAG trials.")
    fig.subplots_adjust(left=0.29, right=0.91, top=0.82, bottom=0.13)
    y = np.arange(len(failures))
    norm = mpl.colors.Normalize(vmin=0, vmax=max(0.65, failures["rate"].max()))
    colors = [failure_cmap()(norm(v)) for v in failures["rate"]]
    ax.barh(y, failures["rate"], color=colors, height=0.58)
    ax.set_yticks(y, failures["label"])
    ax.set_xlim(0, max(0.7, failures["rate"].max() + 0.12))
    ax.set_xlabel("Failure rate")
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
    ax.set_title("Context and citation support dominate current failures", loc="left", pad=14)
    for idx, row in failures.reset_index(drop=True).iterrows():
        ax.text(row["rate"] + 0.012, idx, f"{row['rate']:.0%}  ({int(row['count'])}/100)", va="center", fontsize=10.5, weight="bold")
    clean_axis(ax)
    return save(fig, output_dir / "04_failure_taxonomy")


def render_failure_by_task(output_dir: Path, summary: dict, tasks: pd.DataFrame) -> list[Path]:
    failure_keys = sorted(summary["failure_counts"].keys(), key=lambda key: summary["failure_rates"].get(key, 0), reverse=True)
    matrix = []
    for task_id in tasks["id"]:
        task_failures = summary["by_task"][task_id]["failure_rates"]
        matrix.append([task_failures.get(key, 0.0) for key in failure_keys])
    arr = np.asarray(matrix)

    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "Failure rates by task", "Darker cells identify systematic failure modes, not one-off noise.")
    fig.subplots_adjust(left=0.22, right=0.91, top=0.82, bottom=0.22)
    im = ax.imshow(arr, vmin=0, vmax=1, cmap=failure_cmap(), aspect="auto")
    ax.set_yticks(np.arange(len(tasks)), tasks["label"])
    ax.set_xticks(np.arange(len(failure_keys)), [FAILURE_LABELS.get(key, key).replace(" ", "\n") for key in failure_keys], rotation=0)
    ax.tick_params(axis="both", length=0)
    for row in range(arr.shape[0]):
        for col in range(arr.shape[1]):
            val = arr[row, col]
            if val > 0:
                color = WHITE if val >= 0.72 else INK
                ax.text(col, row, f"{val:.0%}", ha="center", va="center", fontsize=8.5, weight="bold", color=color)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.035)
    cbar.set_label("Failure rate")
    return save(fig, output_dir / "05_failure_by_task_heatmap")


def render_judge_heatmap(output_dir: Path, df: pd.DataFrame, tasks: pd.DataFrame) -> list[Path]:
    judge_cols = list(JUDGE_LABELS.keys())
    by_task = df.groupby("id")[judge_cols].mean().reindex(tasks["id"])
    arr = by_task.to_numpy()

    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "LLM judge score profile", "Scores are 1-5; citation quality and faithfulness are the weak judge dimensions.")
    fig.subplots_adjust(left=0.22, right=0.91, top=0.82, bottom=0.18)
    cmap = LinearSegmentedColormap.from_list("uw_judge", ["#F7F2E6", "#D6C28C", UW_GOLD, "#7058A5", UW_PURPLE])
    im = ax.imshow(arr, vmin=1, vmax=5, cmap=cmap, aspect="auto")
    ax.set_yticks(np.arange(len(tasks)), tasks["label"])
    ax.set_xticks(np.arange(len(judge_cols)), [JUDGE_LABELS[col] for col in judge_cols])
    ax.tick_params(axis="both", length=0)
    for row in range(arr.shape[0]):
        for col in range(arr.shape[1]):
            val = arr[row, col]
            color = WHITE if val >= 4.2 else INK
            ax.text(col, row, f"{val:.1f}", ha="center", va="center", fontsize=9.5, weight="bold", color=color)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.035)
    cbar.set_label("Judge score")
    return save(fig, output_dir / "06_judge_metric_heatmap")


def render_context_faithfulness(output_dir: Path, df: pd.DataFrame, summary: dict) -> list[Path]:
    fig, ax = plt.subplots(figsize=(10.8, 7.2))
    fig.patch.set_facecolor(PAPER)
    add_title(
        fig,
        "Context recall vs. answer faithfulness",
        "Each dot is one run. High recall without faithfulness points to answer/citation issues; low recall bounds answer quality.",
    )
    fig.subplots_adjust(left=0.12, right=0.82, top=0.82, bottom=0.12)

    rng = np.random.default_rng(42)
    for family, group in df.groupby("family"):
        x = group["context_recall"].to_numpy(dtype=float) + rng.normal(0, 0.009, len(group))
        y = group["judge_faithfulness"].to_numpy(dtype=float) / 5.0 + rng.normal(0, 0.008, len(group))
        ax.scatter(
            x,
            y,
            s=62,
            color=FAMILY_COLORS.get(family, UW_PURPLE),
            edgecolor=WHITE,
            linewidth=0.7,
            alpha=0.86,
            label=FAMILY_LABELS.get(family, family),
        )

    ax.axvline(float(df["context_recall"].mean()), color=UW_METALLIC_GOLD, linewidth=1.4, linestyle=(0, (4, 3)))
    ax.axhline(float((df["judge_faithfulness"] / 5.0).mean()), color=UW_METALLIC_GOLD, linewidth=1.4, linestyle=(0, (4, 3)))
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Context recall")
    ax.set_ylabel("Judge faithfulness (normalized)")
    ax.set_title("Current failures are not purely retrieval failures", loc="left", pad=14)
    clean_axis(ax, grid_axis="both")
    ax.legend(frameon=False, bbox_to_anchor=(1.02, 0.5), loc="center left")
    return save(fig, output_dir / "07_context_recall_vs_faithfulness")


def render_latency(output_dir: Path, df: pd.DataFrame, tasks: pd.DataFrame) -> list[Path]:
    ordered = tasks.sort_values("answer_deterministic_score_mean", ascending=True)["id"].tolist()
    labels = [short_task(task_id) for task_id in ordered]
    answer_data = [df.loc[df["id"] == task_id, "answer_latency_s"].to_numpy(dtype=float) for task_id in ordered]
    judge_data = [df.loc[df["id"] == task_id, "judge_latency_s"].to_numpy(dtype=float) for task_id in ordered]

    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "Codex timing by task", "Answer and judge latency distributions over 10 repeats per hard prompt.")
    fig.subplots_adjust(left=0.11, right=0.92, top=0.82, bottom=0.28)

    positions = np.arange(len(ordered))
    bp1 = ax.boxplot(answer_data, positions=positions - 0.18, widths=0.28, patch_artist=True, showfliers=False)
    bp2 = ax.boxplot(judge_data, positions=positions + 0.18, widths=0.28, patch_artist=True, showfliers=False)
    for patch in bp1["boxes"]:
        patch.set_facecolor(UW_PURPLE)
        patch.set_alpha(0.86)
        patch.set_edgecolor(UW_PURPLE)
    for patch in bp2["boxes"]:
        patch.set_facecolor(UW_GOLD)
        patch.set_alpha(0.92)
        patch.set_edgecolor(UW_METALLIC_GOLD)
    for element in ["whiskers", "caps", "medians"]:
        for line in bp1[element] + bp2[element]:
            line.set_color(INK)
            line.set_linewidth(1.1)
    ax.set_xticks(positions, labels, rotation=0)
    ax.set_ylabel("Seconds")
    ax.set_title("Runtime is prompt-dependent but stable enough to compare", loc="left", pad=14)
    clean_axis(ax, grid_axis="y")
    handles = [
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=UW_PURPLE, markersize=9, label="answer"),
        plt.Line2D([0], [0], marker="s", color="none", markerfacecolor=UW_GOLD, markersize=9, label="judge"),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper right")
    return save(fig, output_dir / "08_latency_by_task")


def repeatability_table(df: pd.DataFrame, tasks: pd.DataFrame) -> pd.DataFrame:
    stats = df.groupby("id")["overall_score"].agg(["mean", "std", "min", "max", "count"]).reset_index()
    stats["span"] = stats["max"] - stats["min"]
    stats["ci95"] = 1.96 * stats["std"] / np.sqrt(stats["count"])
    stats["cv"] = stats["std"] / stats["mean"]
    stats = stats.merge(tasks[["id", "label", "family"]], on="id", how="left")
    return stats.sort_values("span", ascending=False).reset_index(drop=True)


def render_repeatability_runs(output_dir: Path, df: pd.DataFrame, tasks: pd.DataFrame) -> list[Path]:
    stats = repeatability_table(df, tasks)
    order = stats["id"].tolist()
    labels = stats["label"].tolist()

    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(PAPER)
    add_title(
        fig,
        "Repeatability across runs",
        "Each dot is one Codex answer+judge run. Horizontal bars show min-to-max; diamonds show the task mean.",
    )
    fig.subplots_adjust(left=0.23, right=0.91, top=0.82, bottom=0.12)

    rng = np.random.default_rng(7)
    y_positions = np.arange(len(order))
    for y, task_id in zip(y_positions, order):
        group = df[df["id"] == task_id].sort_values("run_index")
        color = FAMILY_COLORS.get(group["family"].iloc[0], UW_PURPLE)
        values = group["overall_score"].to_numpy(dtype=float)
        jitter = rng.normal(0, 0.035, len(values))
        ax.hlines(y, values.min(), values.max(), color=UW_METALLIC_GOLD, linewidth=2.2, alpha=0.95)
        ax.scatter(values, y + jitter, s=64, color=color, edgecolor=WHITE, linewidth=0.8, alpha=0.92, zorder=3)
        ax.scatter(values.mean(), y, s=108, marker="D", color=INK, edgecolor=WHITE, linewidth=0.8, zorder=4)
        ax.text(values.max() + 0.008, y, f"span {values.max() - values.min():.3f}", va="center", fontsize=9.5, color=MUTED)

    ax.set_yticks(y_positions, labels)
    ax.set_xlim(0.38, 0.96)
    ax.set_xlabel("Overall score (0-1)")
    ax.set_title("Most repeated runs are stable; abstention has the largest spread", loc="left", pad=14)
    clean_axis(ax, grid_axis="x")
    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=UW_PURPLE, markeredgecolor=WHITE, markersize=8, label="individual run"),
        plt.Line2D([0], [0], marker="D", color="none", markerfacecolor=INK, markeredgecolor=WHITE, markersize=8, label="task mean"),
        plt.Line2D([0], [0], color=UW_METALLIC_GOLD, linewidth=2.2, label="min-max span"),
    ]
    ax.legend(handles=handles, frameon=False, loc="lower right")
    return save(fig, output_dir / "09_repeatability_run_scores")


def render_repeatability_variation(output_dir: Path, df: pd.DataFrame, tasks: pd.DataFrame) -> list[Path]:
    stats = repeatability_table(df, tasks)

    fig, ax = plt.subplots(figsize=(11.8, 6.8))
    fig.patch.set_facecolor(PAPER)
    add_title(fig, "How much do repeated scores move?", "Tasks ranked by max-min score span across 10 independent runs.")
    fig.subplots_adjust(left=0.31, right=0.90, top=0.81, bottom=0.14)

    y = np.arange(len(stats))
    colors = [FAMILY_COLORS.get(fam, UW_PURPLE) for fam in stats["family"]]
    ax.barh(y, stats["span"], color=colors, height=0.58, alpha=0.95, label="max-min span")
    ax.scatter(stats["ci95"], y, s=92, color=INK, edgecolor=WHITE, linewidth=0.8, zorder=3, label="95% CI half-width")
    ax.set_yticks(y, stats["label"])
    ax.invert_yaxis()
    ax.set_xlim(0, max(0.10, stats["span"].max() + 0.02))
    ax.set_xlabel("Score movement over 10 repeats")
    ax.set_title("Observed variability is smaller than between-task differences", loc="left", pad=14)
    for idx, row in stats.iterrows():
        ax.text(row["span"] + 0.003, idx, f"{row['span']:.3f}", va="center", fontsize=10, weight="bold")
    clean_axis(ax)
    ax.legend(frameon=False, loc="lower right")
    return save(fig, output_dir / "10_repeatability_variation")


def write_repeatability_outputs(input_dir: Path, output_dir: Path, df: pd.DataFrame, tasks: pd.DataFrame, summary: dict) -> None:
    stats = repeatability_table(df, tasks)
    stats_path = output_dir / "repeatability_stats.csv"
    stats.to_csv(stats_path, index=False)

    example_task = "moire_exciton_exclude_polariton"
    record_path = input_dir / "raw" / "tasks" / example_task / "run_000" / "record.json"
    with record_path.open() as f:
        record = json.load(f)

    lines = [
        "# Example Scientific Task and Repeatability Readout",
        "",
        "## Worked Example: Moire Exciton Hard Negative",
        "",
        f"Task ID: `{example_task}`",
        "",
        f"Prompt: {record['question']}",
        "",
        "Why this is hard:",
        "- It asks for moire-exciton optical-signature references.",
        "- It explicitly forbids exciton-polariton or waveguide distractors unless they directly address moire trapping.",
        "- The evaluator therefore tests both positive retrieval and negative filtering.",
        "",
        "Gold rubric encoded in the task:",
        "- Required evidence groups: one group for moire exciton language; one group for moire-trapped valley exciton language.",
        "- Required answer concepts: moire exciton, optical/PL/photoluminescence, and explicit exclusion of distractors.",
        "- Forbidden retrieval terms: `polariton`, `waveguide`.",
        "- Forbidden answer titles: polariton/waveguide papers that should not be recommended.",
        "- Citation expectation: cite graph/paper IDs or `knowledge/papers/moire_excitons_and_optics.md`.",
        "",
        "Run 000 metric trace:",
        f"- Retrieval: recall@10 `{record['retrieval']['recall_at_k']:.2f}`, precision@10 `{record['retrieval']['precision_at_k']:.2f}`, MRR `{record['retrieval']['mrr']:.2f}`, nDCG@10 `{record['retrieval']['ndcg_at_k']:.2f}`.",
        f"- Retrieval hard-negative problem: first relevant hit was rank `{record['retrieval']['first_relevant_rank']}`, while forbidden polariton/waveguide hits appeared at the top of retrieval.",
        f"- Context: recall `{record['context']['context_recall']:.2f}`, precision proxy `{record['context']['context_precision']:.2f}`.",
        f"- Deterministic answer checks: concept coverage `{record['answer_metrics']['required_concept_coverage']:.2f}`, citation precision proxy `{record['answer_metrics']['citation_precision_proxy']:.2f}`, behavior OK `{record['answer_metrics']['behavior_ok']}`.",
        f"- LLM judge: context relevance `{record['judge']['context_relevance']}/5`, faithfulness `{record['judge']['faithfulness']}/5`, citation quality `{record['judge']['citation_quality']}/5`, scientific correctness `{record['judge']['scientific_correctness']}/5`.",
        f"- Composite scores: retrieval `{record['scores']['retrieval_score']:.3f}`, context `{record['scores']['context_score']:.3f}`, answer `{record['scores']['answer_deterministic_score']:.3f}`, judge `{record['scores']['judge_score']:.3f}`, overall `{record['scores']['overall_score']:.3f}`.",
        "",
        "Scoring model:",
        "- Retrieval score averages recall@10, precision@10, MRR, nDCG@10, and a binary no-forbidden-retrieval-hit term.",
        "- Context score averages context recall and an average-precision-like context precision proxy.",
        "- Deterministic answer score averages required concept coverage, citation precision proxy, required citation-pattern coverage, expected behavior, atomic support proxy, and absence of forbidden answer terms.",
        "- Judge score averages seven normalized 1-5 judge metrics: context relevance, answer relevance, faithfulness, citation quality, scientific correctness, uncertainty calibration, and actionability.",
        "- Overall score is the mean of retrieval, context, deterministic answer, and judge scores.",
        "",
        "Interpretation for this example:",
        "- The answer often understands the task, but retrieval brings polariton/waveguide distractors to the top.",
        "- That creates low retrieval score and weak judge faithfulness/citation quality even when the final answer tries to exclude the distractors.",
        "- This is a concrete negative-filtering failure, not just a generation failure.",
        "",
        "## Repeatability Summary",
        "",
        f"Across all tasks, mean overall score is `{summary['overall']['mean']:.3f} +/- {summary['overall']['ci95']:.3f}` 95% CI.",
        "Per-task run-to-run variation is small compared with between-task differences.",
        "",
        "| Task | Mean | Std | 95% CI | Min | Max | Span |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in stats.iterrows():
        label = row["label"].replace("\n", " ")
        lines.append(
            f"| {label} | {row['mean']:.3f} | {row['std']:.3f} | {row['ci95']:.3f} | {row['min']:.3f} | {row['max']:.3f} | {row['span']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Presentation figures:",
            "- `09_repeatability_run_scores.*` shows every run-level overall score.",
            "- `10_repeatability_variation.*` ranks tasks by score span and CI.",
            f"- Raw repeatability table: `{stats_path.name}`.",
        ]
    )
    (output_dir / "task_example_and_repeatability.md").write_text("\n".join(lines) + "\n")


def render_contact_sheet(output_dir: Path, png_paths: list[Path]) -> list[Path]:
    selected = png_paths
    ncols = 2
    nrows = math.ceil(len(selected) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(14, 5 * nrows))
    axes_arr = np.asarray(axes).reshape(-1)
    fig.patch.set_facecolor(PAPER)
    for ax, path in zip(axes_arr, selected):
        img = mpimg.imread(path)
        ax.imshow(img)
        ax.set_title(path.stem.replace("_", " "), loc="left", fontsize=12, color=UW_PURPLE, weight="bold")
        ax.axis("off")
    for ax in axes_arr[len(selected) :]:
        ax.axis("off")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02, hspace=0.15, wspace=0.06)
    return save(fig, output_dir / "00_review_contact_sheet")


def write_index(output_dir: Path, all_paths: list[Path], font_family: str) -> None:
    groups: dict[str, list[Path]] = {}
    for path in all_paths:
        groups.setdefault(path.stem, []).append(path)
    lines = [
        "# UW-Styled Hard RAG Benchmark Figures",
        "",
        f"Font family used: `{font_family}`.",
        "Palette: UW purple `#4B2E83`, UW gold `#B7A57A`, metallic gold `#85754D`.",
        "",
        "Generated files:",
        "",
    ]
    for stem in sorted(groups):
        variants = ", ".join(path.name for path in sorted(groups[stem]))
        lines.append(f"- `{stem}`: {variants}")
    (output_dir / "README.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("outputs/rag_hard_quality_2026-07-13_n100"))
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir / "plots_uw_review"
    font_family = find_or_fetch_open_sans(output_dir / "assets" / "fonts")
    apply_uw_style(font_family)

    df, summary = load_data(input_dir)
    tasks = task_table(df, summary)

    all_paths: list[Path] = []
    all_paths.extend(render_overview(output_dir, df, summary))
    all_paths.extend(render_task_scorecard(output_dir, tasks, summary))
    all_paths.extend(render_layer_heatmap(output_dir, tasks))
    all_paths.extend(render_failure_taxonomy(output_dir, summary))
    all_paths.extend(render_failure_by_task(output_dir, summary, tasks))
    all_paths.extend(render_judge_heatmap(output_dir, df, tasks))
    all_paths.extend(render_context_faithfulness(output_dir, df, summary))
    all_paths.extend(render_latency(output_dir, df, tasks))
    all_paths.extend(render_repeatability_runs(output_dir, df, tasks))
    all_paths.extend(render_repeatability_variation(output_dir, df, tasks))
    write_repeatability_outputs(input_dir, output_dir, df, tasks, summary)

    png_paths = [path for path in all_paths if path.suffix == ".png"]
    all_paths.extend(render_contact_sheet(output_dir, png_paths))
    write_index(output_dir, all_paths, font_family)

    print(f"wrote {len(all_paths)} figure files to {output_dir}")
    print(f"font: {font_family}")


if __name__ == "__main__":
    main()
