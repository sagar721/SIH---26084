"""Per-cell lifecycle table: centroid, area, movement, lifetime, growth/decay, phase (rules v0).

All quantities are computed from the tracked features and the segmentation mask of real frames.
Phase rules come from ``config/phases.yaml`` (PROPOSED; mentor sign-off pending, decision D7).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml
from pyproj import Geod, Transformer
from scipy.ndimage import binary_dilation

from ml.tracking.overlap_link import coldness_centroid

GEOD = Geod(ellps="WGS84")


def load_phase_rules(path: Path = Path("config/phases.yaml")) -> dict:
    return yaml.safe_load(path.read_text())


def movement(lat: np.ndarray, lon: np.ndarray, dt_s: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Speed (km/h) and heading (deg clockwise from north, direction of travel) between consecutive points.

    The first element of each output is NaN (no previous position).
    """
    speed = np.full(len(lat), np.nan)
    heading = np.full(len(lat), np.nan)
    if len(lat) > 1:
        az, _, dist_m = GEOD.inv(lon[:-1], lat[:-1], lon[1:], lat[1:])
        speed[1:] = (dist_m / 1000.0) / (dt_s[1:] / 3600.0)
        heading[1:] = np.mod(az, 360.0)
    return speed, heading


def per_feature_stats(feats: pd.DataFrame, bt: xr.DataArray, mask: xr.DataArray, cold_core_K: float,
                      pixel_area_km2: float, centroid: str = "segment", coldness_ref_K: float = 245.0) -> pd.DataFrame:
    """Min BT, segment area, cold-core area for each feature from the real BT field and mask."""
    rows = []
    bt_v, mask_v = bt.values, mask.values
    for _, f in feats.iterrows():
        k = int(f["frame"])
        seg = mask_v[k] == int(f["feature"])
        touches_missing = False
        if seg.any():
            vals = bt_v[k][seg]
            min_bt = float(np.nanmin(vals))
            area = float(seg.sum() * pixel_area_km2)
            core = float((vals < cold_core_K).sum() * pixel_area_km2)
            # Flag cells whose segment (dilated by 1 px) touches missing data: area/min BT may be biased.
            touches_missing = bool(np.isnan(bt_v[k][binary_dilation(seg)]).any())
            if centroid == "coldness":  # Phase 3: centroid weighted by (coldness_ref_K - BT)
                ci, cj = coldness_centroid(seg, bt_v[k], coldness_ref_K)
                pos_src = "coldness"
            else:
                ii, jj = np.nonzero(seg)
                ci, cj = float(ii.mean()), float(jj.mean())  # area-weighted segment centroid (grid index)
                pos_src = "segment"
        else:
            # Feature warmer than the segmentation threshold: take min BT in a 3x3 window around it.
            i, j = int(round(f["hdim_1"])), int(round(f["hdim_2"]))
            win = bt_v[k][max(i - 1, 0):i + 2, max(j - 1, 0):j + 2]
            min_bt = float(np.nanmin(win)) if np.isfinite(win).any() else float("nan")
            area, core = 0.0, 0.0
            ci, cj, pos_src = float(f["hdim_1"]), float(f["hdim_2"]), "feature"
        rows.append({"feature": int(f["feature"]), "min_bt_K": min_bt, "area_km2": area, "cold_core_km2": core,
                     "touches_missing": touches_missing, "cy_idx": ci, "cx_idx": cj, "centroid_source": pos_src})
    return feats.merge(pd.DataFrame(rows), on="feature")


def _net_motion(g: pd.DataFrame, t: pd.Series) -> dict:
    """Net displacement speed/heading from first to last position: robust to per-step centroid jitter."""
    hours = (t.max() - t.min()).total_seconds() / 3600.0
    if hours <= 0:
        return {"net_speed_kmh": np.nan, "net_heading_deg": np.nan, "net_displacement_km": 0.0}
    az, _, d = GEOD.inv(g["lon"].iloc[0], g["lat"].iloc[0], g["lon"].iloc[-1], g["lat"].iloc[-1])
    return {"net_speed_kmh": d / 1000.0 / hours, "net_heading_deg": float(np.mod(az, 360.0)),
            "net_displacement_km": d / 1000.0}


def assign_phases(g: pd.DataFrame, rules: dict) -> list[str]:
    """Apply phase rules v0 to one cell's time-ordered rows (rates per 30 min)."""
    phases: list[str] = []
    prev = None
    for idx in range(len(g)):
        r = g.iloc[idx]
        d_bt = r["d_min_bt_30"]
        d_area = r["area_change_frac_30"]
        d_core = r["d_cold_core_30"]
        phase = None
        if (np.isfinite(d_bt) and d_bt >= rules["decaying"]["min_bt_warming_K_per_30min"]
                and np.isfinite(d_core) and d_core < 0):
            phase = "Decaying"
        elif (r["min_bt_K"] < rules["mature"]["min_bt_below_K"] and np.isfinite(d_area)
              and abs(d_area) <= rules["mature"]["area_change_frac_abs_max"]):
            phase = "Mature"
        elif np.isfinite(d_bt) and np.isfinite(d_area) and d_bt < 0 and d_area > 0:
            phase = "Developing"
        elif (idx <= 1 and r["min_bt_K"] < rules["initiation"]["bt_below_K"]
              and np.isfinite(d_bt) and d_bt <= rules["initiation"]["cooling_K_per_30min"]):
            phase = "Initiation"
        phase = phase or prev or "Unclassified"
        phases.append(phase)
        prev = phase
    return phases


def build_lifecycle(feats: pd.DataFrame, bt: xr.DataArray, mask: xr.DataArray, crs_proj4: str,
                    resolution_m: float, rules: dict, cell_to_track: dict,
                    centroid: str = "segment") -> tuple[pd.DataFrame, pd.DataFrame]:
    feats = feats[feats["cell"] != -1].copy()
    pixel_km2 = (resolution_m / 1000.0) ** 2
    feats = per_feature_stats(feats, bt, mask, rules["cold_core_K"], pixel_km2, centroid=centroid)

    # Centroid: segment (< segmentation threshold) area-weighted centroid where a segment exists, else the
    # tobac feature position. The multithreshold feature position jumps when the coldest threshold level
    # changes (median step speed 90 vs 60 km/h on 14 May 2026), so the segment centroid is preferred.
    x0, y0 = float(bt.x.values[0]), float(bt.y.values[0])
    feats["x_m"] = x0 + feats["cx_idx"] * resolution_m
    feats["y_m"] = y0 + feats["cy_idx"] * resolution_m
    to_ll = Transformer.from_crs(crs_proj4, "EPSG:4326", always_xy=True)
    feats["lon"], feats["lat"] = to_ll.transform(feats["x_m"].values, feats["y_m"].values)

    out = []
    for cell, g in feats.sort_values("time").groupby("cell"):
        g = g.copy()
        t = pd.to_datetime(g["time"]).values
        dt_s = np.r_[np.nan, np.diff(t) / np.timedelta64(1, "s")]
        g["speed_kmh"], g["heading_deg"] = movement(g["lat"].values, g["lon"].values, dt_s)
        scale = 1800.0 / dt_s  # normalise differences to per-30-min rates
        g["d_min_bt_30"] = g["min_bt_K"].diff().values * scale
        prev_area = g["area_km2"].shift()
        g["area_change_frac_30"] = np.where(prev_area > 0, (g["area_km2"] - prev_area) / prev_area, np.nan) * scale
        g["d_cold_core_30"] = g["cold_core_km2"].diff().values * scale
        g["phase"] = assign_phases(g.reset_index(drop=True), rules)
        g["track_family"] = cell_to_track.get(str(int(cell)), cell_to_track.get(int(cell), -1))
        out.append(g)
    per_frame = pd.concat(out, ignore_index=True)

    def _summ(g: pd.DataFrame) -> pd.Series:
        t = pd.to_datetime(g["time"])
        return pd.Series({
            "track_family": int(g["track_family"].iloc[0]),
            "first_time_utc": t.min(), "last_time_utc": t.max(),
            "n_frames": len(g), "lifetime_min": (t.max() - t.min()).total_seconds() / 60.0,
            "start_lat": g["lat"].iloc[0], "start_lon": g["lon"].iloc[0],
            "end_lat": g["lat"].iloc[-1], "end_lon": g["lon"].iloc[-1],
            "min_bt_K": g["min_bt_K"].min(), "max_area_km2": g["area_km2"].max(),
            "max_cold_core_km2": g["cold_core_km2"].max(),
            "median_step_speed_kmh": np.nanmedian(g["speed_kmh"]) if g["speed_kmh"].notna().any() else np.nan,
            **_net_motion(g, t),
            "max_cooling_K_per_30": np.nanmin(g["d_min_bt_30"]) if g["d_min_bt_30"].notna().any() else np.nan,
            "phases_seen": ",".join(dict.fromkeys(g["phase"])),
            "frames_touching_missing": int(g["touches_missing"].sum()),
        })

    summary = per_frame.groupby("cell").apply(_summ, include_groups=False).reset_index()
    fam_size = summary.groupby("track_family")["cell"].transform("size")
    summary["merge_split_family_size"] = np.where(summary["track_family"] >= 0, fam_size, 1)
    return per_frame, summary
