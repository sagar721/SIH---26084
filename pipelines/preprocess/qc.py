"""Frame-level quality control (PRD F2): physical BT range, missing fraction, time monotonicity."""
from __future__ import annotations

import numpy as np

BT_MIN_K, BT_MAX_K = 170.0, 330.0
MAX_MISSING_FRAC = 0.05


def frame_qc(bt: np.ndarray, in_domain: np.ndarray) -> dict:
    vals = bt[in_domain]
    finite = np.isfinite(vals)
    missing_frac = float(1.0 - finite.mean())
    out_of_range = float(((vals[finite] < BT_MIN_K) | (vals[finite] > BT_MAX_K)).mean()) if finite.any() else 1.0
    return {
        "missing_frac": missing_frac,
        "out_of_range_frac": out_of_range,
        "bt_min": float(np.nanmin(vals)) if finite.any() else float("nan"),
        "bt_max": float(np.nanmax(vals)) if finite.any() else float("nan"),
        "status": "OK" if (missing_frac <= MAX_MISSING_FRAC and out_of_range == 0.0) else "QC_FAIL",
    }


def times_monotonic(times) -> bool:
    t = np.asarray(times, dtype="datetime64[ns]")
    return bool(np.all(np.diff(t) > np.timedelta64(0, "ns")))
