"""Tracking-quality audit metrics (Phase 3). The same functions are applied to every track version, so
before/after numbers are directly comparable.

Input: a "positions" table with one row per (cell, frame): cell, frame, feature, x, y (metres on the 2 km grid,
x = column * dxy, y = row * dxy), plus the segmentation mask (labels = feature id) and pySTEPS motion fields.
All metrics describe the tracks themselves; none uses the forecast baselines.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_STEP_KM = 4.0  # one native (4 km) pixel: displacements below this are within position noise


def steps(pos: pd.DataFrame) -> pd.DataFrame:
    """Consecutive (frame -> frame+1) steps within each cell, with displacement in km."""
    p = pos.sort_values(["cell", "frame"]).copy()
    g = p.groupby("cell")
    p["dx_km"] = g["x"].diff() / 1000.0
    p["dy_km"] = g["y"].diff() / 1000.0
    p["dframe"] = g["frame"].diff()
    p["prev_feature"] = g["feature"].shift()
    p["prev_x"], p["prev_y"] = g["x"].shift(), g["y"].shift()
    s = p[p["dframe"] == 1].copy()
    s["disp_km"] = np.hypot(s["dx_km"], s["dy_km"])
    return s


def zigzag_fraction(pos: pd.DataFrame) -> tuple[float, int]:
    """Fraction of consecutive step pairs whose direction turns by > 90 deg (both steps >= MIN_STEP_KM)."""
    s = steps(pos)
    s = s.sort_values(["cell", "frame"])
    s["pdx"] = s.groupby("cell")["dx_km"].shift()
    s["pdy"] = s.groupby("cell")["dy_km"].shift()
    s["pdisp"] = np.hypot(s["pdx"], s["pdy"])
    ok = (s["disp_km"] >= MIN_STEP_KM) & (s["pdisp"] >= MIN_STEP_KM)
    d = s[ok]
    cosang = (d["dx_km"] * d["pdx"] + d["dy_km"] * d["pdy"]) / (d["disp_km"] * d["pdisp"])
    return (float((cosang < 0).mean()) if len(d) else float("nan")), int(len(d))


def flow_consistency(pos: pd.DataFrame, mask: np.ndarray, vel: dict[int, np.ndarray], dxy: float) -> dict:
    """Compare each step's observed displacement with the mean pySTEPS flow over the parent segment (or at the
    parent position if unsegmented). ``vel[frame]`` is (2, ny, nx) px/step estimated from frames <= frame."""
    s = steps(pos)
    obs, flow = [], []
    for r in s.itertuples(index=False):
        k = int(r.frame) - 1
        if k not in vel:
            continue
        seg = mask[k] == int(r.prev_feature)
        if seg.any():
            u, v = vel[k][0][seg].mean(), vel[k][1][seg].mean()
        else:
            iy = int(np.clip(round(r.prev_y / dxy), 0, mask.shape[1] - 1))
            ix = int(np.clip(round(r.prev_x / dxy), 0, mask.shape[2] - 1))
            u, v = vel[k][0][iy, ix], vel[k][1][iy, ix]
        obs.append((r.dx_km, r.dy_km))
        flow.append((u * dxy / 1000.0, v * dxy / 1000.0))
    obs, flow = np.array(obs), np.array(flow)
    if len(obs) < 3:
        return {"n_steps": len(obs)}
    diff = np.hypot(*(obs - flow).T)
    return {"n_steps": int(len(obs)),
            "corr_x": float(np.corrcoef(obs[:, 0], flow[:, 0])[0, 1]),
            "corr_y": float(np.corrcoef(obs[:, 1], flow[:, 1])[0, 1]),
            "median_obs_step_km": float(np.median(np.hypot(*obs.T))),
            "median_flow_step_km": float(np.median(np.hypot(*flow.T))),
            "median_abs_dev_from_flow_km": float(np.median(diff))}


def link_overlap(pos: pd.DataFrame, mask: np.ndarray, vel: dict[int, np.ndarray], dxy: float) -> pd.DataFrame:
    """For each step between two SEGMENTED features: overlap of the parent segment (unshifted and flow-shifted)
    with the linked child segment, and with the best-overlapping other segment at the child time."""
    s = steps(pos)
    rows = []
    for r in s.itertuples(index=False):
        k = int(r.frame) - 1
        par = mask[k] == int(r.prev_feature)
        chi = mask[k + 1] == int(r.feature)
        if not (par.any() and chi.any()):
            continue
        rec = {"cell": r.cell, "frame": int(r.frame), "area_ratio": chi.sum() / par.sum()}
        shifts = {"none": (0, 0)}
        if k in vel:
            shifts["flow"] = (int(round(vel[k][1][par].mean())), int(round(vel[k][0][par].mean())))
        for name, (dy, dx) in shifts.items():
            sp = _shift(par, dy, dx)
            labels = mask[k + 1][sp]
            ov_linked = int((labels == int(r.feature)).sum())
            others = labels[(labels > 0) & (labels != int(r.feature))]
            ov_best_other = int(np.bincount(others).max()) if others.size else 0
            rec[f"ov_{name}_linked_frac"] = ov_linked / min(par.sum(), chi.sum())
            rec[f"better_other_{name}"] = ov_best_other > ov_linked
        rows.append(rec)
    return pd.DataFrame(rows)


def _shift(m: np.ndarray, dy: int, dx: int) -> np.ndarray:
    out = np.zeros_like(m)
    ny, nx = m.shape
    ys, yd = (slice(0, ny - dy), slice(dy, ny)) if dy >= 0 else (slice(-dy, ny), slice(0, ny + dy))
    xs, xd = (slice(0, nx - dx), slice(dx, nx)) if dx >= 0 else (slice(-dx, nx), slice(0, nx + dx))
    out[yd, xd] = m[ys, xs]
    return out


def summarize(pos: pd.DataFrame, mask: np.ndarray, vel: dict[int, np.ndarray], dxy: float, label: str) -> dict:
    s = steps(pos)
    zz, n_zz = zigzag_fraction(pos)
    lo = link_overlap(pos, mask, vel, dxy)
    life = pos.groupby("cell")["frame"].agg(lambda f: f.max() - f.min() + 1)
    out = {"version": label, "n_cells": int(pos["cell"].nunique()), "n_rows": int(len(pos)), "n_steps": int(len(s)),
           "median_step_km": float(s["disp_km"].median()), "p90_step_km": float(s["disp_km"].quantile(0.9)),
           "zigzag_frac": zz, "zigzag_n_pairs": n_zz,
           "cells_ge_4_frames": int((life >= 4).sum()),
           **{f"flow_{k}": v for k, v in flow_consistency(pos, mask, vel, dxy).items()}}
    if len(lo):
        out.update({"seg_links_n": int(len(lo)),
                    "seg_links_zero_overlap_both_frac": float(((lo["ov_none_linked_frac"] == 0) &
                                                               (lo.get("ov_flow_linked_frac", 0) == 0)).mean()),
                    "seg_links_better_other_none_frac": float(lo["better_other_none"].mean()),
                    "seg_links_area_jump_frac": float(((lo["area_ratio"] > 2) | (lo["area_ratio"] < 0.5)).mean())})
    return out
