"""Phase-2 baselines (VALIDATION_PLAN.md §1): M0 persistence and M1 pySTEPS Lagrangian extrapolation (grid),
plus object persistence / constant-velocity extrapolation of tracked cells.

Leakage rule (VALIDATION_PLAN §3 item 4): a forecast issued at frame index ``k`` may only read frames <= k.
The grid functions receive the full cube but slice ``bt[: k + 1]`` before doing anything; a test verifies
that changing future frames leaves the forecast unchanged.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from pysteps import extrapolation, motion

logging.getLogger("pysteps").setLevel(logging.WARNING)
_LK = motion.get_method("lucaskanade")
_SL = extrapolation.get_method("semilagrangian")


# ---------------- grid baselines ----------------

def persistence_grid(bt: np.ndarray, k: int, n_leads: int) -> np.ndarray:
    """M0 Eulerian persistence: BT(t + L) = BT(t) for L = 1..n_leads."""
    past = bt[: k + 1]
    return np.repeat(past[-1][None], n_leads, axis=0).astype(np.float32)


def coldness(bt: np.ndarray, ref_K: float) -> np.ndarray:
    """Motion tracer: max(0, ref - BT); NaN stays NaN."""
    return np.where(np.isfinite(bt), np.clip(ref_K - bt, 0.0, None), np.nan)


def advection_grid(bt: np.ndarray, k: int, n_leads: int, cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    """M1 pySTEPS Lucas-Kanade motion from the last n_past frames + semi-Lagrangian advection of BT(t).

    Returns (forecast (n_leads, ny, nx) K, velocity (2, ny, nx) px per step).
    """
    n_past = cfg["motion"]["n_past_frames"]
    if k + 1 < n_past:
        raise ValueError(f"issue index {k} has fewer than {n_past} past frames")
    past = bt[: k + 1][-n_past:]
    tracer = np.ma.masked_invalid(coldness(past, cfg["motion"]["tracer_ref_K"]))
    velocity = _LK(tracer, verbose=False)
    fc = _SL(past[-1].astype(np.float64), velocity, n_leads, outval=np.nan, allow_nonfinite_values=True)
    return np.asarray(fc, dtype=np.float32), np.asarray(velocity, dtype=np.float32)


# ---------------- object baselines ----------------

def object_forecasts(features: pd.DataFrame, n_leads: int, velocity_window: int, dxy_m: float) -> pd.DataFrame:
    """Per (cell, issue frame, lead): persistence and constant-velocity centroid forecasts vs the observed
    position of the same cell (truth exists only if the cell survives to t + L).

    Positions are tobac feature positions (hdim_1/hdim_2, the positions the linker used), in metres.
    Velocity uses only frames <= issue frame: displacement over ``velocity_window`` steps, falling back to 1 step.
    """
    f = features[features["cell"] != -1][["cell", "frame", "feature", "hdim_1", "hdim_2"]].copy()
    f["x"] = f["hdim_2"] * dxy_m
    f["y"] = f["hdim_1"] * dxy_m
    return object_forecasts_from_positions(f, n_leads, velocity_window)


def object_forecasts_from_positions(f: pd.DataFrame, n_leads: int, velocity_window: int) -> pd.DataFrame:
    """Same as ``object_forecasts`` for any position table with columns cell, frame, feature, x, y (metres)."""
    pos = {(int(c), int(fr)): (x, y, int(ft)) for c, fr, x, y, ft in f[["cell", "frame", "x", "y", "feature"]].itertuples(index=False)}
    rows = []
    for (cell, k), (x, y, feat) in pos.items():
        prev = None
        for w in (velocity_window, 1):
            if (cell, k - w) in pos:
                px, py, _ = pos[(cell, k - w)]
                prev = ((x - px) / w, (y - py) / w, w)
                break
        if prev is None:
            continue  # no motion history at issue time -> cell not forecastable by M1; skipped for both methods
        vx, vy, w = prev
        for L in range(1, n_leads + 1):
            obs = pos.get((cell, k + L))
            base = {"cell": cell, "issue_frame": k, "lead_steps": L, "velocity_window_used": w,
                    "issue_feature": feat, "x0": x, "y0": y,
                    "survived": obs is not None,
                    "obs_x": obs[0] if obs else np.nan, "obs_y": obs[1] if obs else np.nan,
                    "obs_feature": obs[2] if obs else -1}
            rows.append({**base, "method": "persistence", "pred_x": x, "pred_y": y})
            rows.append({**base, "method": "constant_velocity", "pred_x": x + vx * L, "pred_y": y + vy * L})
    out = pd.DataFrame(rows)
    out["centroid_err_km"] = np.hypot(out["pred_x"] - out["obs_x"], out["pred_y"] - out["obs_y"]) / 1000.0
    return out


def shifted_iou(mask_t: np.ndarray, mask_obs: np.ndarray, shift_px: tuple[int, int]) -> float:
    """IoU between a boolean mask shifted by (dy, dx) whole pixels (no wrap-around) and an observed mask."""
    dy, dx = shift_px
    shifted = np.zeros_like(mask_t)
    ny, nx = mask_t.shape
    if abs(dy) >= ny or abs(dx) >= nx:  # forecast object entirely off the grid: no overlap (Phase-4 fix)
        union = mask_obs.sum()
        return 0.0 if union else np.nan
    ys, yd = (slice(0, ny - dy), slice(dy, ny)) if dy >= 0 else (slice(-dy, ny), slice(0, ny + dy))
    xs, xd = (slice(0, nx - dx), slice(dx, nx)) if dx >= 0 else (slice(-dx, nx), slice(0, nx + dx))
    shifted[yd, xd] = mask_t[ys, xs]
    inter = np.logical_and(shifted, mask_obs).sum()
    union = np.logical_or(shifted, mask_obs).sum()
    return float(inter / union) if union else np.nan
