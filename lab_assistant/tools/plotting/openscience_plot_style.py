"""OpenScience plotting defaults for Xu Lab analysis figures.

This module is intentionally small: it standardizes the first-pass Matplotlib
look, robust color limits, common labels, and heatmap behavior while leaving
project-specific physics choices explicit at call sites.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal


Context = Literal["paper", "deck", "slack"]
MapKind = Literal["sequential", "diverging"]


LABELS = {
    "energy": "Energy (eV)",
    "photon_energy": "Photon energy (eV)",
    "magnetic_field": r"$B$ (T)",
    "density": r"$n$ ($10^{12}$ cm$^{-2}$)",
    "density_cm2": r"$n$ (cm$^{-2}$)",
    "displacement": r"$D$ (V/nm)",
    "filling": r"moire filling $\nu$",
    "rmcd": "RMCD (%)",
    "reflectance_contrast": r"$dR/R$",
    "pl": "PL intensity (a.u.)",
    "integrated_pl": "Integrated PL (a.u.)",
}


def apply_style(context: Context = "paper") -> None:
    """Apply compact Xu Lab-oriented Matplotlib defaults."""
    import matplotlib as mpl

    if context == "paper":
        base = 8.5
        line = 1.1
    elif context == "deck":
        base = 13
        line = 1.5
    else:
        base = 12
        line = 1.4

    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "font.size": base,
            "axes.labelsize": base,
            "axes.titlesize": base + 1,
            "xtick.labelsize": base - 1,
            "ytick.labelsize": base - 1,
            "legend.fontsize": base - 1,
            "axes.linewidth": line,
            "lines.linewidth": line,
            "lines.markersize": 3.5 if context == "paper" else 4.5,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.width": line,
            "ytick.major.width": line,
            "axes.grid": False,
            "axes.facecolor": "white",
            "figure.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def figure_size(kind: Literal["single", "wide", "tall", "grid"] = "single") -> tuple[float, float]:
    """Return practical figure sizes in inches."""
    sizes = {
        "single": (3.1, 2.35),
        "wide": (6.3, 2.6),
        "tall": (3.0, 4.0),
        "grid": (6.4, 5.0),
    }
    return sizes[kind]


def axis_label(key_or_label: str) -> str:
    """Map a common observable key to a rendered axis label."""
    return LABELS.get(key_or_label, key_or_label)


def infer_map_kind(observable: str | None) -> MapKind:
    """Infer whether an observable should use sequential or diverging colors."""
    if not observable:
        return "sequential"
    text = observable.lower()
    signed_terms = ("rmcd", "mcd", "dr/r", "contrast", "difference", "diff", "residual", "slope", "antisym")
    return "diverging" if any(term in text for term in signed_terms) else "sequential"


def default_cmap(observable: str | None = None, kind: MapKind | None = None) -> str:
    """Choose a conservative, publication-appropriate colormap."""
    map_kind = kind or infer_map_kind(observable)
    return "RdBu_r" if map_kind == "diverging" else "viridis"


def robust_limits(
    data,
    *,
    kind: MapKind | None = None,
    observable: str | None = None,
    percentiles: tuple[float, float] = (1.0, 99.0),
    symmetric: bool | None = None,
    floor_zero: bool | None = None,
) -> tuple[float, float]:
    """Return robust color limits, ignoring NaNs and avoiding outlier domination."""
    import numpy as np

    arr = np.asarray(data, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return (0.0, 1.0)

    map_kind = kind or infer_map_kind(observable)
    use_symmetric = (map_kind == "diverging") if symmetric is None else symmetric
    lo, hi = np.nanpercentile(arr, percentiles)

    if use_symmetric:
        bound = float(max(abs(lo), abs(hi)))
        if bound == 0:
            bound = float(np.nanmax(np.abs(arr))) or 1.0
        return (-bound, bound)

    if floor_zero is None:
        floor_zero = bool(observable and any(term in observable.lower() for term in ("pl", "intensity", "counts")))
    if floor_zero:
        lo = max(0.0, float(lo))
    if lo == hi:
        hi = lo + 1.0
    return (float(lo), float(hi))


def style_axes(ax, *, box: bool = False) -> None:
    """Apply standard axis spine/tick treatment."""
    ax.tick_params(direction="out", top=False, right=False)
    if box:
        for spine in ax.spines.values():
            spine.set_visible(True)
    else:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)


def plot_heatmap(
    ax,
    x,
    y,
    z,
    *,
    observable: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    colorbar_label: str | None = None,
    cmap: str | None = None,
    clim: tuple[float, float] | None = None,
    kind: MapKind | None = None,
    rasterized: bool = True,
):
    """Plot a 2D map with lab defaults and an attached colorbar.

    Uses `pcolormesh` because many lab maps are naturally sweep grids. For
    irregular grids, callers should pre-grid carefully or use scatter/triangulation
    rather than implying a rectangular acquisition.
    """
    import matplotlib.pyplot as plt

    map_kind = kind or infer_map_kind(observable)
    limits = clim or robust_limits(z, kind=map_kind, observable=observable)
    mesh = ax.pcolormesh(
        x,
        y,
        z,
        shading="auto",
        cmap=cmap or default_cmap(observable, map_kind),
        vmin=limits[0],
        vmax=limits[1],
        rasterized=rasterized,
    )
    ax.set_xlabel(axis_label(xlabel or ""))
    ax.set_ylabel(axis_label(ylabel or ""))
    style_axes(ax, box=True)
    cbar = plt.colorbar(mesh, ax=ax)
    cbar.set_label(axis_label(colorbar_label or observable or "Signal"))
    return mesh


def plot_hysteresis(ax, field, down, up, *, ylabel: str = "RMCD (%)") -> None:
    """Plot paired up/down magnetic-field sweeps with consistent labels."""
    ax.plot(field, down, color="#d55e00", marker=".", linewidth=1.2, markersize=2.5, label="down sweep")
    ax.plot(field, up, color="#0072b2", marker=".", linewidth=1.2, markersize=2.5, label="up sweep")
    ax.set_xlabel(LABELS["magnetic_field"])
    ax.set_ylabel(axis_label(ylabel))
    style_axes(ax)
    ax.legend(frameon=False)


def save_figure(fig, stem: str | Path, *, formats: Iterable[str] = ("png", "pdf")) -> list[Path]:
    """Save a figure in review and reusable formats."""
    stem_path = Path(stem)
    stem_path.parent.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for fmt in formats:
        path = stem_path.with_suffix(f".{fmt}")
        fig.savefig(path)
        outputs.append(path)
    return outputs
