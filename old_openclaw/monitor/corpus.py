"""
Physics-feature corpus for similarity-based anomaly detection.

Each analyzed file's metrics are stored as a normalized feature vector.
New files are compared against the corpus using cosine similarity.

Two signals flag a file as unusual:
  1. Low nearest-neighbor similarity  (global shape mismatch)
  2. High z-score on a specific feature  (one quantity out of range)

Storage (state/corpus/):
  {collection}_vectors.npy    — float32 matrix, shape (n_files, n_features)
  {collection}_meta.jsonl     — one JSON dict per line: filename, sample, path, raw_metrics
  {collection}_stats.json     — running mean/std per feature (Welford online update)

Collections: PL | RMCD_hysteresis | RMCD_gate_map | Reflectance | misc

misc: background spectra (bg_*), reference/calibration frames (300g_*), and other
files that do not represent primary physics measurements.  Stored for traceability
but excluded from similarity scoring.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Feature schemas: defines what goes into each collection's embedding vector.
# Order matters — must stay stable as the corpus grows.
# ---------------------------------------------------------------------------

FEATURE_KEYS: dict[str, list[str]] = {
    "PL": [
        "peak_energy_eV",
        "peak_snr",
        "integrated_intensity",
        "background_level",
        "nan_gate_fraction",
    ],
    "RMCD_hysteresis": [
        "coercive_field_T",
        "saturation_contrast",
        "saturation_high_B",
        "saturation_low_B",
        "hysteresis_loop_area",
        "B_min_T",
        "B_max_T",
    ],
    "RMCD_gate_map": [
        "rmcd_mean",
        "rmcd_std",
        "rmcd_range",
        "fill_fraction",
        "Vt_min_V",
        "Vt_max_V",
        "Vb_min_V",
        "Vb_max_V",
    ],
    "Reflectance": [
        "resonance_center_eV",
        "dRR_amplitude",
        "resonance_dip_depth",
    ],
}

# Nearest-neighbor similarity below this → flag as corpus_outlier
_SIM_THRESHOLD = 0.85

# Z-score above this → flag the specific feature as anomalous
_Z_THRESHOLD = 3.0

# Minimum corpus size before outlier detection fires
# (too few entries → noisy stats)
_MIN_CORPUS_SIZE = 8


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _collection_for(modality: str, metrics: dict[str, Any]) -> str | None:
    """Map modality + metrics to a collection name."""
    if modality == "PL" and "peak_energy_eV" in metrics:
        return "PL"
    if modality == "Reflectance" and "resonance_center_eV" in metrics:
        return "Reflectance"
    if modality == "RMCD":
        t = metrics.get("rmcd_type", "")
        if t == "hysteresis_loop":
            return "RMCD_hysteresis"
        if t == "gate_map":
            return "RMCD_gate_map"
    return None


def _extract_raw(metrics: dict, collection: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract feature vector from metrics.

    Returns:
      raw    : float array, NaN where a feature is missing
      valid  : bool array, True where a feature was present
    """
    keys = FEATURE_KEYS[collection]
    raw = np.array([float(metrics.get(k, math.nan)) for k in keys], dtype=np.float64)
    valid = np.isfinite(raw)
    return raw, valid


def _normalize(raw: np.ndarray, valid: np.ndarray, stats: dict) -> np.ndarray:
    """
    Z-score normalize a raw feature vector using corpus stats.
    Missing features (valid=False) → 0 (corpus mean after normalization).
    Returns a float32 unit vector (for cosine similarity).
    """
    n_feat = len(raw)
    vec = np.zeros(n_feat, dtype=np.float64)
    for i, (v, ok) in enumerate(zip(raw, valid)):
        if ok:
            mean = stats.get("mean", [0.0] * n_feat)[i]
            std = stats.get("std", [1.0] * n_feat)[i]
            vec[i] = (v - mean) / (std if std > 1e-12 else 1.0)
    # Unit-normalize for cosine similarity
    norm = np.linalg.norm(vec)
    if norm > 1e-12:
        vec = vec / norm
    return vec.astype(np.float32)


def _cosine_similarities(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    Cosine similarity between a unit query vector and each row of matrix.
    Both query and rows should already be unit-normalized.
    """
    # matrix rows may not be perfectly unit; re-normalize
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe_matrix = matrix / np.where(norms > 1e-12, norms, 1.0)
    return safe_matrix @ query_vec  # shape (n,)


def _welford_update(stats: dict, raw: np.ndarray, valid: np.ndarray, n_feat: int) -> None:
    """
    Online Welford update of mean/variance stats.

    stats dict is mutated in place. Keys: count, mean (list), M2 (list), std (list).
    """
    if "count" not in stats:
        stats["count"] = 0
        stats["mean"] = [0.0] * n_feat
        stats["M2"] = [0.0] * n_feat
        stats["std"] = [1.0] * n_feat

    stats["count"] += 1
    n = stats["count"]
    for i, (v, ok) in enumerate(zip(raw, valid)):
        if ok:
            delta = v - stats["mean"][i]
            stats["mean"][i] += delta / n
            delta2 = v - stats["mean"][i]
            stats["M2"][i] += delta * delta2
            variance = stats["M2"][i] / n if n > 1 else 1.0
            stats["std"][i] = math.sqrt(max(variance, 1e-24))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_MISC_FILENAME_PREFIXES = ("bg_", "300g_")
_MISC_FILENAME_EXACT   = {"1120.mat"}


def _is_misc_file(filename: str) -> bool:
    """Return True for background/calibration frames that should go in misc."""
    return (any(filename.startswith(p) for p in _MISC_FILENAME_PREFIXES)
            or filename in _MISC_FILENAME_EXACT)


def add_entry(
    metrics: dict[str, Any],
    filename: str,
    sample: str,
    modality: str,
    path: str,
    corpus_dir: Path,
) -> bool:
    """
    Add one file's metrics to the corpus.

    Files matching the misc pattern are stored in the misc collection and
    excluded from physics-feature scoring.

    Returns True if added, False if the modality/metrics don't fit any collection.
    """
    if _is_misc_file(filename):
        corpus_dir.mkdir(parents=True, exist_ok=True)
        meta_path = corpus_dir / "misc_meta.jsonl"
        entry = {"filename": filename, "sample": sample,
                 "modality": modality, "path": path,
                 "raw_metrics": metrics}
        with open(meta_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return True

    collection = _collection_for(modality, metrics)
    if collection is None:
        return False

    corpus_dir.mkdir(parents=True, exist_ok=True)
    raw, valid = _extract_raw(metrics, collection)

    if not valid.any():
        return False  # no usable features

    n_feat = len(FEATURE_KEYS[collection])

    # ---- Update stats ----
    stats_path = corpus_dir / f"{collection}_stats.json"
    stats = json.loads(stats_path.read_text()) if stats_path.exists() else {}
    _welford_update(stats, raw, valid, n_feat)
    stats_path.write_text(json.dumps(stats))

    # ---- Append normalized vector ----
    vec = _normalize(raw, valid, stats)
    vec_path = corpus_dir / f"{collection}_vectors.npy"
    if vec_path.exists():
        existing = np.load(str(vec_path))
        combined = np.vstack([existing, vec[np.newaxis, :]])
    else:
        combined = vec[np.newaxis, :]
    np.save(str(vec_path), combined.astype(np.float32))

    # ---- Append metadata ----
    meta_path = corpus_dir / f"{collection}_meta.jsonl"
    entry = {
        "filename": filename,
        "sample": sample,
        "modality": modality,
        "path": path,
        "raw_metrics": {k: v for k, v in metrics.items()
                        if k in FEATURE_KEYS[collection] and v is not None},
    }
    with open(meta_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return True


def query_similar(
    metrics: dict[str, Any],
    modality: str,
    corpus_dir: Path,
    n_results: int = 5,
    sample_filter: str | None = None,
) -> dict[str, Any] | None:
    """
    Find nearest neighbors in the corpus for a new file's metrics.

    Returns None if: no matching collection, corpus too small, or no features extracted.

    Return dict:
      collection        — which feature schema was used
      n_corpus          — how many files in this collection
      nearest_sim       — cosine similarity to nearest neighbor (1.0 = identical)
      top_neighbors     — list of dicts: filename, sample, sim, key_metrics
      z_scores          — {feature_name: z_score} for all features present in query
      outlier_features  — features with |z| > Z_THRESHOLD
      is_outlier        — True if nearest_sim < SIM_THRESHOLD or any outlier_features
    """
    collection = _collection_for(modality, metrics)
    if collection is None:
        return None

    vec_path = corpus_dir / f"{collection}_vectors.npy"
    meta_path = corpus_dir / f"{collection}_meta.jsonl"
    stats_path = corpus_dir / f"{collection}_stats.json"

    if not (vec_path.exists() and meta_path.exists() and stats_path.exists()):
        return None

    matrix = np.load(str(vec_path))  # (n, d)
    n_corpus = matrix.shape[0]
    if n_corpus < _MIN_CORPUS_SIZE:
        return None

    meta_lines = meta_path.read_text().strip().split("\n")
    all_meta = [json.loads(line) for line in meta_lines if line.strip()]
    stats = json.loads(stats_path.read_text())

    raw, valid = _extract_raw(metrics, collection)
    if not valid.any():
        return None

    # Z-scores against corpus means/stds
    z_scores: dict[str, float] = {}
    outlier_features: list[str] = []
    for i, (key, v, ok) in enumerate(zip(FEATURE_KEYS[collection], raw, valid)):
        if ok and stats.get("count", 0) > 1:
            mean = stats["mean"][i]
            std = stats["std"][i]
            if std > 1e-12:
                z = (v - mean) / std
                z_scores[key] = round(float(z), 2)
                if abs(z) > _Z_THRESHOLD:
                    outlier_features.append(key)

    # Similarity search
    query_vec = _normalize(raw, valid, stats)
    sims = _cosine_similarities(query_vec, matrix)

    # Optional sample filter
    if sample_filter:
        for j, m in enumerate(all_meta):
            if m.get("sample", "") != sample_filter:
                sims[j] = -2.0  # exclude

    top_k_idx = np.argsort(sims)[::-1][:n_results]
    top_neighbors = []
    for idx in top_k_idx:
        if idx >= len(all_meta) or sims[idx] < -1.5:
            continue
        m = all_meta[idx]
        top_neighbors.append({
            "filename": m["filename"],
            "sample": m.get("sample", ""),
            "similarity": round(float(sims[idx]), 4),
            "key_metrics": m.get("raw_metrics", {}),
        })

    nearest_sim = float(top_neighbors[0]["similarity"]) if top_neighbors else 0.0
    is_outlier = nearest_sim < _SIM_THRESHOLD or bool(outlier_features)

    return {
        "collection": collection,
        "n_corpus": n_corpus,
        "nearest_sim": round(nearest_sim, 4),
        "top_neighbors": top_neighbors,
        "z_scores": z_scores,
        "outlier_features": outlier_features,
        "is_outlier": is_outlier,
    }


def corpus_stats(corpus_dir: Path) -> dict[str, int]:
    """Return {collection_name: n_files} for all collections that exist."""
    result = {}
    for collection in list(FEATURE_KEYS.keys()) + ["misc"]:
        meta_path = corpus_dir / f"{collection}_meta.jsonl"
        if meta_path.exists():
            lines = [l for l in meta_path.read_text().split("\n") if l.strip()]
            result[collection] = len(lines)
    return result


def format_corpus_result(result: dict[str, Any]) -> str:
    """
    Format a query_similar result as compact plain text for LLM consumption.
    Fits in ~15 lines.
    """
    if result is None:
        return "Corpus: no matching collection or corpus too small."

    lines = [
        f"Corpus ({result['collection']}, n={result['n_corpus']}):  "
        f"nearest_sim={result['nearest_sim']:.3f}  "
        f"{'⚠ OUTLIER' if result['is_outlier'] else 'within normal range'}"
    ]

    if result["outlier_features"]:
        for feat in result["outlier_features"]:
            z = result["z_scores"].get(feat, "?")
            lines.append(f"  ! {feat}: z={z:+.1f}σ")

    if result["top_neighbors"]:
        lines.append("  Nearest neighbors:")
        for nb in result["top_neighbors"][:3]:
            key_str = "  ".join(
                f"{k}={v:.4g}" for k, v in list(nb["key_metrics"].items())[:3]
            )
            lines.append(f"    [{nb['similarity']:.3f}] {nb['filename'][:50]}  ({nb['sample']})  {key_str}")

    return "\n".join(lines)
