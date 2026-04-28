#!/usr/bin/env python3
"""
query_corpus.py — Compare a single data file against the physics corpus.

Extracts metrics from the file, looks up nearest neighbors, and reports
any features that are statistically unusual compared to the stored corpus.

Designed for the LLM to call when a file looks interesting:
  python3 tools/query_corpus.py <path_to_mat_file> --modality RMCD [--sample D93]

Output: plain text, ~15 lines, optimized for LLM reading.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.analyze.dispatch import analyze_file  # noqa: E402
from monitor.corpus import corpus_stats, format_corpus_result, query_similar  # noqa: E402
from monitor.plot_embed import (  # noqa: E402
    format_plot_result, plot_corpus_stats, query_plot_similar,
)
from monitor.schemas import FileArrivedEvent  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Compare a .mat file against the physics corpus."
    )
    ap.add_argument("filepath", help="Path to .mat file")
    ap.add_argument(
        "--modality", default=None,
        choices=["PL", "RMCD", "Reflectance", "unknown"],
        help="Measurement modality (auto-detect if omitted)"
    )
    ap.add_argument("--sample", default=None,
                    help="Restrict corpus search to this sample label (optional)")
    ap.add_argument("--corpus-dir", default="state/corpus",
                    help="Corpus directory (default: state/corpus)")
    ap.add_argument("--n", type=int, default=5, help="Number of nearest neighbors to show")
    ap.add_argument("--json", action="store_true", dest="output_json",
                    help="Output raw JSON instead of plain text")
    args = ap.parse_args()

    cwd = Path.cwd()
    corpus_dir = (cwd / args.corpus_dir).resolve()
    path = Path(args.filepath).resolve()

    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    # --- Auto-detect modality from filename if not given ---
    modality = args.modality or "unknown"
    if modality == "unknown":
        name = path.name.lower()
        if "rmcd" in name or "hyster" in name:
            modality = "RMCD"
        elif "refl" in name or "whitelight" in name:
            modality = "Reflectance"
        else:
            modality = "PL"  # default

    # --- Analyze the file to extract metrics ---
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    evt = FileArrivedEvent(
        event_id=str(path),
        run_id="",
        filename=path.name,
        local_path=str(path),
        file_size_bytes=path.stat().st_size,
        mtime=mtime,
        inferred_modality=modality,
    )
    ar = analyze_file(evt, corpus_dir=None)  # don't query inside; we'll do it below

    if not ar.loadable:
        print(f"ERROR: could not load file (load_failed)", file=sys.stderr)
        sys.exit(1)

    if not ar.metrics:
        print("ERROR: no metrics extracted — check modality or file format", file=sys.stderr)
        sys.exit(1)

    # --- Corpus query ---
    stats = corpus_stats(corpus_dir)
    if not stats:
        print("Corpus is empty. Run build_corpus.py first.", file=sys.stderr)
        sys.exit(1)

    result = query_similar(
        ar.metrics, modality, corpus_dir,
        n_results=args.n,
        sample_filter=args.sample,
    )

    if args.output_json:
        import json
        out = {
            "file": str(path),
            "modality": modality,
            "metrics": {k: v for k, v in ar.metrics.items()
                        if isinstance(v, (int, float))},
            "quality_flags": ar.quality_flags,
            "corpus_result": result,
        }
        print(json.dumps(out, indent=2))
        return

    # --- Plain text output for LLM ---
    print(f"File:      {path.name}")
    print(f"Modality:  {modality}")

    # Key metrics
    key_metrics = {k: v for k, v in ar.metrics.items()
                   if isinstance(v, (int, float))
                   and k not in ("file_size_bytes", "variable_count", "integration_time_s")}
    if key_metrics:
        metric_str = "  ".join(f"{k}={v:.5g}" for k, v in list(key_metrics.items())[:6])
        print(f"Metrics:   {metric_str}")

    if ar.quality_flags:
        print(f"Flags:     {', '.join(ar.quality_flags)}")

    print()

    if result is None:
        total = sum(stats.values())
        print(f"Corpus ({total} total files): collection too small or no matching modality.")
        print(f"  Collections: {stats}")
    else:
        print(format_corpus_result(result))

    # --- Plot corpus (DINOv2) ---
    plot_stats = plot_corpus_stats(corpus_dir)
    if plot_stats:
        print()
        mat_data = None
        try:
            from monitor.analyze.loader import load_mat
            mat_data, _ = load_mat(path)
        except Exception:
            pass
        if mat_data and ar.metrics:
            plot_result = query_plot_similar(
                mat_data, ar.metrics, modality, corpus_dir,
                n_results=args.n, sample_filter=args.sample,
            )
            print(format_plot_result(plot_result))
        else:
            print(f"Plot corpus: {plot_stats} (could not load mat_data for query)")

    print()
    print(f"Metric corpus: {stats}")
    if plot_stats:
        print(f"Plot corpus:   {plot_stats}")


if __name__ == "__main__":
    main()
