#!/usr/bin/env python3
"""
plot_run_health.py — Timeline of anomaly scores across a run directory.

Analyzes all .mat files in a directory (or active run's local_dir) in mtime order,
plots anomaly score vs file index, and overlays key physics metric trends.

Useful for: a quick visual of whether data quality is drifting during a long sweep.
Output: out/plots/<run_id or dir_stem>_health.png  (path printed to stdout)

Usage:
  python3 tools/plot_run_health.py --dir data/dropbox_cache/.../Spot3 --modality RMCD
  python3 tools/plot_run_health.py --run-id <id>    # uses registered run's local_dir
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

_MAT_EXTS = {".mat", ".h5", ".hdf5", ".npy", ".csv"}


def _collect_files(directory: Path) -> list[Path]:
    files = [p for p in directory.rglob("*") if p.suffix in _MAT_EXTS and p.is_file()]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def _analyze_files(paths: list[Path], modality: str, corpus_dir: "Path | None" = None, sample: str = "") -> list[dict]:
    from monitor.analyze import analyze_file
    from monitor.schemas import FileArrivedEvent

    results = []
    for p in paths:
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        evt = FileArrivedEvent(
            event_id=str(p),
            run_id="",
            filename=p.name,
            local_path=str(p),
            file_size_bytes=p.stat().st_size,
            mtime=mtime,
            inferred_modality=modality,
        )
        ar = analyze_file(
            evt,
            corpus_dir=corpus_dir if (corpus_dir and corpus_dir.exists()) else None,
            corpus_sample=sample or None,
        )
        results.append({
            "name": p.name,
            "score": ar.anomaly_score,
            "flags": ar.quality_flags,
            "metrics": ar.metrics,
        })
    return results


def _plot(results: list[dict], out_path: Path, modality: str, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    scores = [r["score"] for r in results]
    idx = list(range(len(scores)))

    # Pick one physics metric to overlay
    metric_key = {
        "PL": "peak_energy_eV",
        "RMCD": "coercive_field_T",
        "Reflectance": "resonance_center_eV",
    }.get(modality)

    metric_vals = None
    metric_idx = None
    if metric_key:
        metric_vals = [r["metrics"].get(metric_key) for r in results]
        valid = [(i, v) for i, v in enumerate(metric_vals) if v is not None]
        if len(valid) >= 2:
            metric_idx = [v[0] for v in valid]
            metric_vals = [v[1] for v in valid]
        else:
            metric_vals = None

    has_metric = metric_vals is not None
    nrows = 2 if has_metric else 1

    # Cap width at 14 inches — bin files if there are too many
    n = len(scores)
    MAX_WIDTH = 14
    px_per_file = MAX_WIDTH / max(n, 1)
    if px_per_file < 0.04:  # more than ~350 files — bin into ~200 buckets
        bin_size = max(1, n // 200)
        def _bin(vals, func=np.mean):
            return [func(vals[i:i+bin_size]) for i in range(0, len(vals), bin_size)]
        scores_plot = _bin(scores, np.max)  # max score in each bin
        idx_plot = list(range(len(scores_plot)))
        # For metric: use mean per bin, only bins that have data
        if has_metric:
            # Scatter the sparse metric data onto a dense grid first
            dense = np.full(n, np.nan)
            for ii, vv in zip(metric_idx, metric_vals):
                dense[ii] = vv
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore", RuntimeWarning)
                metric_binned = [np.nanmean(dense[i:i+bin_size]) for i in range(0, n, bin_size)]
            metric_idx_plot = [i for i, v in enumerate(metric_binned) if not np.isnan(v)]
            metric_vals_plot = [v for v in metric_binned if not np.isnan(v)]
        xlabel = f"File bin (~{bin_size} files each, mtime order)"
    else:
        scores_plot = scores
        idx_plot = idx
        metric_idx_plot = metric_idx
        metric_vals_plot = metric_vals
        xlabel = "File index (mtime order)"
        bin_size = 1

    width = max(6, min(MAX_WIDTH, len(scores_plot) * 0.06 + 2))
    fig, axes = plt.subplots(nrows, 1, figsize=(width, 3.5 * nrows), dpi=150, sharex=True)
    if nrows == 1:
        axes = [axes]

    # Anomaly score bar chart
    ax = axes[0]
    colors = ["#dc2626" if s >= 0.5 else "#f59e0b" if s > 0 else "#22c55e" for s in scores_plot]
    ax.bar(idx_plot, scores_plot, color=colors, width=0.8)
    ax.axhline(0.5, color="#dc2626", lw=0.8, ls="--", label="error threshold")
    ax.axhline(0.2, color="#f59e0b", lw=0.8, ls=":", label="warn threshold")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Anomaly score", fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.legend(fontsize=6, loc="upper right")
    ax.tick_params(labelsize=7)

    # Annotate only error-level bins/files (keep readable)
    if bin_size == 1:
        for i, r in enumerate(results):
            if r["score"] >= 0.5:
                short_flags = ", ".join(f.split(":")[0] for f in r["flags"])[:25]
                ax.annotate(short_flags, (i, r["score"] + 0.02),
                            fontsize=5, ha="center", va="bottom", rotation=55, color="#dc2626")

    # Physics metric trend
    if has_metric:
        ax2 = axes[1]
        ax2.plot(metric_idx_plot, metric_vals_plot,
                 "o-" if len(metric_idx_plot) < 80 else "-",
                 ms=3, lw=1.0, color="#2563eb")
        ax2.set_ylabel(metric_key, fontsize=8)
        ax2.set_xlabel(xlabel, fontsize=8)
        ax2.tick_params(labelsize=7)
        # Mark any large jumps in the plotted (possibly binned) trend
        if len(metric_vals_plot) > 1:
            diffs = [abs(metric_vals_plot[i+1] - metric_vals_plot[i])
                     for i in range(len(metric_vals_plot)-1)]
            threshold = 3 * (sum(diffs) / len(diffs)) if diffs else 0
            for j, d in enumerate(diffs):
                if d > threshold and threshold > 0:
                    mid = (metric_idx_plot[j] + metric_idx_plot[j+1]) / 2
                    ax2.axvline(mid, color="#dc2626", lw=0.7, ls="--", alpha=0.6)
    else:
        axes[0].set_xlabel(xlabel, fontsize=8)

    plt.tight_layout(pad=0.8)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot anomaly score timeline for a data directory.")
    ap.add_argument("--dir", default=None, help="Directory to analyze")
    ap.add_argument("--run-id", default=None, help="Use registered run's local_dir")
    ap.add_argument("--modality", default="unknown",
                    choices=["PL", "RMCD", "Reflectance", "unknown"],
                    help="Measurement modality")
    ap.add_argument("--out", default=None, help="Output image path")
    ap.add_argument(
        "--state", default="state/active_runs.json",
        help="Path to active_runs.json"
    )
    ap.add_argument("--sample", default=None,
                    help="Sample label for corpus lookup (e.g. D93)")
    ap.add_argument("--corpus-dir", default=None,
                    help="Corpus directory (default: <workspace>/state/corpus)")
    args = ap.parse_args()

    cwd = Path.cwd()

    # Resolve directory
    sample = args.sample
    if args.run_id:
        from monitor.active_run import load_active_runs
        runs = load_active_runs(state_path=(cwd / args.state).resolve())
        match = [r for r in runs if r.run_id.startswith(args.run_id)]
        if not match:
            print(f"ERROR: no run matching {args.run_id}", file=sys.stderr)
            sys.exit(1)
        run = match[0]
        directory = Path(run.local_dir)
        modality = run.modality
        stem = run.run_id[:8]
        title_base = f"Run {stem} | {run.sample} | {run.modality}"
        if sample is None:
            sample = run.sample
    elif args.dir:
        directory = Path(args.dir).resolve()
        modality = args.modality
        stem = directory.name[:30]
        title_base = f"{stem} | {modality}"
    else:
        print("ERROR: provide --dir or --run-id", file=sys.stderr)
        sys.exit(1)

    if not directory.exists():
        print(f"ERROR: directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    corpus_dir = Path(args.corpus_dir).resolve() if args.corpus_dir else _WORKSPACE / "state" / "corpus"
    if not corpus_dir.exists():
        corpus_dir = None

    files = _collect_files(directory)
    if not files:
        print(f"ERROR: no data files found in {directory}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(files)} files...", file=sys.stderr)
    if corpus_dir:
        print(f"  (using corpus: {corpus_dir})", file=sys.stderr)
    results = _analyze_files(files, modality, corpus_dir=corpus_dir, sample=sample or "")

    out_dir = _WORKSPACE / "out" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out).resolve() if args.out else out_dir / f"{stem}_health.png"

    title = f"{title_base} | {len(files)} files"
    _plot(results, out_path, modality, title)

    n_error = sum(1 for r in results if r["score"] >= 0.5)
    n_warn = sum(1 for r in results if 0 < r["score"] < 0.5)
    print(out_path)
    print(f"  {len(files)} files: {len(files)-n_error-n_warn} clean, {n_warn} warnings, {n_error} errors",
          file=sys.stderr)


if __name__ == "__main__":
    main()
