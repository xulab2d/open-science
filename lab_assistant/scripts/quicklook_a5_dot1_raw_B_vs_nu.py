from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat


PROJECT_ROOT = Path("/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry")
DATA_DIR = PROJECT_ROOT / "data" / "02PL" / "dot1dispersion"
OUT_DIR = Path.cwd() / "out" / "plots"

E_MIN = 1.080
E_MAX = 1.084


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    bg = loadmat(DATA_DIR / "1140c_20s.mat", squeeze_me=True)
    bcg = np.asarray(bg["dat"], dtype=float).reshape(-1)
    wavelength = np.asarray(bg["w"], dtype=float).reshape(-1)
    energy = 1240.0 / wavelength
    energy_mask = (energy >= E_MIN) & (energy <= E_MAX)

    dt = 34.0
    db = 27.4
    eps0 = 8.85e-12
    cbg = 3.0 * eps0 / (db * 1e-9)
    ctg = 3.0 * eps0 / (dt * 1e-9)

    v13 = -1.3344
    v23 = -2.34762
    n1 = -(v13 - v23) * 3.0

    files = sorted(DATA_DIR.glob("*Bset*.mat"))
    if not files:
        raise FileNotFoundError(f"No Bset files found in {DATA_DIR}")

    bvals = []
    fill_rows = []
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
        filling = -(nn - v23) / n1 - 2.0 / 3.0

        bvals.append(current_b)
        fill_rows.append(filling)
        raw_rows.append(raw_band)

    bvals = np.asarray(bvals)
    fill_rows = np.asarray(fill_rows)
    raw_rows = np.asarray(raw_rows)

    order = np.argsort(bvals)
    bvals = bvals[order]
    fill_rows = fill_rows[order]
    raw_rows = raw_rows[order]

    filling_axis = fill_rows[0]
    vmin, vmax = np.percentile(raw_rows, [3, 99])

    fig, ax = plt.subplots(figsize=(14, 5), constrained_layout=True)
    im = ax.imshow(
        raw_rows,
        origin="lower",
        aspect="auto",
        extent=[filling_axis.min(), filling_axis.max(), bvals.min(), bvals.max()],
        cmap="magma",
        vmin=vmin,
        vmax=vmax,
    )
    ax.set_xlabel(r"$\nu$")
    ax.set_ylabel("B (T)")
    ax.set_ylim(0, 7)
    ax.set_title(f"A5 dot1 raw band sum, {E_MIN:.3f}-{E_MAX:.3f} eV")
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Band-summed PL (a.u.)")

    png_path = OUT_DIR / "a5_dot1_raw_band_sum_B_vs_nu_python.png"
    pdf_path = OUT_DIR / "a5_dot1_raw_band_sum_B_vs_nu_python.pdf"
    fig.savefig(png_path, dpi=250, facecolor="white")
    fig.savefig(pdf_path, facecolor="white")
    plt.close(fig)

    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
