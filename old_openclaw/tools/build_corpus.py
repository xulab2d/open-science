#!/usr/bin/env python3
"""
build_corpus.py — Seed the physics corpus from historical data.

Walks a data directory, analyzes every .mat file, and adds clean files
(no load errors, no all-NaN primary arrays) to the corpus vector store.
Flagged/bad files are skipped so the corpus represents normal physics.

Usage:
  python3 tools/build_corpus.py \
    --dir "data/dropbox_cache/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522/Data" \
    --modality RMCD --sample D93

  python3 tools/build_corpus.py --dir data/dropbox_cache/tMoTe2_Measuring \
    --modality PL --sample B79 --dry-run

Writes to: state/corpus/
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
from monitor.corpus import corpus_stats  # noqa: E402
from monitor.schemas import FileArrivedEvent  # noqa: E402

_MAT_EXTS = {".mat", ".h5", ".hdf5", ".npy"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed the physics corpus from historical data.")
    ap.add_argument("--dir", required=True, help="Directory to scan recursively")
    ap.add_argument("--modality", required=True,
                    choices=["PL", "RMCD", "Reflectance", "unknown"])
    ap.add_argument("--sample", default="unknown", help="Sample label (e.g. D93)")
    ap.add_argument("--corpus-dir", default="state/corpus",
                    help="Corpus storage directory (default: state/corpus)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Analyze but don't write to corpus")
    ap.add_argument("--plot-embed", action="store_true",
                    help="Also build DINOv2 plot embeddings (requires torch + transformers). "
                         "analyze_file already handles this when add_to_corpus=True, so this "
                         "flag is only needed if you skipped it on a previous run.")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    cwd = Path.cwd()
    directory = Path(args.dir).resolve()
    if not directory.exists():
        print(f"ERROR: directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    corpus_dir = (cwd / args.corpus_dir).resolve()

    files = sorted(
        [p for p in directory.rglob("*") if p.suffix in _MAT_EXTS and p.is_file()],
        key=lambda p: p.stat().st_mtime,
    )
    print(f"Found {len(files)} files in {directory}")

    if not args.dry_run:
        corpus_dir.mkdir(parents=True, exist_ok=True)

    before = corpus_stats(corpus_dir)
    added = skipped_error = skipped_no_features = 0

    for i, p in enumerate(files):
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat()
        evt = FileArrivedEvent(
            event_id=str(p),
            run_id="",
            filename=p.name,
            local_path=str(p),
            file_size_bytes=p.stat().st_size,
            mtime=mtime,
            inferred_modality=args.modality,
        )

        # analyze_file handles both metric corpus and plot corpus when add_to_corpus=True.
        # Pass plot_embed flag so it only runs DINOv2 when requested (it's slower).
        ar = analyze_file(
            evt,
            corpus_dir=corpus_dir if not args.dry_run else None,
            corpus_sample=args.sample,
            add_to_corpus=(not args.dry_run),
            add_plot_to_corpus=(not args.dry_run and args.plot_embed),
        )

        has_hard_error = any(
            s in ar.quality_flags for s in
            ("load_failed", "all_nan", "all_zeros", "missing_intensity_array",
             "missing_reflectance_data", "all_nan_after_bg_sub", "zero_dimension")
        )

        if has_hard_error:
            skipped_error += 1
            if args.verbose:
                print(f"  SKIP (error) {p.name}: {', '.join(ar.quality_flags)}")
        elif not ar.metrics:
            skipped_no_features += 1
            if args.verbose:
                print(f"  SKIP (no features) {p.name}")
        else:
            added += 1
            if args.verbose:
                key_metrics = {k: v for k, v in ar.metrics.items()
                               if isinstance(v, (int, float)) and k not in ("file_size_bytes", "variable_count")}
                metric_str = "  ".join(f"{k}={v:.4g}" for k, v in list(key_metrics.items())[:4])
                print(f"  {'(dry)' if args.dry_run else 'ADD '} {p.name[:60]:60s}  {metric_str}")

        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{len(files)} files processed")

    after = corpus_stats(corpus_dir)
    print(f"\nDone.")
    print(f"  Files scanned:      {len(files)}")
    print(f"  Added to corpus:    {added}" + (" (dry run — not written)" if args.dry_run else ""))
    print(f"  Skipped (errors):   {skipped_error}")
    print(f"  Skipped (no feat):  {skipped_no_features}")
    print()
    print("Corpus state:")
    for collection, n in sorted(after.items()):
        prev = before.get(collection, 0)
        delta = n - prev
    for collection, n in sorted(after.items()):
        prev = before.get(collection, 0)
        delta = n - prev
        print(f"  {collection:<22} {n:>5} files  (+{delta})")


if __name__ == "__main__":
    main()
