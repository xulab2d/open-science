from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat


PROJECT_ROOT = Path("/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry")
DATA_DIR = PROJECT_ROOT / "data" / "02PL" / "dot1dispersion"
OUT_DIR = Path.cwd() / "out" / "plots"

ENERGY_MIN = 1.080
ENERGY_MAX = 1.084
FIELD_MIN = 3.6
FIELD_MAX = 6.8


def load_band_rows() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    bg = loadmat(DATA_DIR / "1140c_20s.mat", squeeze_me=True)
    bcg = np.asarray(bg["dat"], dtype=float).reshape(-1)
    wavelength = np.asarray(bg["w"], dtype=float).reshape(-1)
    energy = 1240.0 / wavelength
    energy_mask = (energy >= ENERGY_MIN) & (energy <= ENERGY_MAX)

    dt = 34.0
    db = 27.4
    eps0 = 8.85e-12
    cbg = 3.0 * eps0 / (db * 1e-9)
    ctg = 3.0 * eps0 / (dt * 1e-9)

    files = sorted(DATA_DIR.glob("*allrange_Bset*.mat"))
    if not files:
        raise FileNotFoundError(f"No allrange Bset files found in {DATA_DIR}")

    bvals = []
    n_rows = []
    raw_rows = []

    for path in files:
        m = loadmat(path, squeeze_me=True)
        dat = np.asarray(m["dat"], dtype=float)
        vt = np.asarray(m["Vt"], dtype=float).reshape(-1)
        vb = np.asarray(m["Vb"], dtype=float).reshape(-1)
        current_b = float(np.asarray(m["currentBfield"]).reshape(()))

        if dat.ndim == 3:
            spectra = dat[:, 0, :]
        elif dat.ndim == 2:
            spectra = dat
        else:
            raise ValueError(f"Unexpected dat shape for {path.name}: {dat.shape}")

        spectra = spectra - bcg[:, None]
        spectra = spectra - spectra[989:1000, :].mean(axis=0, keepdims=True)
        raw_band = spectra[energy_mask, :].sum(axis=0)

        nn = ((ctg * vt + cbg * vb) / 1.6e-19 / 1e4) * 1e-12

        bvals.append(current_b)
        n_rows.append(nn)
        raw_rows.append(raw_band)

    bvals = np.asarray(bvals)
    n_rows = np.asarray(n_rows)
    raw_rows = np.asarray(raw_rows)

    order = np.argsort(bvals)
    bvals = bvals[order]
    n_rows = n_rows[order]
    raw_rows = raw_rows[order]

    field_mask = (bvals >= FIELD_MIN) & (bvals <= FIELD_MAX)
    return bvals[field_mask], n_rows[field_mask], raw_rows[field_mask]


def smooth_along_n(raw_rows: np.ndarray, window: int = 9) -> np.ndarray:
    kernel = np.ones(window, dtype=float) / window
    padded = np.pad(raw_rows, ((0, 0), (window // 2, window // 2)), mode="edge")
    return np.apply_along_axis(lambda row: np.convolve(row, kernel, mode="valid"), 1, padded)


def plot_map(
    data: np.ndarray,
    n_axis: np.ndarray,
    bvals: np.ndarray,
    title: str,
    cbar_label: str,
    out_name: str,
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.6), constrained_layout=True)
    im = ax.imshow(
        data,
        origin="lower",
        aspect="auto",
        extent=[n_axis.min(), n_axis.max(), bvals.min(), bvals.max()],
        cmap=cmap,
        interpolation="nearest",
        vmin=vmin,
        vmax=vmax,
    )
    ax.set_xlabel(r"n ($10^{12}$ cm$^{-2}$)")
    ax.set_ylabel("B (T)")
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label(cbar_label)
    png_path = OUT_DIR / f"{out_name}.png"
    pdf_path = OUT_DIR / f"{out_name}.pdf"
    fig.savefig(png_path, dpi=250, facecolor="white")
    fig.savefig(pdf_path, facecolor="white")
    plt.close(fig)
    print(png_path)
    print(pdf_path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bvals, n_rows, raw_rows = load_band_rows()
    n_axis = n_rows[0]

    plot_map(
        data=raw_rows,
        n_axis=n_axis,
        bvals=bvals,
        title=f"Raw band sum, {ENERGY_MIN:.3f}-{ENERGY_MAX:.3f} eV",
        cbar_label="Band-summed PL (a.u.)",
        out_name="a5_dot1_raw_band_sum_B_vs_n",
        cmap="magma",
        vmin=float(np.percentile(raw_rows, 3)),
        vmax=float(np.percentile(raw_rows, 99)),
    )

    smooth_rows = smooth_along_n(raw_rows, window=9)
    row_medians = np.median(smooth_rows, axis=1, keepdims=True)
    normalized = smooth_rows / np.clip(row_medians, 1e-9, None)
    normalized_log = np.log10(np.clip(normalized, 1e-6, None))

    plot_map(
        data=normalized_log,
        n_axis=n_axis,
        bvals=bvals,
        title="Normalized+log (vmax=4), smooth B1",
        cbar_label="log10(I / median(I))",
        out_name="a5_dot1_normalized_log_smooth_B_vs_n",
        cmap="viridis",
        vmin=float(np.percentile(normalized_log, 2)),
        vmax=np.log10(4.0),
    )


if __name__ == "__main__":
    main()
