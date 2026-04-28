"""
PL (photoluminescence) file analyzer.

Follows the lab's standard analysis pipeline:
  1. cmerge: intelligent two-channel average (handle cosmic rays / dead pixels)
  2. Background subtraction: subtract mean of dark spectral region (first ~50 px)
  3. Energy conversion: E = 1240 / w_nm
  4. Integration over exciton/trion energy window (1.04–1.13 eV by default)
  5. Gate coverage: Vt/Vb axes, doping and displacement field range

Expected .mat variables (per WJL/Courtney analysis scripts):
  dat   — raw spectra, shape (n_wavelengths, n_pol, n_gate) or (n_wl, n_Vt, n_Vb)
  I     — intensity array (alternative to dat; same shape conventions)
  w     — wavelength axis in nm
  Vt    — top-gate voltages
  Vb    — bottom-gate voltages
  spectime / exptime — integration time (optional scalar)
"""

from __future__ import annotations

import warnings
from typing import Any


# Exciton / trion integration window (eV) — typical for tMoTe2 at low T
_EV_WINDOW_LO = 1.040
_EV_WINDOW_HI = 1.130

# Dark spectral region: first N pixels, used for background subtraction
_DARK_PX = 50

# cmerge threshold: if |ch1 - ch2| > X, use the quieter channel
_CMERGE_THRESH = 60.0


def analyze_pl(mat_data: dict[str, Any], filename: str) -> dict[str, Any]:
    """Extract PL quality metrics. Returns a flat dict."""
    metrics: dict[str, Any] = {}
    flags: list[str] = []

    try:
        import numpy as np

        # --- Wavelength axis ---
        w = _get_arr(mat_data, ["w", "wavelength", "wl"])
        if w is None:
            flags.append("missing_wavelength_axis")
            metrics["pl_flags"] = flags
            return metrics

        w = np.asarray(w, dtype=float).ravel()
        # Determine units: nm if values > 10, eV otherwise
        if np.nanmax(w) > 10:
            energy = 1240.0 / w          # nm → eV
            metrics["wavelength_unit"] = "nm"
        else:
            energy = w.copy()            # already eV
            metrics["wavelength_unit"] = "eV"
        nw = len(energy)

        # --- Load raw intensity array ---
        I_raw = _get_arr(mat_data, ["I", "dat", "spec", "spectra", "data"])
        if I_raw is None:
            flags.append("missing_intensity_array")
            metrics["pl_flags"] = flags
            return metrics
        I_raw = np.asarray(I_raw, dtype=float)

        # --- cmerge: intelligent two-channel merge ---
        # Shape conventions vary:
        #   (nw, 2, n_gate)   — wavelength first, polarization axis = 1
        #   (nw, nVt, nVb)    — wavelength first, no polarization
        #   (nVt, nVb, nw)    — wavelength last (spatial PL maps)
        #   (nw, n_gate)      — 1D gate sweep
        if I_raw.ndim == 3 and I_raw.shape[0] == nw and I_raw.shape[1] == 2:
            ch1 = I_raw[:, 0, :]
            ch2 = I_raw[:, 1, :]
            I_merged = _cmerge(ch1, ch2)
        elif I_raw.ndim == 3 and I_raw.shape[0] == nw:
            I_merged = I_raw.reshape(nw, -1)
        elif I_raw.ndim == 3 and I_raw.shape[2] == nw:
            # Wavelength-last spatial map: (nX, nY, nw) → transpose to (nw, nX*nY)
            I_merged = I_raw.reshape(-1, nw).T
        elif I_raw.ndim == 2 and I_raw.shape[0] == nw:
            I_merged = I_raw
        elif I_raw.ndim == 2 and I_raw.shape[1] == nw:
            I_merged = I_raw.T
        elif I_raw.ndim == 1 and I_raw.shape[0] == nw:
            I_merged = I_raw[:, np.newaxis]
        else:
            flags.append(f"unexpected_shape:{I_raw.shape}")
            metrics["pl_flags"] = flags
            return metrics

        # --- Background subtraction (dark spectral region) ---
        n_dark = min(_DARK_PX, nw // 10)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            dark_bias = np.nanmean(I_merged[:n_dark, :], axis=0, keepdims=True)
        I_sub = I_merged - dark_bias

        # --- Mean spectrum over all gate points ---
        spec_mean = np.nanmean(I_sub, axis=1)   # (nw,)
        finite = spec_mean[np.isfinite(spec_mean)]
        if finite.size == 0:
            flags.append("all_nan_after_bg_sub")
            metrics["pl_flags"] = flags
            return metrics

        # --- Find energy window for integration ---
        e_lo, e_hi = _EV_WINDOW_LO, _EV_WINDOW_HI
        if np.nanmin(energy) < 10:  # energy is in eV
            px_lo = np.argmin(np.abs(energy - e_lo))
            px_hi = np.argmin(np.abs(energy - e_hi))
            if px_lo > px_hi:
                px_lo, px_hi = px_hi, px_lo
        else:
            # Energy axis might be decreasing (wavelength → energy not sorted)
            px_lo = min(np.argmin(np.abs(energy - e_lo)), np.argmin(np.abs(energy - e_hi)))
            px_hi = max(np.argmin(np.abs(energy - e_lo)), np.argmin(np.abs(energy - e_hi)))

        if px_hi <= px_lo:
            px_lo, px_hi = 0, nw - 1

        window_spec = spec_mean[px_lo:px_hi + 1]
        finite_window = window_spec[np.isfinite(window_spec)]

        # --- Intensity stats ---
        bg_est = float(np.nanpercentile(spec_mean, 5))
        if finite_window.size > 0:
            peak_intensity = float(np.nanmax(finite_window))
            peak_idx_in_window = px_lo + int(np.nanargmax(window_spec))
        else:
            peak_intensity = float(np.nanmax(finite))
            peak_idx_in_window = int(np.nanargmax(spec_mean))

        metrics["peak_intensity_raw"] = round(peak_intensity, 1)
        metrics["background_level"] = round(bg_est, 1)
        snr = (peak_intensity - bg_est) / max(abs(bg_est), 1.0)
        metrics["peak_snr"] = round(snr, 2)

        if snr < 2.0:
            flags.append(f"low_snr:{snr:.1f}")
        if peak_intensity < 10:
            flags.append("very_low_intensity")

        # Peak energy
        peak_energy = float(energy[peak_idx_in_window])
        if np.nanmax(energy) < 10:   # in eV
            metrics["peak_energy_eV"] = round(peak_energy, 4)
            # Flag if peak is outside typical tMoTe2 window (0.95–1.20 eV)
            if not (0.95 < peak_energy < 1.20):
                flags.append(f"peak_outside_typical_window:{peak_energy:.3f}eV")
        else:
            metrics["peak_wavelength_nm"] = round(peak_energy, 1)

        # Integrated intensity over window
        if finite_window.size > 0:
            metrics["integrated_intensity"] = round(float(np.nansum(finite_window)), 1)

        # --- Gate coverage ---
        for gk, gl in [("Vt", "top_gate"), ("Vb", "bottom_gate")]:
            vg = _get_arr(mat_data, [gk])
            if vg is not None:
                vg = np.asarray(vg, dtype=float).ravel()
                if vg.size > 1:
                    metrics[f"{gl}_min_V"] = round(float(np.nanmin(vg)), 3)
                    metrics[f"{gl}_max_V"] = round(float(np.nanmax(vg)), 3)
                    metrics[f"{gl}_npoints"] = int(vg.size)

        # Total gate points
        if I_raw.ndim == 3:
            if I_raw.shape[1] == 2:  # polarization axis present
                metrics["gate_points_total"] = int(I_raw.shape[2])
            else:
                metrics["gate_points_total"] = int(I_raw.shape[1]) * int(I_raw.shape[2])
        elif I_raw.ndim == 2:
            metrics["gate_points_total"] = int(I_raw.shape[1])

        # Integration time
        t = mat_data.get("spectime") or mat_data.get("exptime")
        if t is not None:
            try:
                metrics["integration_time_s"] = float(t)
            except (TypeError, ValueError):
                pass

        # NaN gate fraction: how complete is the sweep?
        if I_merged.ndim == 2:
            nan_fraction = float(np.mean(np.all(~np.isfinite(I_merged), axis=0)))
            metrics["nan_gate_fraction"] = round(nan_fraction, 3)
            if nan_fraction > 0.5:
                flags.append(f"mostly_nan_gate_points:{nan_fraction:.0%}")

    except Exception as e:
        flags.append(f"analysis_error:{str(e)[:80]}")

    metrics["pl_flags"] = flags
    return metrics


def _cmerge(ch1: "np.ndarray", ch2: "np.ndarray") -> "np.ndarray":
    """Intelligent two-channel merge (matches lab cmerge.m logic)."""
    import numpy as np
    diff = ch1 - ch2
    out = 0.5 * (ch1 + ch2)
    out[diff > _CMERGE_THRESH] = ch2[diff > _CMERGE_THRESH]
    out[diff < -_CMERGE_THRESH] = ch1[diff < -_CMERGE_THRESH]
    return out


def _get_arr(mat_data: dict, keys: list[str]):
    import numpy as np
    for k in keys:
        if k in mat_data:
            try:
                arr = np.asarray(mat_data[k], dtype=float)
                if arr.size > 0:
                    return arr
            except (TypeError, ValueError):
                continue
    return None
