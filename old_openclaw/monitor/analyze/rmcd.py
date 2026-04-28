"""
RMCD (reflective magnetic circular dichroism) file analyzer.

Two distinct file types in this lab:

1. Gate-map (dualgate sweep at fixed B field):
   Variables: RMCD (Vt × Vb), Vt, Vb, xc (resonance center energy), xp1f
   Analysis: gate-dependent RMCD map — mean, contrast, gate coverage
   Physics: identifies ferromagnetic vs. paramagnetic regions in (n, D) space

2. Hysteresis loop (B-field sweep at fixed gate voltage):
   Variables: Bsel, RMCD_up, RMCD_down, Vtset, Vbset
   Analysis: coercive field, remanence, loop area, saturation contrast
   Physics: quantifies ferromagnetic order; zero Hc is EXPECTED PHYSICS at
            paramagnetic filling factors — do not flag as instrument error

Notes on the D93 dataset:
- dt = 14 nm, db = 15 nm (BN thickness)
- dualgate files: RMCD is (nVt, nVb) indexed by gate voltage, NOT a spatial map
- xc variable: optical resonance center energy tracked alongside RMCD
- Zero coercive field at some gate voltages during a Curie-Weiss sweep is the
  expected physics signal (phase boundary between FM and PM phases)
"""

from __future__ import annotations

import numpy as np
from typing import Any


def analyze_rmcd(mat_data: dict[str, Any], filename: str) -> dict[str, Any]:
    """Extract RMCD quality metrics. Returns a flat dict."""
    metrics: dict[str, Any] = {}
    flags: list[str] = []

    try:
        # --- Detect file type ---
        # Priority: hysteresis (B axis + RMCD_up/down) > gate_map (2D RMCD + Vt/Vb) > spatial
        # B-field axis may be named Bsel (post-processed) or field_up/field_down (raw LabOne output).
        has_bsel = ("Bsel" in mat_data and np.asarray(mat_data["Bsel"], dtype=float).size > 5) or \
                   ("field_up" in mat_data and np.asarray(mat_data["field_up"], dtype=float).size > 5)
        has_up = "RMCD_up" in mat_data
        has_down = "RMCD_down" in mat_data

        if (has_up or has_down) and has_bsel:
            metrics["rmcd_type"] = "hysteresis_loop"
            _analyze_hysteresis(mat_data, metrics, flags)
        elif "RMCD" in mat_data:
            rmcd_arr = np.asarray(mat_data["RMCD"], dtype=float)
            if rmcd_arr.ndim == 2 and rmcd_arr.size >= 4 and "Vt" in mat_data and "Vb" in mat_data:
                metrics["rmcd_type"] = "gate_map"
                _analyze_gate_map(mat_data, rmcd_arr, metrics, flags)
            elif rmcd_arr.ndim == 2 and rmcd_arr.size >= 4:
                metrics["rmcd_type"] = "spatial_map"
                _analyze_spatial(rmcd_arr, metrics, flags)
            elif rmcd_arr.ndim == 1 and rmcd_arr.size >= 4:
                metrics["rmcd_type"] = "1d_scan"
                finite = rmcd_arr[np.isfinite(rmcd_arr)]
                if finite.size > 0:
                    metrics["rmcd_mean"] = round(float(np.mean(finite)), 5)
                    metrics["rmcd_range"] = round(float(np.ptp(finite)), 5)
            else:
                # Scalar or tiny RMCD — placeholder only; not an error
                metrics["rmcd_type"] = "placeholder"
        else:
            flags.append("unrecognized_rmcd_format")
            metrics["available_keys"] = list(mat_data.keys())[:10]

    except Exception as e:
        flags.append(f"analysis_error:{str(e)[:80]}")

    metrics["rmcd_flags"] = flags
    return metrics


def _analyze_hysteresis(mat_data: dict, metrics: dict, flags: list) -> None:
    """
    Analyze a hysteresis loop sweep (Bsel or field_up, RMCD_up, RMCD_down).

    Coercive field is found from zero-crossing of (RMCD_up + RMCD_down)/2
    (the irreversible part of the loop), not from the mean of the full array.
    Zero Hc is NOT flagged as an error — it is expected physics at paramagnetic
    filling factors (phase boundary of the ferromagnetic phase in tMoTe₂).
    """
    # Accept both Bsel (processed) and field_up (raw LabOne) as B-field axis
    if "Bsel" in mat_data:
        Bsel = np.asarray(mat_data["Bsel"], dtype=float).ravel()
    elif "field_up" in mat_data:
        Bsel = np.asarray(mat_data["field_up"], dtype=float).ravel()
    else:
        flags.append("missing_bfield_axis")
        return
    RMCD_up = np.asarray(mat_data["RMCD_up"], dtype=float).ravel()
    RMCD_down = np.asarray(mat_data.get("RMCD_down", np.full_like(RMCD_up, np.nan)), dtype=float).ravel()

    n = min(len(Bsel), len(RMCD_up), len(RMCD_down))
    Bsel, RMCD_up, RMCD_down = Bsel[:n], RMCD_up[:n], RMCD_down[:n]

    finite_up = np.isfinite(RMCD_up)
    if finite_up.sum() < 10:
        flags.append("insufficient_finite_hysteresis_points")
        return

    Bsel_f = Bsel[finite_up]
    up_f = RMCD_up[finite_up]

    metrics["B_min_T"] = round(float(np.min(Bsel_f)), 3)
    metrics["B_max_T"] = round(float(np.max(Bsel_f)), 3)
    metrics["hysteresis_npoints"] = int(finite_up.sum())

    # Saturation: mean value in top/bottom 10% of field range
    B_thresh_hi = np.percentile(Bsel_f, 90)
    B_thresh_lo = np.percentile(Bsel_f, 10)
    hi_mask = Bsel_f >= B_thresh_hi
    lo_mask = Bsel_f <= B_thresh_lo
    if hi_mask.any() and lo_mask.any():
        sat_hi = float(np.mean(up_f[hi_mask]))
        sat_lo = float(np.mean(up_f[lo_mask]))
        metrics["saturation_high_B"] = round(sat_hi, 5)
        metrics["saturation_low_B"] = round(sat_lo, 5)
        contrast = abs(sat_hi - sat_lo)
        metrics["saturation_contrast"] = round(contrast, 5)
        if contrast < 1e-5:
            flags.append("no_saturation_contrast")

    # Coercive field from midpoint zero-crossing of averaged loop
    # Using (up + down)/2 isolates the irreversible (hysteretic) component
    finite_down = np.isfinite(RMCD_down)
    if finite_down.sum() >= 10:
        Bsel_fd = Bsel[finite_down]
        down_f = RMCD_down[finite_down]
        # Interpolate down onto up's grid for averaging
        if len(Bsel_fd) == len(Bsel_f):
            midpoint = 0.5 * (up_f + down_f)
        else:
            midpoint = up_f  # fallback

        # Sort by B for zero-crossing detection
        sort_idx = np.argsort(Bsel_f)
        B_sorted = Bsel_f[sort_idx]
        mid_sorted = midpoint[sort_idx] if len(midpoint) == len(sort_idx) else up_f[sort_idx]

        # Offset by mean (removes paramagnetic background)
        mid_centered = mid_sorted - np.mean(mid_sorted)
        sign_changes = np.where(np.diff(np.sign(mid_centered)))[0]
        if sign_changes.size >= 1:
            # Interpolate for sub-point precision
            hc_vals = []
            for idx in sign_changes[:4]:  # at most 2 crossings for a loop
                B1, B2 = B_sorted[idx], B_sorted[idx + 1]
                s1, s2 = mid_centered[idx], mid_centered[idx + 1]
                if abs(s2 - s1) > 1e-12:
                    Bc = B1 - s1 * (B2 - B1) / (s2 - s1)
                    hc_vals.append(abs(Bc))
            if hc_vals:
                metrics["coercive_field_T"] = round(float(np.mean(hc_vals)), 4)
                # NOTE: Do NOT flag near-zero Hc — it is expected physics at
                # paramagnetic filling factors in a Curie-Weiss sweep.
                # Only flag if it looks like measurement noise (Hc > B_max)
                if metrics["coercive_field_T"] > abs(metrics["B_max_T"]):
                    flags.append("coercive_field_exceeds_field_range")

        # Loop area (integral of closed hysteresis loop)
        try:
            finite_both = np.isfinite(RMCD_up) & np.isfinite(RMCD_down)
            if finite_both.sum() > 20:
                area = abs(
                    float(np.trapz(RMCD_up[finite_both], Bsel[finite_both]))
                    - float(np.trapz(RMCD_down[finite_both], Bsel[finite_both]))
                )
                metrics["hysteresis_loop_area"] = round(area, 6)
                # Very small loop area at intermediate field CAN be physics (at phase boundary)
                # Only flag if field range is large and area is effectively zero
                if area < 1e-6 and abs(metrics.get("B_max_T", 0)) > 0.5:
                    flags.append("vanishing_loop_area_at_high_field")
        except Exception:
            pass

    # Gate voltage context (informs whether zero Hc is expected)
    for k in ("Vtset", "Vbset"):
        v = mat_data.get(k)
        if v is not None:
            try:
                metrics[k] = round(float(v), 4)
            except (TypeError, ValueError):
                pass


def _analyze_gate_map(
    mat_data: dict, rmcd_arr: np.ndarray, metrics: dict, flags: list
) -> None:
    """
    Analyze a dualgate RMCD map: RMCD(Vt, Vb).

    This is the primary format for D93 dualgate sweeps — RMCD is a 2D array
    indexed by (Vt_index, Vb_index), showing how RMCD amplitude varies with
    carrier density and displacement field.
    """
    Vt = np.asarray(mat_data["Vt"], dtype=float).ravel()
    Vb = np.asarray(mat_data["Vb"], dtype=float).ravel()

    finite = rmcd_arr[np.isfinite(rmcd_arr)]
    total = rmcd_arr.size
    metrics["gate_map_shape"] = list(rmcd_arr.shape)
    metrics["gate_map_nVt"] = int(len(Vt))
    metrics["gate_map_nVb"] = int(len(Vb))

    if finite.size == 0:
        flags.append("all_nan_gate_map")
        return

    fill_fraction = finite.size / total
    metrics["fill_fraction"] = round(fill_fraction, 3)
    if fill_fraction < 0.1:
        flags.append(f"mostly_nan_gate_map:{fill_fraction:.0%}_filled")

    metrics["rmcd_mean"] = round(float(np.mean(finite)), 4)
    metrics["rmcd_std"] = round(float(np.std(finite)), 4)
    metrics["rmcd_min"] = round(float(np.min(finite)), 4)
    metrics["rmcd_max"] = round(float(np.max(finite)), 4)
    metrics["rmcd_range"] = round(float(np.max(finite) - np.min(finite)), 4)

    # Gate voltage coverage
    metrics["Vt_min_V"] = round(float(np.min(Vt)), 3)
    metrics["Vt_max_V"] = round(float(np.max(Vt)), 3)
    metrics["Vb_min_V"] = round(float(np.min(Vb)), 3)
    metrics["Vb_max_V"] = round(float(np.max(Vb)), 3)

    if np.std(finite) < 1e-5:
        flags.append("no_gate_dependent_contrast")

    # xc: resonance center energy if tracked alongside RMCD
    xc = mat_data.get("xc")
    if xc is not None:
        xc_arr = np.asarray(xc, dtype=float)
        xc_finite = xc_arr[np.isfinite(xc_arr)]
        if xc_finite.size > 0:
            metrics["resonance_center_mean_eV"] = round(float(np.mean(xc_finite)), 5)
            metrics["resonance_center_range_eV"] = round(float(np.ptp(xc_finite)), 5)


def _analyze_spatial(rmcd_arr: np.ndarray, metrics: dict, flags: list) -> None:
    """Analyze a 2D RMCD spatial map (x, y coordinates)."""
    finite = rmcd_arr[np.isfinite(rmcd_arr)]
    if finite.size == 0:
        flags.append("all_nan_spatial")
        return

    metrics["spatial_shape"] = list(rmcd_arr.shape)
    metrics["spatial_mean"] = round(float(np.mean(finite)), 5)
    metrics["spatial_std"] = round(float(np.std(finite)), 5)
    metrics["spatial_range"] = round(float(np.ptp(finite)), 5)

    if np.std(finite) < 1e-6:
        flags.append("no_spatial_variation")

    try:
        peak_pos = np.unravel_index(int(np.nanargmax(np.abs(rmcd_arr))), rmcd_arr.shape)
        metrics["peak_location_ij"] = list(peak_pos)
    except Exception:
        pass
