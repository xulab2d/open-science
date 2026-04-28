"""
Reflectance / dR/R file analyzer.

Follows the lab's standard analysis pipeline (from WJL/Courtney scripts):
  1. cmerge: merge left/right circular polarization channels
  2. dR/R normalization: (I_signal - I_ref) / I_ref, using first gate point as reference
  3. Smooth differentiation: d(dR/R)/dE using smooth_diff filter (low-pass differentiator)
  4. Parabolic minimum fitting: extract resonance center energy and dip depth with sub-pixel accuracy

Expected .mat variables:
  dat     — raw spectra, shape (n_wl, n_pol, n_gate)  [primary; WJL-style]
  datR    — right-channel spectra (n_wl × n_gate)    [alternative naming]
  datL    — left-channel spectra  (n_wl × n_gate)
  w       — wavelength axis in nm
  Vt, Vb  — gate voltages
  TG, BG  — BN thicknesses in nm (for n/D calibration, if present)
"""

from __future__ import annotations

import numpy as np
from typing import Any

# Energy window of interest for tMoTe2 (eV) — exciton/trion resonance
_E_LO = 1.080
_E_HI = 1.146

# smooth_diff filter length (matches lab scripts: n=20)
_SMOOTH_DIFF_N = 20

# cmerge threshold
_CMERGE_THRESH = 60.0


def analyze_reflectance(mat_data: dict[str, Any], filename: str) -> dict[str, Any]:
    """Extract reflectance quality metrics. Returns a flat dict."""
    metrics: dict[str, Any] = {}
    flags: list[str] = []

    try:
        # --- Wavelength axis ---
        w = _get_arr(mat_data, ["w", "wavelength", "wl"])
        if w is None:
            flags.append("missing_wavelength_axis")
            metrics["refl_flags"] = flags
            return metrics
        w = w.ravel()
        nw = len(w)

        if np.nanmax(w) > 10:
            energy = 1240.0 / w
            metrics["wavelength_unit"] = "nm"
        else:
            energy = w.copy()
            metrics["wavelength_unit"] = "eV"

        # Sort by increasing energy (scripts sometimes have decreasing wavelength axis)
        sort_idx = np.argsort(energy)
        energy_sorted = energy[sort_idx]

        # --- Load raw intensity ---
        # Try WJL-style (dat with pol axis) first, then datR/datL convention
        raw_I = _load_raw(mat_data, nw, sort_idx)
        if raw_I is None:
            flags.append("missing_reflectance_data")
            metrics["refl_flags"] = flags
            return metrics

        # raw_I shape: (nw, n_gate) — single merged channel

        if raw_I.shape[1] == 0:
            flags.append("zero_gate_points")
            metrics["refl_flags"] = flags
            return metrics

        # Single-spectrum files (reference/background calibration files):
        # dR/R is trivially zero — just record absolute spectrum metrics and return.
        if raw_I.shape[1] == 1:
            metrics["refl_type"] = "reference_spectrum"
            spec = raw_I[:, 0]
            finite = spec[np.isfinite(spec)]
            if finite.size > 0:
                metrics["ref_spectrum_max"] = round(float(np.max(finite)), 1)
                metrics["ref_spectrum_mean"] = round(float(np.mean(finite)), 1)
            metrics["refl_flags"] = flags
            return metrics

        # --- dR/R normalization using first finite gate point as reference ---
        # Find first column where at least half the pixels are finite and nonzero
        ref_spectrum = None
        for col_i in range(raw_I.shape[1]):
            col = raw_I[:, col_i]
            finite_nonzero = np.isfinite(col) & (np.abs(col) > 1e-6)
            if finite_nonzero.sum() > nw // 2:
                ref_spectrum = col
                break
        if ref_spectrum is None:
            flags.append("all_nan_after_normalization")
            metrics["refl_flags"] = flags
            return metrics

        dRR = np.full_like(raw_I, np.nan)
        valid_ref = np.isfinite(ref_spectrum) & (np.abs(ref_spectrum) > 1e-6)
        for i in range(raw_I.shape[1]):
            dRR[valid_ref, i] = (raw_I[valid_ref, i] - ref_spectrum[valid_ref]) / ref_spectrum[valid_ref]

        if np.all(~np.isfinite(dRR)):
            flags.append("all_nan_after_normalization")
            metrics["refl_flags"] = flags
            return metrics

        if np.nanmean(np.abs(dRR)) < 1e-9:
            flags.append("near_zero_dRR")

        # Mean dR/R spectrum over gate points
        drr_mean = np.nanmean(dRR, axis=1)
        metrics["dRR_amplitude"] = round(float(np.nanmax(np.abs(drr_mean))), 5)

        # --- Smooth derivative: d(dR/R)/dE ---
        dE = float(np.nanmean(np.diff(energy_sorted)))
        if abs(dE) < 1e-9:
            flags.append("degenerate_energy_axis")
            metrics["refl_flags"] = flags
            return metrics

        # Apply to each gate spectrum, then take mean
        h = _smooth_diff_kernel(_SMOOTH_DIFF_N)
        drr_sorted = drr_mean[sort_idx]

        from numpy import convolve
        smoothdiff = np.convolve(-h, drr_sorted, mode="same") / dE

        # Mask edge artefacts from convolution
        edge = len(h) // 2 + 1
        smoothdiff[:edge] = np.nan
        smoothdiff[-edge:] = np.nan

        # --- Find resonance dip in energy window ---
        e_lo_px = np.searchsorted(energy_sorted, _E_LO)
        e_hi_px = np.searchsorted(energy_sorted, _E_HI)
        if e_hi_px <= e_lo_px + 3:
            e_lo_px, e_hi_px = 0, len(energy_sorted) - 1

        window_diff = smoothdiff[e_lo_px:e_hi_px].copy()
        finite_mask = np.isfinite(window_diff)

        if finite_mask.sum() < 5:
            flags.append("insufficient_data_in_energy_window")
        else:
            # Find most negative dip (absorption resonance)
            dip_idx_local = np.nanargmin(window_diff)
            dip_idx_global = e_lo_px + dip_idx_local

            metrics["resonance_dip_depth"] = round(float(smoothdiff[dip_idx_global]), 3)

            # Parabolic sub-pixel fitting for resonance center
            if 1 <= dip_idx_global <= len(energy_sorted) - 2:
                x3 = energy_sorted[dip_idx_global - 1: dip_idx_global + 2]
                y3 = smoothdiff[dip_idx_global - 1: dip_idx_global + 2]
                if np.all(np.isfinite(y3)):
                    xc, yc = _subpixel_parabolic_min(x3, y3)
                    if _E_LO - 0.02 < xc < _E_HI + 0.02:
                        metrics["resonance_center_eV"] = round(xc, 4)
                        metrics["resonance_dip_fitted"] = round(yc, 3)
                    else:
                        metrics["resonance_center_eV"] = round(float(energy_sorted[dip_idx_global]), 4)
                else:
                    metrics["resonance_center_eV"] = round(float(energy_sorted[dip_idx_global]), 4)
            else:
                metrics["resonance_center_eV"] = round(float(energy_sorted[dip_idx_global]), 4)

            # Flag if resonance is very weak
            if abs(metrics["resonance_dip_depth"]) < 1.0:
                flags.append("weak_resonance_feature")

        # --- Gate coverage ---
        for gk, gl in [("Vt", "top_gate"), ("Vb", "bottom_gate")]:
            vg = _get_arr(mat_data, [gk])
            if vg is not None:
                vg = vg.ravel()
                if vg.size > 1:
                    metrics[f"{gl}_min_V"] = round(float(np.nanmin(vg)), 3)
                    metrics[f"{gl}_max_V"] = round(float(np.nanmax(vg)), 3)
                    metrics[f"{gl}_npoints"] = int(vg.size)

        metrics["gate_points_total"] = int(raw_I.shape[1])

        # Integration time
        t = mat_data.get("exptime") or mat_data.get("spectime")
        if t is not None:
            try:
                metrics["integration_time_s"] = float(t)
            except (TypeError, ValueError):
                pass

    except Exception as e:
        flags.append(f"analysis_error:{str(e)[:80]}")

    metrics["refl_flags"] = flags
    return metrics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_raw(mat_data: dict, nw: int, sort_idx: "np.ndarray") -> "np.ndarray | None":
    """
    Load and merge raw intensity data into shape (nw, n_gate).

    Handles multiple naming/shape conventions:
      dat  (nw, 2, n_gate)    — WJL-style with polarization axis
      dat  (nw, n_gate)       — already merged
      dat  (nX, nY, nw)       — wavelength-last spatial map
      I    (nw, nVt, nVb)     — gate sweep (Zengde / B79 convention)
      I    (nw, n_gate)       — 2D gate sweep
      datR/datL               — per-channel convention
    """
    # I convention: (nw, nVt, nVb) or (nw, n_gate) — common in Zengde/B79 dualgate files
    # Check BEFORE dat so that files with both dat (1D reference) and I (gate sweep) use I
    I_arr = mat_data.get("I")
    if I_arr is not None:
        try:
            I_arr = np.asarray(I_arr, dtype=float)
            if I_arr.ndim == 3 and I_arr.shape[0] == nw:
                # (nw, nVt, nVb) — flatten gate dims
                return I_arr.reshape(nw, -1)[sort_idx, :]
            elif I_arr.ndim == 2 and I_arr.shape[0] == nw:
                return I_arr[sort_idx, :]
            elif I_arr.ndim == 3 and I_arr.shape[2] == nw:
                # (nX, nY, nw) wavelength-last
                return I_arr.reshape(-1, nw).T[sort_idx, :]
        except Exception:
            pass

    # WJL-style: dat with various shapes
    dat = mat_data.get("dat")
    if dat is not None:
        try:
            dat = np.asarray(dat, dtype=float)
            if dat.ndim == 3 and dat.shape[0] == nw and dat.shape[1] == 2:
                # (nw, 2, n_gate) polarization axis — cmerge
                ch1 = dat[:, 0, :]
                ch2 = dat[:, 1, :]
                merged = _cmerge(ch1, ch2)
                return merged[sort_idx, :]
            elif dat.ndim == 3 and dat.shape[0] == nw:
                # (nw, nVt, nVb) — flatten gate dims
                return dat.reshape(nw, -1)[sort_idx, :]
            elif dat.ndim == 3 and dat.shape[2] == nw:
                # (nX, nY, nw) wavelength-last spatial map — transpose
                return dat.reshape(-1, nw).T[sort_idx, :]
            elif dat.ndim == 2 and dat.shape[0] == nw:
                return dat[sort_idx, :]
            elif dat.ndim == 2 and dat.shape[1] == nw:
                return dat.T[sort_idx, :]
            elif dat.ndim == 1 and dat.shape[0] == nw:
                # Standalone reference spectrum — treat as single gate point
                return dat[sort_idx, np.newaxis]
        except Exception:
            pass

    # datR/datL convention
    datR = _get_arr(mat_data, ["datR", "R", "dR"])
    datL = _get_arr(mat_data, ["datL", "L", "dL"])
    if datR is not None:
        datR = datR.reshape(nw, -1)
        if datL is not None and datL.size == datR.size:
            datL = datL.reshape(nw, -1)
            merged = _cmerge(datR, datL)
            return merged[sort_idx, :]
        return datR[sort_idx, :]

    return None


def _cmerge(ch1: np.ndarray, ch2: np.ndarray) -> np.ndarray:
    diff = ch1 - ch2
    out = 0.5 * (ch1 + ch2)
    out[diff > _CMERGE_THRESH] = ch2[diff > _CMERGE_THRESH]
    out[diff < -_CMERGE_THRESH] = ch1[diff < -_CMERGE_THRESH]
    return out


def _smooth_diff_kernel(n: int) -> np.ndarray:
    """
    Smooth differentiation filter (matches smooth_diff.m).
    Anti-symmetric kernel: for odd n, h = [-1...0...+1] / (m*(m+1))
    """
    if n < 2:
        return np.array([-1.0, 0.0, 1.0]) / 2.0
    if n % 2 == 1:
        m = (n - 1) // 2
        h = np.zeros(n)
        h[:m] = -1.0
        h[m] = 0.0
        h[m + 1:] = 1.0
        return h / (m * (m + 1))
    else:
        m = n // 2
        h = np.zeros(n)
        h[:m] = -1.0
        h[m:] = 1.0
        return h / (m * m)


def _subpixel_parabolic_min(x3: np.ndarray, y3: np.ndarray) -> tuple[float, float]:
    """Fit parabola through 3 points, return vertex (xc, yc)."""
    X = np.column_stack([x3 ** 2, x3, np.ones(3)])
    try:
        abc = np.linalg.lstsq(X, y3, rcond=None)[0]
    except Exception:
        return float(x3[np.argmin(y3)]), float(np.min(y3))
    a, b, c = abc
    if a <= 0:
        i = int(np.argmin(y3))
        return float(x3[i]), float(y3[i])
    xc = -b / (2 * a)
    yc = a * xc ** 2 + b * xc + c
    return float(xc), float(yc)


def _get_arr(mat_data: dict, keys: list[str]):
    for k in keys:
        if k in mat_data:
            try:
                arr = np.asarray(mat_data[k], dtype=float)
                if arr.size > 0:
                    return arr
            except (TypeError, ValueError):
                continue
    return None
