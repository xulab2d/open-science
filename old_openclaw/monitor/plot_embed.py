"""
Plot-based embeddings using DINOv2 (facebook/dinov2-small).

Renders a standardized diagnostic plot for each file, embeds it with DINOv2's
CLS token (384-dim), and stores it alongside the metric-based corpus.

Design intent
-------------
DINOv2 embeddings catch *structural anomalies* — plots that look visually wrong:
blank spectra, inverted signals, loss of loop structure, dead detector.
They complement the metric corpus (which handles meV-scale peak shifts and
numerical outliers) by capturing cases where the numbers extracted are
unreliable or the file format is unexpected.

Typical cosine similarity ranges on lab data:
  Same modality, similar conditions    0.95 – 0.99
  Same modality, very different regime 0.93 – 0.97
  Different modality entirely          0.60 – 0.70
  Blank / broken vs normal             < 0.80  (good detection threshold)

Storage (state/corpus/):
  {collection}_plot_vectors.npy    — float32 matrix, shape (n_files, 384)
  {collection}_plot_meta.jsonl     — filename, sample, path (parallel with metric meta)

Collections match monitor/corpus.py: PL | RMCD_hysteresis | RMCD_gate_map | Reflectance
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import numpy as np

# DINOv2-small: 22M params, 384-dim CLS token
_MODEL_NAME = "facebook/dinov2-small"
_EMBED_DIM = 384
_DPI = 72         # render quality — 72 dpi at 4×3 in → ~290×220 px → resized to 224×224 by processor
_FIGSIZE = (4, 3)

# Similarity below this → flag as plot_outlier
PLOT_SIM_THRESHOLD = 0.92

# Minimum corpus size before outlier detection fires
_MIN_CORPUS_SIZE = 8

_model = None
_proc = None


def _get_model():
    """Lazy-load DINOv2. First call takes ~0.5s; subsequent calls are instant."""
    global _model, _proc
    if _model is None:
        import warnings
        import torch
        from transformers import AutoImageProcessor, AutoModel
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _proc = AutoImageProcessor.from_pretrained(_MODEL_NAME)
            _model = AutoModel.from_pretrained(_MODEL_NAME)
            _model.eval()
    return _proc, _model


def _render_plot(mat_data: dict[str, Any], modality: str, collection: str) -> "Image | None":
    """
    Render a standardized diagnostic plot for a file.
    Returns a PIL Image, or None if rendering fails.
    Keeps plots minimal and consistent so DINOv2 sees the data, not decoration.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image

        fig, ax = plt.subplots(figsize=_FIGSIZE)
        ax.set_xticks([])
        ax.set_yticks([])

        drawn = False

        if collection == "PL":
            drawn = _draw_pl(ax, mat_data)
        elif collection == "RMCD_hysteresis":
            drawn = _draw_rmcd_hyst(ax, mat_data)
        elif collection == "RMCD_gate_map":
            drawn = _draw_rmcd_gatemap(ax, mat_data, fig)
        elif collection == "Reflectance":
            drawn = _draw_reflectance(ax, mat_data)

        if not drawn:
            plt.close(fig)
            return None

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=_DPI, bbox_inches="tight", pad_inches=0.05)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

    except Exception:
        return None


def _draw_pl(ax, mat_data: dict) -> bool:
    w = mat_data.get("w")
    if w is None:
        return False
    w = np.asarray(w, dtype=float).ravel()
    energy = 1240.0 / w if np.nanmax(w) > 10 else w.copy()
    sort_idx = np.argsort(energy)
    energy = energy[sort_idx]

    nw = len(energy)
    I_raw = None
    for k in ("I", "dat", "spec", "spectra", "data"):
        arr = mat_data.get(k)
        if arr is None:
            continue
        try:
            arr = np.asarray(arr, dtype=float)
            if arr.ndim == 3 and arr.shape[0] == nw:
                I_raw = arr.reshape(nw, -1)[sort_idx, :]
                break
            elif arr.ndim == 3 and arr.shape[2] == nw:
                I_raw = arr.reshape(-1, nw).T[sort_idx, :]
                break
            elif arr.ndim == 2 and arr.shape[0] == nw:
                I_raw = arr[sort_idx, :]
                break
            elif arr.ndim == 1 and arr.shape[0] == nw:
                I_raw = arr[sort_idx, np.newaxis]
                break
        except Exception:
            continue
    if I_raw is None:
        return False

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spec = np.nanmean(I_raw, axis=1)

    mask = (energy >= 1.00) & (energy <= 1.25) & np.isfinite(spec)
    if mask.sum() < 5:
        return False

    ax.plot(energy[mask], spec[mask], lw=1.5, color="#2563eb")
    ax.set_xlim(energy[mask].min(), energy[mask].max())
    return True


def _draw_rmcd_hyst(ax, mat_data: dict) -> bool:
    Bsel = mat_data.get("Bsel") if "Bsel" in mat_data else mat_data.get("field_up")
    up = mat_data.get("RMCD_up")
    if Bsel is None or up is None:
        return False
    Bsel = np.asarray(Bsel, dtype=float).ravel()
    up = np.asarray(up, dtype=float).ravel()
    n = min(len(Bsel), len(up))
    if n < 10:
        return False
    Bsel, up = Bsel[:n], up[:n]
    mask = np.isfinite(up)
    if mask.sum() < 10:
        return False

    ax.plot(Bsel[mask], up[mask], lw=1.2, color="#2563eb")
    down = mat_data.get("RMCD_down")
    if down is not None:
        down = np.asarray(down, dtype=float).ravel()[:n]
        dmask = np.isfinite(down)
        if dmask.sum() > 10:
            ax.plot(Bsel[dmask], down[dmask], lw=1.2, color="#dc2626", ls="--")
    ax.axhline(0, color="k", lw=0.4, ls=":")
    ax.axvline(0, color="k", lw=0.4, ls=":")
    return True


def _draw_rmcd_gatemap(ax, mat_data: dict, fig) -> bool:
    rmcd = mat_data.get("RMCD")
    if rmcd is None:
        return False
    rmcd = np.asarray(rmcd, dtype=float)
    if rmcd.ndim != 2 or rmcd.size < 4:
        return False

    Vt = mat_data.get("Vt")
    Vb = mat_data.get("Vb")
    if Vt is None or Vb is None:
        return False
    Vt = np.asarray(Vt, dtype=float).ravel()
    Vb = np.asarray(Vb, dtype=float).ravel()

    finite = rmcd[np.isfinite(rmcd)]
    if finite.size == 0:
        return False
    vmax = float(np.nanpercentile(np.abs(finite), 98)) or 1.0
    ax.pcolormesh(Vb, Vt, rmcd, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
    return True


def _draw_reflectance(ax, mat_data: dict) -> bool:
    w = mat_data.get("w")
    if w is None:
        return False
    w = np.asarray(w, dtype=float).ravel()
    nw = len(w)
    energy = 1240.0 / w if np.nanmax(w) > 10 else w.copy()
    sort_idx = np.argsort(energy)
    energy_s = energy[sort_idx]

    raw_I = None
    for key in ("I", "dat", "datR"):
        arr = mat_data.get(key)
        if arr is None:
            continue
        try:
            arr = np.asarray(arr, dtype=float)
            if arr.ndim == 3 and arr.shape[0] == nw:
                raw_I = arr.reshape(nw, -1)[sort_idx, :]
                break
            elif arr.ndim == 3 and arr.shape[2] == nw:
                raw_I = arr.reshape(-1, nw).T[sort_idx, :]
                break
            elif arr.ndim == 2 and arr.shape[0] == nw:
                raw_I = arr[sort_idx, :]
                break
            elif arr.ndim == 1 and arr.shape[0] == nw:
                raw_I = arr[sort_idx, np.newaxis]
                break
        except Exception:
            continue

    if raw_I is None or raw_I.shape[1] == 0:
        return False

    # Find valid reference column
    ref = None
    for col_i in range(raw_I.shape[1]):
        col = raw_I[:, col_i]
        if (np.isfinite(col) & (np.abs(col) > 1e-6)).sum() > nw // 2:
            ref = col
            break
    if ref is None or raw_I.shape[1] == 1:
        return False

    valid_ref = np.isfinite(ref) & (np.abs(ref) > 1e-6)
    dRR = np.full_like(raw_I, np.nan)
    for i in range(raw_I.shape[1]):
        dRR[valid_ref, i] = (raw_I[valid_ref, i] - ref[valid_ref]) / ref[valid_ref]

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        drr_mean = np.nanmean(dRR, axis=1)

    mask = (energy_s >= 1.0) & (energy_s <= 1.25) & np.isfinite(drr_mean)
    if mask.sum() < 5:
        return False

    ax.plot(energy_s[mask], drr_mean[mask], lw=1.5, color="#2563eb")
    ax.axhline(0, color="k", lw=0.4, ls=":")
    ax.set_xlim(energy_s[mask].min(), energy_s[mask].max())
    return True


def _embed_image(img: "Image") -> np.ndarray:
    """Run DINOv2 on a PIL image, return unit-normalized 384-dim CLS vector."""
    import torch
    proc, model = _get_model()
    inputs = proc(images=img, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs)
    v = out.last_hidden_state[:, 0, :].squeeze().numpy().astype(np.float32)
    norm = np.linalg.norm(v)
    return v / norm if norm > 1e-12 else v


# ---------------------------------------------------------------------------
# Public API  (mirrors monitor/corpus.py's add_entry / query_similar)
# ---------------------------------------------------------------------------

def _collection_for(modality: str, metrics: dict[str, Any]) -> str | None:
    """Same mapping as corpus.py."""
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


def add_plot_entry(
    mat_data: dict[str, Any],
    metrics: dict[str, Any],
    filename: str,
    sample: str,
    modality: str,
    path: str,
    corpus_dir: Path,
) -> bool:
    """
    Render a plot, embed it with DINOv2, and append to the plot corpus.
    Returns True if added.
    """
    collection = _collection_for(modality, metrics)
    if collection is None:
        return False

    img = _render_plot(mat_data, modality, collection)
    if img is None:
        return False

    vec = _embed_image(img)
    corpus_dir.mkdir(parents=True, exist_ok=True)

    vec_path = corpus_dir / f"{collection}_plot_vectors.npy"
    if vec_path.exists():
        existing = np.load(str(vec_path))
        combined = np.vstack([existing, vec[np.newaxis, :]])
    else:
        combined = vec[np.newaxis, :]
    np.save(str(vec_path), combined.astype(np.float32))

    meta_path = corpus_dir / f"{collection}_plot_meta.jsonl"
    entry = {"filename": filename, "sample": sample, "modality": modality, "path": path}
    with open(meta_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return True


def query_plot_similar(
    mat_data: dict[str, Any],
    metrics: dict[str, Any],
    modality: str,
    corpus_dir: Path,
    n_results: int = 5,
    sample_filter: str | None = None,
) -> dict[str, Any] | None:
    """
    Find visually similar plots in the corpus.

    Returns None if: no matching collection, corpus too small, or rendering fails.

    Return dict:
      collection      — which collection was searched
      n_corpus        — files in corpus
      nearest_sim     — similarity to nearest neighbor
      top_neighbors   — list of {filename, sample, similarity}
      is_plot_outlier — True if nearest_sim < PLOT_SIM_THRESHOLD
    """
    collection = _collection_for(modality, metrics)
    if collection is None:
        return None

    vec_path = corpus_dir / f"{collection}_plot_vectors.npy"
    meta_path = corpus_dir / f"{collection}_plot_meta.jsonl"
    if not (vec_path.exists() and meta_path.exists()):
        return None

    matrix = np.load(str(vec_path))
    n_corpus = matrix.shape[0]
    if n_corpus < _MIN_CORPUS_SIZE:
        return None

    meta_lines = [l for l in meta_path.read_text().split("\n") if l.strip()]
    all_meta = [json.loads(l) for l in meta_lines]

    img = _render_plot(mat_data, modality, collection)
    if img is None:
        return None

    query_vec = _embed_image(img)

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe_matrix = matrix / np.where(norms > 1e-12, norms, 1.0)
    sims = safe_matrix @ query_vec

    if sample_filter:
        for j, m in enumerate(all_meta):
            if m.get("sample", "") != sample_filter:
                sims[j] = -2.0

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
        })

    nearest_sim = float(top_neighbors[0]["similarity"]) if top_neighbors else 0.0

    return {
        "collection": collection,
        "n_corpus": n_corpus,
        "nearest_sim": round(nearest_sim, 4),
        "top_neighbors": top_neighbors,
        "is_plot_outlier": nearest_sim < PLOT_SIM_THRESHOLD,
    }


def format_plot_result(result: dict[str, Any]) -> str:
    """Compact plain-text summary for LLM consumption."""
    if result is None:
        return "Plot corpus: no match or corpus too small."
    lines = [
        f"Plot corpus ({result['collection']}, n={result['n_corpus']}):  "
        f"nearest_sim={result['nearest_sim']:.3f}  "
        f"{'⚠ VISUALLY UNUSUAL' if result['is_plot_outlier'] else 'visually normal'}"
    ]
    for nb in result["top_neighbors"][:3]:
        lines.append(f"  [{nb['similarity']:.3f}] {nb['filename'][:55]}  ({nb['sample']})")
    return "\n".join(lines)


def plot_corpus_stats(corpus_dir: Path) -> dict[str, int]:
    """Return {collection: n_files} for all plot collections that exist."""
    from .corpus import FEATURE_KEYS
    result = {}
    for collection in FEATURE_KEYS:
        meta_path = corpus_dir / f"{collection}_plot_meta.jsonl"
        if meta_path.exists():
            lines = [l for l in meta_path.read_text().split("\n") if l.strip()]
            result[collection] = len(lines)
    return result
