"""
Generic file health checks applied to any .mat file before modality analysis.

Conservative: only flags genuine data problems, not expected physics patterns.
All-NaN arrays are only flagged if they are the *primary* data variable
(e.g., the RMCD or intensity array) — sparse NaN from incomplete gate sweeps
is expected and handled by the modality analyzers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Primary data variable names by modality — these are checked for NaN/zero
_PRIMARY_VARS: dict[str, list[str]] = {
    "PL":          ["I", "dat"],
    "Reflectance": ["I", "dat", "datR"],
    "RMCD":        ["RMCD_up", "RMCD_down", "RMCD"],
    "unknown":     [],
}

_MIN_SANE_BYTES = 512


def check_generic(
    path: Path,
    mat_data: dict[str, Any] | None,
    load_error: str | None,
    modality: str,
) -> tuple[list[str], dict[str, Any]]:
    """Returns (quality_flags, metrics_dict)."""
    flags: list[str] = []
    metrics: dict[str, Any] = {}

    # File size
    try:
        size = path.stat().st_size
        metrics["file_size_bytes"] = size
        if size < _MIN_SANE_BYTES:
            flags.append(f"tiny_file:{size}b")
    except OSError:
        flags.append("stat_failed")

    if mat_data is None:
        flags.append("load_failed")
        if load_error:
            metrics["load_error"] = load_error[:120]
        return flags, metrics

    import numpy as np

    variables = list(mat_data.keys())
    metrics["variable_count"] = len(variables)

    # Check primary data variables for complete NaN or all-zeros.
    # Only flag arrays with at least 10 elements — scalar NaN placeholders
    # (common in acquisition scripts that pre-allocate fields) are not errors.
    primary_vars = _PRIMARY_VARS.get(modality, [])
    for key in primary_vars:
        if key not in mat_data:
            continue
        try:
            arr = np.asarray(mat_data[key], dtype=float)
        except (TypeError, ValueError):
            continue
        if arr.size < 10:
            # Scalar or tiny array — likely a metadata placeholder, not data
            continue

        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            flags.append(f"all_nan:{key}")
        elif finite.size == arr.size and np.all(finite == 0):
            flags.append(f"all_zeros:{key}")

    # Check for degenerate shape on any array variable (suggests incomplete acquisition)
    for key, val in mat_data.items():
        try:
            arr = np.asarray(val, dtype=float)
        except (TypeError, ValueError):
            continue
        if arr.ndim >= 2 and 0 in arr.shape:
            flags.append(f"zero_dimension:{key}:{arr.shape}")

    return flags, metrics
