#!/usr/bin/env python3
"""
plot_mixed_run_health.py — Health timeline for a mixed-modality run directory.

Auto-detects the modality of each file from filename and variable contents,
analyzes each with the correct analyzer, then plots three separate anomaly
score timelines (one per modality) in chronological (mtime) order.

Usage:
  python3 tools/plot_mixed_run_health.py --dir <path> --sample D88
  python3 tools/plot_mixed_run_health.py --dir <path> --sample D88 --out out/D88_mixed.png
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


def _infer_modality(path: Path, mat_data: dict | None) -> str:
    """
    Detect modality from filename first, then variable keys.
    Returns "PL", "RMCD", "Reflectance", or "unknown".
    """
    name = path.name.lower()

    # Filename-based (most reliable for lab naming conventions)
    if "rmcd" in name or "hyster" in name:
        return "RMCD"
    if "reflectance" in name or "whitelight" in name or "refl" in name:
        return "Reflectance"
    if ("pl" in name or "doping" in name or "dopingdep" in name
            or "dualgate" in name or "spatialscan" in name
            or "spatialmap" in name or "dispersion" in name):
        # Distinguish PL from reflectance dualgate by variable presence
        if mat_data is not None and "RMCD_up" in mat_data:
            return "RMCD"
        if mat_data is not None and ("datR" in mat_data or
                ("dat" in mat_data and "RMCD" not in mat_data
                 and "w" not in mat_data)):
            return "Reflectance"
        return "PL"

    # Variable-based fallback
    if mat_data is not None:
        if "RMCD_up" in mat_data or "RMCD_down" in mat_data or "RMCD" in mat_data:
            return "RMCD"
        if "datR" in mat_data:
            return "Reflectance"
        if "w" in mat_data and any(k in mat_data for k in ("I", "dat", "spec")):
            return "PL"

    return "unknown"


def _analyze_files(paths: list[Path], sample: str, corpus_dir: Path | None) -> list[dict]:
    from monitor.analyze.dispatch import analyze_file
    from monitor.analyze.loader import load_mat
    from monitor.schemas import FileArrivedEvent

    results = []
    for p in paths:
        mat_data, _ = load_mat(p)
        modality = _infer_modality(p, mat_data)

        mtime_dt = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        evt = FileArrivedEvent(
            event_id=str(p), run_id="", filename=p.name,
            local_path=str(p), file_size_bytes=p.stat().st_size,
            mtime=mtime_dt.isoformat(), inferred_modality=modality,
        )
        ar = analyze_file(
            evt,
            corpus_dir=corpus_dir if (corpus_dir and corpus_dir.exists()) else None,
            corpus_sample=sample or None,
        )
        results.append({
            "name": p.name,
            "mtime": mtime_dt,
            "modality": modality,
            "score": ar.anomaly_score,
            "flags": ar.quality_flags,
            "metrics": ar.metrics,
        })
    return results


def _plot(results: list[dict], out_path: Path, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    modalities = ["PL", "RMCD", "Reflectance"]
    colors_err  = {"PL": "#dc2626", "RMCD": "#dc2626", "Reflectance": "#dc2626"}
    colors_warn = {"PL": "#f59e0b", "RMCD": "#f59e0b", "Reflectance": "#f59e0b"}
    colors_clean= {"PL": "#22c55e", "RMCD": "#2563eb",  "Reflectance": "#7c3aed"}

    # Metric to overlay per modality
    metric_key = {"PL": "peak_energy_eV", "RMCD": "coercive_field_T",
                  "Reflectance": "resonance_center_eV"}

    # Split by modality, preserve global mtime ordering
    by_mod = {m: [] for m in modalities}
    for r in results:
        if r["modality"] in by_mod:
            by_mod[r["modality"]].append(r)

    # Only plot modalities that have data
    active = [m for m in modalities if len(by_mod[m]) >= 2]
    if not active:
        print("No recognized modality files found.", file=sys.stderr)
        return

    nrows = len(active) * 2  # score + metric per modality
    fig, axes = plt.subplots(nrows, 1, figsize=(14, 3.0 * nrows), dpi=130,
                             gridspec_kw={"hspace": 0.1})
    axes = list(axes)

    ax_idx = 0
    for mod in active:
        rows = by_mod[mod]
        n = len(rows)
        scores = [r["score"] for r in rows]
        idx = list(range(n))

        # Bin if > 350
        MAX_W = 14
        bin_size = max(1, n // 200) if n / max(n, 1) * 0.04 < 0.04 else 1
        if n > 350:
            bin_size = max(1, n // 200)
            scores_plot = [max(scores[i:i+bin_size]) for i in range(0, n, bin_size)]
            idx_plot = list(range(len(scores_plot)))
            xlabel = f"File bin (~{bin_size} files each, mtime order)"
        else:
            scores_plot = scores
            idx_plot = idx
            xlabel = "File index (mtime order)"
            bin_size = 1

        bar_colors = ["#dc2626" if s >= 0.5 else "#f59e0b" if s > 0 else colors_clean[mod]
                      for s in scores_plot]

        # Score panel
        ax = axes[ax_idx]; ax_idx += 1
        ax.bar(idx_plot, scores_plot, color=bar_colors, width=0.8)
        ax.axhline(0.5, color="#dc2626", lw=0.7, ls="--")
        ax.axhline(0.2, color="#f59e0b", lw=0.7, ls=":")
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Anomaly score", fontsize=7)
        n_err  = sum(1 for s in scores if s >= 0.5)
        n_warn = sum(1 for s in scores if 0 < s < 0.5)
        n_clean= sum(1 for s in scores if s == 0.0)
        ax.set_title(f"{mod}  —  {n} files: {n_clean} clean / {n_warn} warn / {n_err} error",
                     fontsize=8, loc="left", pad=3)
        ax.tick_params(labelsize=6)
        ax.set_xticklabels([])

        # Annotate error bars (only when not binned)
        if bin_size == 1:
            for i, r in enumerate(rows):
                if r["score"] >= 0.5:
                    short = ", ".join(f.split(":")[0] for f in r["flags"])[:22]
                    ax.annotate(short, (i, r["score"] + 0.02),
                                fontsize=4, ha="center", va="bottom",
                                rotation=55, color="#dc2626")

        # Metric trend panel
        mk = metric_key.get(mod)
        ax2 = axes[ax_idx]; ax_idx += 1
        if mk:
            vals = [r["metrics"].get(mk) for r in rows]
            valid = [(i, v) for i, v in enumerate(vals) if v is not None]
            if len(valid) >= 2:
                mi = [x[0] for x in valid]
                mv = [x[1] for x in valid]
                if bin_size > 1:
                    dense = np.full(n, np.nan)
                    for ii, vv in zip(mi, mv):
                        dense[ii] = vv
                    import warnings as _w
                    with _w.catch_warnings():
                        _w.simplefilter("ignore", RuntimeWarning)
                        mb = [np.nanmean(dense[i:i+bin_size]) for i in range(0, n, bin_size)]
                    mi = [i for i, v in enumerate(mb) if not np.isnan(v)]
                    mv = [v for v in mb if not np.isnan(v)]
                ax2.plot(mi, mv, "o-" if len(mi) < 80 else "-",
                         ms=2, lw=0.9, color="#1d4ed8")
                ax2.set_ylabel(mk, fontsize=6)
                # Jump detection
                if len(mv) > 1:
                    diffs = [abs(mv[i+1]-mv[i]) for i in range(len(mv)-1)]
                    thr = 3*(sum(diffs)/len(diffs)) if diffs else 0
                    for j, d in enumerate(diffs):
                        if d > thr > 0:
                            mid = (mi[j]+mi[j+1])/2
                            ax2.axvline(mid, color="#dc2626", lw=0.6, ls="--", alpha=0.5)
            else:
                ax2.text(0.5, 0.5, f"no {mk} data", ha="center", va="center",
                         transform=ax2.transAxes, fontsize=7, color="gray")
                ax2.set_ylabel(mk, fontsize=6)
        else:
            ax2.set_visible(False)
            ax_idx -= 1  # reuse
        ax2.set_xlabel(xlabel, fontsize=7)
        ax2.tick_params(labelsize=6)

    fig.suptitle(title, fontsize=9, y=1.001)
    plt.tight_layout(pad=0.6)
    plt.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Mixed-modality data directory")
    ap.add_argument("--sample", default="", help="Sample label for corpus lookup")
    ap.add_argument("--out", default=None)
    ap.add_argument("--corpus-dir", default=None)
    args = ap.parse_args()

    directory = Path(args.dir).resolve()
    if not directory.exists():
        print(f"ERROR: not found: {directory}", file=sys.stderr); sys.exit(1)

    corpus_dir = (Path(args.corpus_dir).resolve() if args.corpus_dir
                  else _WORKSPACE / "state" / "corpus")
    if not corpus_dir.exists():
        corpus_dir = None

    files = sorted(
        [p for p in directory.rglob("*") if p.suffix in _MAT_EXTS and p.is_file()],
        key=lambda p: p.stat().st_mtime,
    )
    if not files:
        print("ERROR: no data files found", file=sys.stderr); sys.exit(1)

    print(f"Analyzing {len(files)} files (auto-detecting modality)...", file=sys.stderr)
    if corpus_dir:
        print(f"  (corpus: {corpus_dir})", file=sys.stderr)

    results = _analyze_files(files, args.sample, corpus_dir)

    # Summary by modality
    from collections import Counter
    mod_counts = Counter(r["modality"] for r in results)
    for mod, cnt in sorted(mod_counts.items()):
        sub = [r for r in results if r["modality"] == mod]
        n_err  = sum(1 for r in sub if r["score"] >= 0.5)
        n_warn = sum(1 for r in sub if 0 < r["score"] < 0.5)
        print(f"  {mod:12s}: {cnt:4d} files  {cnt-n_err-n_warn} clean / {n_warn} warn / {n_err} err",
              file=sys.stderr)

    stem = directory.name[:30]
    out_dir = _WORKSPACE / "out" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out).resolve() if args.out else out_dir / f"{stem}_mixed_health.png"

    title = f"{stem} | {args.sample} | {len(files)} files (auto-detected modality)"
    _plot(results, out_path, title)
    print(out_path)


if __name__ == "__main__":
    main()
