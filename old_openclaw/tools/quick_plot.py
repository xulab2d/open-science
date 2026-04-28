#!/usr/bin/env python3
"""
quick_plot.py — Generate a diagnostic plot from any .mat data file.

Auto-detects the data type and produces the appropriate figure:
  PL file           → mean spectrum (peak highlighted) + gate-integrated heatmap (if dualgate)
  RMCD hysteresis   → RMCD_up / RMCD_down vs B-field
  RMCD gate map     → 2D heatmap (Vt × Vb)
  Reflectance       → mean dR/R spectrum with resonance marker

Output is saved to out/plots/<stem>_<type>.png and the path is printed to stdout.
The LLM can pass this path to the Slack `message` tool (filePath argument).

Usage:
  python3 tools/quick_plot.py <path_to_mat_file> [--out <output_path>] [--modality RMCD]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
sys.path.insert(0, str(_WORKSPACE))

from monitor.analyze.loader import load_mat  # noqa: E402


def _infer_modality(mat_data: dict, filename: str, hint: str | None) -> str:
    if hint and hint != "unknown":
        return hint
    name_lower = filename.lower()
    if "rmcd" in name_lower or "hyster" in name_lower or "RMCD" in mat_data:
        return "RMCD"
    if "refl" in name_lower or "whitelight" in name_lower or "datR" in mat_data:
        return "Reflectance"
    if any(k in mat_data for k in ("I", "dat", "spec", "spectra")):
        if "w" in mat_data:
            return "PL"
    return "unknown"


def plot_pl(mat_data: dict, out_path: Path) -> str:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from monitor.analyze.pl import analyze_pl

    w = np.asarray(mat_data.get("w", []), dtype=float).ravel()
    if len(w) == 0:
        return "no_wavelength_axis"
    energy = 1240.0 / w if np.nanmax(w) > 10 else w.copy()
    sort_idx = np.argsort(energy)
    energy = energy[sort_idx]

    # Find intensity array
    I_raw = None
    for k in ("I", "dat", "spec", "spectra", "data"):
        if k in mat_data:
            try:
                arr = np.asarray(mat_data[k], dtype=float)
                if arr.size > len(energy):
                    I_raw = arr
                    break
            except Exception:
                continue
    if I_raw is None:
        return "no_intensity_array"

    nw = len(energy)
    # Collapse to (nw, n_gate)
    if I_raw.ndim == 3 and I_raw.shape[0] == nw and I_raw.shape[1] == 2:
        I_2d = 0.5 * (I_raw[:, 0, :] + I_raw[:, 1, :])
    elif I_raw.ndim == 3 and I_raw.shape[0] == nw:
        I_2d = I_raw.reshape(nw, -1)
    elif I_raw.ndim == 3 and I_raw.shape[2] == nw:
        I_2d = I_raw.reshape(-1, nw).T
    elif I_raw.ndim == 2 and I_raw.shape[0] == nw:
        I_2d = I_raw
    elif I_raw.ndim == 2 and I_raw.shape[1] == nw:
        I_2d = I_raw.T
    else:
        I_2d = I_raw[:nw, np.newaxis] if I_raw.ndim == 1 else None

    if I_2d is None:
        return "unexpected_shape"

    I_2d = I_2d[sort_idx, :]
    spec_mean = np.nanmean(I_2d, axis=1)

    has_dualgate = I_2d.shape[1] > 1
    Vt = mat_data.get("Vt")
    Vb = mat_data.get("Vb")
    has_gate_axes = Vt is not None and Vb is not None

    ncols = 2 if (has_dualgate and has_gate_axes and I_raw.ndim == 3
                  and I_raw.shape[0] == nw and I_raw.shape[1] != 2) else 1
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4), dpi=150)
    if ncols == 1:
        axes = [axes]

    # Panel 1: mean spectrum
    ax = axes[0]
    mask = (energy >= 1.00) & (energy <= 1.25)
    e_plot = energy[mask]
    s_plot = spec_mean[mask]
    ax.plot(e_plot, s_plot, lw=1.2, color="#2563eb")
    finite = s_plot[np.isfinite(s_plot)]
    if finite.size > 0:
        peak_i = np.nanargmax(s_plot)
        ax.axvline(e_plot[peak_i], color="#dc2626", lw=0.8, ls="--",
                   label=f"peak {e_plot[peak_i]:.3f} eV")
        ax.legend(fontsize=7)
    ax.set_xlabel("Energy (eV)", fontsize=8)
    ax.set_ylabel("Intensity (cts)", fontsize=8)
    ax.set_title("Mean PL spectrum", fontsize=9)
    ax.tick_params(labelsize=7)

    # Panel 2: integrated intensity map (if dualgate)
    if ncols == 2:
        ax2 = axes[1]
        Vt_arr = np.asarray(Vt, dtype=float).ravel()
        Vb_arr = np.asarray(Vb, dtype=float).ravel()
        # Integrate in 1.04–1.13 eV window
        win = (energy >= 1.04) & (energy <= 1.13)
        nVt, nVb = len(Vt_arr), len(Vb_arr)
        I_gate = I_raw[win, :, :] if I_raw.ndim == 3 else I_2d[win, :]
        integ = np.nansum(I_gate.reshape(np.sum(win), nVt * nVb), axis=0).reshape(nVt, nVb)
        im = ax2.pcolormesh(Vb_arr, Vt_arr, integ, cmap="magma", shading="auto")
        plt.colorbar(im, ax=ax2, label="Integrated PL (cts)", pad=0.02)
        ax2.set_xlabel("$V_b$ (V)", fontsize=8)
        ax2.set_ylabel("$V_t$ (V)", fontsize=8)
        ax2.set_title("Integrated PL (1.04–1.13 eV)", fontsize=9)
        ax2.tick_params(labelsize=7)

    plt.tight_layout(pad=0.8)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return "ok"


def plot_rmcd(mat_data: dict, out_path: Path) -> str:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Hysteresis loop
    has_bsel = ("Bsel" in mat_data and np.asarray(mat_data["Bsel"], dtype=float).size > 5) or \
               ("field_up" in mat_data and np.asarray(mat_data["field_up"], dtype=float).size > 5)
    has_up = "RMCD_up" in mat_data or "RMCD_down" in mat_data

    if has_bsel and has_up:
        Bsel = np.asarray(mat_data.get("Bsel", mat_data.get("field_up")), dtype=float).ravel()
        up = np.asarray(mat_data.get("RMCD_up", np.full_like(Bsel, np.nan)), dtype=float).ravel()
        down = np.asarray(mat_data.get("RMCD_down", np.full_like(Bsel, np.nan)), dtype=float).ravel()
        n = min(len(Bsel), len(up), len(down))
        Bsel, up, down = Bsel[:n], up[:n], down[:n]

        fig, ax = plt.subplots(figsize=(5, 4), dpi=150)
        ax.plot(Bsel, up * 1e3, lw=1.2, color="#2563eb", label="RMCD up")
        if np.any(np.isfinite(down)):
            ax.plot(Bsel, down * 1e3, lw=1.2, color="#dc2626", ls="--", label="RMCD down")
        ax.axhline(0, color="k", lw=0.5, ls=":")
        ax.axvline(0, color="k", lw=0.5, ls=":")
        ax.set_xlabel("B (T)", fontsize=8)
        ax.set_ylabel("RMCD (×10⁻³)", fontsize=8)
        ax.set_title("RMCD hysteresis loop", fontsize=9)
        ax.legend(fontsize=7)
        ax.tick_params(labelsize=7)

        # Annotate gate conditions
        annots = []
        for k in ("Vtset", "Vbset"):
            v = mat_data.get(k)
            if v is not None:
                try:
                    annots.append(f"{k}={float(v):.2f}V")
                except Exception:
                    pass
        if annots:
            ax.set_title(f"RMCD hysteresis — {', '.join(annots)}", fontsize=9)

        plt.tight_layout(pad=0.8)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
        return "ok"

    # Gate map
    if "RMCD" in mat_data and "Vt" in mat_data and "Vb" in mat_data:
        rmcd = np.asarray(mat_data["RMCD"], dtype=float)
        Vt = np.asarray(mat_data["Vt"], dtype=float).ravel()
        Vb = np.asarray(mat_data["Vb"], dtype=float).ravel()
        if rmcd.ndim == 2:
            vmax = np.nanpercentile(np.abs(rmcd[np.isfinite(rmcd)]), 98) if np.any(np.isfinite(rmcd)) else 1
            fig, ax = plt.subplots(figsize=(5, 4), dpi=150)
            im = ax.pcolormesh(Vb, Vt, rmcd, cmap="RdBu_r",
                               vmin=-vmax, vmax=vmax, shading="auto")
            plt.colorbar(im, ax=ax, label="RMCD", pad=0.02)
            ax.set_xlabel("$V_b$ (V)", fontsize=8)
            ax.set_ylabel("$V_t$ (V)", fontsize=8)
            ax.set_title("RMCD gate map", fontsize=9)
            ax.tick_params(labelsize=7)
            plt.tight_layout(pad=0.8)
            plt.savefig(out_path, dpi=150, bbox_inches="tight")
            plt.close()
            return "ok"

    return "unrecognized_rmcd_format"


def plot_reflectance(mat_data: dict, out_path: Path) -> str:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from monitor.analyze.reflectance import analyze_reflectance

    w = mat_data.get("w")
    if w is None:
        return "no_wavelength_axis"
    w = np.asarray(w, dtype=float).ravel()
    nw = len(w)
    energy = 1240.0 / w if np.nanmax(w) > 10 else w.copy()
    sort_idx = np.argsort(energy)
    energy_s = energy[sort_idx]

    # Find intensity array (I before dat)
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
        return "no_data_found"

    # Find first valid reference column
    ref = None
    for col_i in range(raw_I.shape[1]):
        col = raw_I[:, col_i]
        if (np.isfinite(col) & (np.abs(col) > 1e-6)).sum() > nw // 2:
            ref = col
            break
    if ref is None:
        return "no_valid_reference"

    if raw_I.shape[1] == 1:
        # Just plot the reference spectrum
        fig, ax = plt.subplots(figsize=(5, 4), dpi=150)
        mask = (energy_s >= 1.0) & (energy_s <= 1.3)
        ax.plot(energy_s[mask], raw_I[mask, 0], lw=1.2, color="#2563eb")
        ax.set_xlabel("Energy (eV)", fontsize=8)
        ax.set_ylabel("Intensity (cts)", fontsize=8)
        ax.set_title("Reference spectrum", fontsize=9)
        ax.tick_params(labelsize=7)
        plt.tight_layout(pad=0.8)
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        plt.close()
        return "ok"

    valid_ref = np.isfinite(ref) & (np.abs(ref) > 1e-6)
    dRR = np.full_like(raw_I, np.nan)
    for i in range(raw_I.shape[1]):
        dRR[valid_ref, i] = (raw_I[valid_ref, i] - ref[valid_ref]) / ref[valid_ref]

    drr_mean = np.nanmean(dRR, axis=1)

    # Get resonance from analyze_reflectance for annotation
    metrics = analyze_reflectance(mat_data, "")
    xc = metrics.get("resonance_center_eV")

    fig, axes = plt.subplots(1, 2, figsize=(9, 4), dpi=150)

    # Left: mean dR/R
    ax = axes[0]
    mask = (energy_s >= 1.0) & (energy_s <= 1.25)
    ax.plot(energy_s[mask], drr_mean[mask], lw=1.2, color="#2563eb")
    if xc:
        ax.axvline(xc, color="#dc2626", lw=0.8, ls="--", label=f"res. {xc:.3f} eV")
        ax.legend(fontsize=7)
    ax.axhline(0, color="k", lw=0.5, ls=":")
    ax.set_xlabel("Energy (eV)", fontsize=8)
    ax.set_ylabel("mean dR/R", fontsize=8)
    ax.set_title("Mean reflectance contrast", fontsize=9)
    ax.tick_params(labelsize=7)

    # Right: gate-resolved dR/R heatmap (truncate at 500 gate points for speed)
    ax2 = axes[1]
    n_gate_plot = min(raw_I.shape[1], 500)
    dRR_plot = dRR[mask, :n_gate_plot]
    vmax = np.nanpercentile(np.abs(dRR_plot[np.isfinite(dRR_plot)]), 99) if np.any(np.isfinite(dRR_plot)) else 0.1
    im = ax2.pcolormesh(np.arange(n_gate_plot), energy_s[mask],
                        dRR_plot, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
    plt.colorbar(im, ax=ax2, label="dR/R", pad=0.02)
    if xc:
        ax2.axhline(xc, color="#dc2626", lw=0.8, ls="--")
    ax2.set_xlabel("Gate index", fontsize=8)
    ax2.set_ylabel("Energy (eV)", fontsize=8)
    ax2.set_title("dR/R gate sweep", fontsize=9)
    ax2.tick_params(labelsize=7)

    plt.tight_layout(pad=0.8)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return "ok"


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot a .mat data file.")
    ap.add_argument("filepath", help="Path to .mat file")
    ap.add_argument("--out", default=None, help="Output image path (default: out/plots/<stem>_plot.png)")
    ap.add_argument("--modality", default=None, choices=["PL", "RMCD", "Reflectance", None],
                    help="Force modality (default: auto-detect)")
    args = ap.parse_args()

    path = Path(args.filepath).resolve()
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    mat_data, load_error = load_mat(path)
    if mat_data is None:
        print(f"ERROR: could not load file: {load_error}", file=sys.stderr)
        sys.exit(1)

    modality = _infer_modality(mat_data, path.name, args.modality)

    if args.out:
        out_path = Path(args.out).resolve()
    else:
        out_dir = (_WORKSPACE / "out" / "plots")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{path.stem}_{modality.lower()}_plot.png"

    if modality == "PL":
        status = plot_pl(mat_data, out_path)
    elif modality == "RMCD":
        status = plot_rmcd(mat_data, out_path)
    elif modality == "Reflectance":
        status = plot_reflectance(mat_data, out_path)
    else:
        print(f"ERROR: could not auto-detect modality for {path.name}. Use --modality.", file=sys.stderr)
        sys.exit(1)

    if status != "ok":
        print(f"ERROR: plot failed ({status})", file=sys.stderr)
        sys.exit(1)

    print(out_path)


if __name__ == "__main__":
    main()
