#!/usr/bin/env python3
"""
make_comparison_plots.py — For each run, find the worst-flagged and cleanest
files, plot them side by side for manual inspection.

Produces:
  out/reports/health_summary/comparisons/<run_id>_error_<n>.png
  out/reports/health_summary/comparisons/<run_id>_clean_<n>.png
  out/reports/health_summary/comparisons/index.json   — metadata for LaTeX

Usage:
  python3 tools/make_comparison_plots.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.analyze.dispatch import analyze_file  # noqa
from monitor.analyze.loader import load_mat  # noqa
from monitor.schemas import FileArrivedEvent  # noqa
from tools.quick_plot import plot_pl, plot_rmcd, plot_reflectance  # noqa

_CORPUS = _WORKSPACE / "state" / "corpus"
_OUT = _WORKSPACE / "out" / "reports" / "health_summary" / "comparisons"
_MAT_EXTS = {".mat", ".h5", ".hdf5", ".npy"}

# Each entry: (label, directory, modality, sample)
RUNS = [
    ("D93_Spot3",  "data/dropbox_cache/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data/Spot 3",          "RMCD",        "D93"),
    ("D88_run2",   "data/dropbox_cache/tMoTe2_Measuring/courtney_christiano_D88_run2_AAA_attodry522/Data",    "RMCD",        "D88"),
    ("B79",        "data/dropbox_cache/tMoTe2_Measuring/WJL_Zengde_B79_Attodry911",                          "Reflectance", "B79"),
    ("C7",         "data/dropbox_cache/tMoTe2_Measuring/Zengde_WJL_C7_Attodry911",                           "PL",          "C7"),
    ("MT48",       "data/dropbox_cache/tMoTe2_Measuring/Shuai_CWB_MT48_attodry911",                          "PL",          "MT48"),
    ("A5",         "data/dropbox_cache/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry",               "PL",          "A5"),
]

N_EACH = 2   # how many error + clean examples per run


def _score_files(directory: Path, modality: str, sample: str) -> list[dict]:
    files = sorted(
        [p for p in directory.rglob("*") if p.suffix in _MAT_EXTS and p.is_file()],
        key=lambda p: p.stat().st_mtime,
    )
    results = []
    for p in files:
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        evt = FileArrivedEvent(
            event_id=str(p), run_id="", filename=p.name,
            local_path=str(p), file_size_bytes=p.stat().st_size,
            mtime=mtime, inferred_modality=modality,
        )
        ar = analyze_file(evt, corpus_dir=_CORPUS, corpus_sample=sample)
        results.append({
            "path": p,
            "score": ar.anomaly_score,
            "flags": ar.quality_flags,
            "reasons": ar.anomaly_reasons,
            "metrics": {k: v for k, v in ar.metrics.items() if isinstance(v, (int, float))},
            "loadable": ar.loadable,
        })
    return results


def _call_quick_plot(path: Path, modality: str, out_path: Path) -> bool:
    mat_data, _ = load_mat(path)
    if mat_data is None:
        return False
    try:
        if modality == "PL":
            status = plot_pl(mat_data, out_path)
        elif modality == "RMCD":
            status = plot_rmcd(mat_data, out_path)
        elif modality == "Reflectance":
            status = plot_reflectance(mat_data, out_path)
        else:
            return False
        return status == "ok"
    except Exception as e:
        print(f"  plot failed for {path.name}: {e}", file=sys.stderr)
        return False


def main() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    index = []

    for run_label, run_dir_str, modality, sample in RUNS:
        directory = (_WORKSPACE / run_dir_str).resolve()
        if not directory.exists():
            print(f"SKIP {run_label}: directory not found", file=sys.stderr)
            continue

        print(f"\n=== {run_label} ({modality}) ===", file=sys.stderr)
        results = _score_files(directory, modality, sample)
        if not results:
            print(f"  no files found", file=sys.stderr)
            continue

        # Sort by score descending → errors first
        by_score = sorted(results, key=lambda r: r["score"], reverse=True)

        # Pick top N errors (score >= 0.5 preferred, else just highest)
        errors = [r for r in by_score if r["score"] >= 0.5 and r["loadable"]][:N_EACH]
        if len(errors) < N_EACH:
            # Fall back to highest-scoring loadable
            errors = [r for r in by_score if r["loadable"]][:N_EACH]

        # Pick top N clean (score == 0 preferred, else lowest)
        cleans = [r for r in reversed(by_score) if r["score"] == 0.0 and r["loadable"]][:N_EACH]
        if len(cleans) < N_EACH:
            cleans = [r for r in reversed(by_score) if r["loadable"]][:N_EACH]

        run_entry = {
            "run": run_label,
            "modality": modality,
            "sample": sample,
            "n_files": len(results),
            "errors": [],
            "cleans": [],
        }

        for i, r in enumerate(errors):
            out_path = _OUT / f"{run_label}_error_{i+1}.png"
            ok = _call_quick_plot(r["path"], modality, out_path)
            tag = "error" if r["score"] >= 0.5 else "high_warn"
            entry = {
                "filename": r["path"].name,
                "score": r["score"],
                "flags": r["flags"],
                "reasons": r["reasons"],
                "metrics": r["metrics"],
                "plot": str(out_path.name) if ok else None,
                "tag": tag,
            }
            run_entry["errors"].append(entry)
            status = "ok" if ok else "plot_failed"
            print(f"  {tag} ({r['score']:.3f}) {r['path'].name[:60]} → {status}", file=sys.stderr)

        for i, r in enumerate(cleans):
            out_path = _OUT / f"{run_label}_clean_{i+1}.png"
            ok = _call_quick_plot(r["path"], modality, out_path)
            entry = {
                "filename": r["path"].name,
                "score": r["score"],
                "flags": r["flags"],
                "reasons": r["reasons"],
                "metrics": r["metrics"],
                "plot": str(out_path.name) if ok else None,
                "tag": "clean",
            }
            run_entry["cleans"].append(entry)
            status = "ok" if ok else "plot_failed"
            print(f"  clean  ({r['score']:.3f}) {r['path'].name[:60]} → {status}", file=sys.stderr)

        index.append(run_entry)

    index_path = _OUT / "index.json"
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, default=str)
    print(f"\nIndex written to {index_path}")
    print(f"Plots written to {_OUT}")


if __name__ == "__main__":
    main()
