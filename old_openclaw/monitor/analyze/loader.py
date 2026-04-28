"""
.mat file loader with graceful error handling.

Supports both MATLAB v5 (scipy.io.loadmat) and v7.3 / HDF5 (h5py).
Returns a plain dict of variable_name -> numpy array, or None on failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_mat(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    """
    Load a .mat file. Returns (data_dict, error_message).
    data_dict is None on failure; error_message is None on success.

    Variable names starting with '_' (MATLAB metadata) are excluded.
    """
    try:
        import scipy.io  # type: ignore[import]
        data = scipy.io.loadmat(str(path), squeeze_me=True, struct_as_record=False)
        cleaned = {k: v for k, v in data.items() if not k.startswith("_")}
        return cleaned, None
    except Exception as e1:
        # Try HDF5 format (MATLAB v7.3)
        try:
            import h5py  # type: ignore[import]
            import numpy as np
            with h5py.File(str(path), "r") as f:
                cleaned = {}
                for k in f.keys():
                    if k.startswith("_"):
                        continue
                    try:
                        cleaned[k] = np.array(f[k])
                    except Exception:
                        cleaned[k] = None
            return cleaned, None
        except ImportError:
            pass
        except Exception:
            pass
        return None, str(e1)


def array_stats(arr: Any) -> dict[str, Any] | None:
    """
    Return basic stats for a numpy array.
    Returns None if input is not array-like.
    """
    try:
        import numpy as np
        a = np.asarray(arr, dtype=float)
        if a.size == 0:
            return {"shape": a.shape, "size": 0, "all_zeros": True, "all_nan": True}
        finite = a[np.isfinite(a)]
        return {
            "shape": a.shape,
            "size": int(a.size),
            "all_zeros": bool(np.all(a == 0)),
            "all_nan": bool(np.all(~np.isfinite(a))),
            "nan_fraction": float(np.sum(~np.isfinite(a)) / a.size),
            "min": float(np.min(finite)) if finite.size else float("nan"),
            "max": float(np.max(finite)) if finite.size else float("nan"),
            "mean": float(np.mean(finite)) if finite.size else float("nan"),
            "std": float(np.std(finite)) if finite.size else float("nan"),
        }
    except Exception:
        return None
