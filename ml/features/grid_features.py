"""Phase-6 per-pixel features for the gridded deep-convection target (config/ml_dataset.yaml).

Leakage rule (VALIDATION_PLAN §3 item 4): features for issue frame k read only ``bt[: k + 1]``; the slice is taken
before anything else and a test destroys future frames to check the features are unchanged.
The pySTEPS forecast used as a feature is the unchanged Phase-2 M1 baseline (``advection_grid``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.ndimage import minimum_filter, uniform_filter

from ml.forecasting.baselines import _SL, advection_grid

FEATURES = ["lead_min", "adv_bt", "adv_frac11", "adv_frac31", "adv_min11", "adv_valid_frac31", "pers_bt",
            "pers_frac31", "pers_min11", "tend30", "adv_tend", "adv_tend_mean31", "speed_px", "dom_cold_frac",
            "dom_cold_change60", "valid_hour_sin", "valid_hour_cos"]


def frac(event: np.ndarray, size: int) -> np.ndarray:
    return uniform_filter(event.astype(np.float32), size=size, mode="constant", cval=0.0)


def nanmin(x: np.ndarray, size: int) -> np.ndarray:
    m = minimum_filter(np.where(np.isfinite(x), x, np.inf), size=size, mode="constant", cval=np.inf)
    return np.where(np.isfinite(m), m, np.nan).astype(np.float32)


def nanmean(x: np.ndarray, size: int) -> np.ndarray:
    ok = np.isfinite(x)
    num = uniform_filter(np.where(ok, x, 0.0).astype(np.float64), size=size, mode="constant", cval=0.0)
    den = uniform_filter(ok.astype(np.float64), size=size, mode="constant", cval=0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 1e-9, num / den, np.nan).astype(np.float32)


def issue_features(bt: np.ndarray, k: int, dom: np.ndarray, times: pd.DatetimeIndex, cfg_b: dict,
                   thr: float = 235.0):
    """Yield (L, features dict of (ny, nx) float32 arrays, pySTEPS forecast at lead L) for L = 1..max_lead_steps.

    ``times`` must hold the frame times; only times[k] is read (valid time = issue time + L x cadence)."""
    past = bt[: k + 1]                                   # leakage guard: nothing after frame k is visible
    n_lead, cad = cfg_b["max_lead_steps"], cfg_b["cadence_min"]
    fa, vel = advection_grid(past, k, n_lead, cfg_b)
    P, P1, P2 = past[k], past[k - 1], past[k - 2]
    T = (P - P1).astype(np.float64)
    Tadv = np.asarray(_SL(T, vel, n_lead, outval=np.nan, allow_nonfinite_values=True), dtype=np.float32)
    speed = np.hypot(vel[0], vel[1]).astype(np.float32)

    def cold_frac(f):
        ok = dom & np.isfinite(f)
        return float((ok & (f < thr)).sum() / max(ok.sum(), 1))
    dcf = cold_frac(P)
    static = {"pers_bt": P.astype(np.float32), "pers_frac31": frac(np.isfinite(P) & (P < thr), 31),
              "pers_min11": nanmin(P, 11), "tend30": T.astype(np.float32), "speed_px": speed}
    for L in range(1, n_lead + 1):
        F = fa[L - 1]
        vh = (times[k] + pd.Timedelta(minutes=L * cad)).hour + (times[k] + pd.Timedelta(minutes=L * cad)).minute / 60
        fe = np.isfinite(F) & (F < thr)
        feats = {"lead_min": np.full(F.shape, L * cad, np.float32), "adv_bt": F.astype(np.float32),
                 "adv_frac11": frac(fe, 11), "adv_frac31": frac(fe, 31), "adv_min11": nanmin(F, 11),
                 "adv_valid_frac31": frac(np.isfinite(F), 31), **static,
                 "adv_tend": Tadv[L - 1], "adv_tend_mean31": nanmean(Tadv[L - 1], 31),
                 "dom_cold_frac": np.full(F.shape, dcf, np.float32),
                 "dom_cold_change60": np.full(F.shape, dcf - cold_frac(P2), np.float32),
                 "valid_hour_sin": np.full(F.shape, np.sin(2 * np.pi * vh / 24), np.float32),
                 "valid_hour_cos": np.full(F.shape, np.cos(2 * np.pi * vh / 24), np.float32)}
        yield L, feats, F


def stack(feats: dict, idx: np.ndarray) -> np.ndarray:
    """Feature matrix (n, len(FEATURES)) for the pixels at flat indices ``idx``."""
    return np.column_stack([feats[f].ravel()[idx] for f in FEATURES]).astype(np.float32)
