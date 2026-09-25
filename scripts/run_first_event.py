"""Phase-1 end-to-end run on one real event.

  python -m scripts.run_first_event --event E8_20260514

Steps: (download is separate: pipelines.ingest.*) cube -> tobac tracking -> lifecycle -> figures -> provenance.
Every step reads only files produced from the real downloads recorded in the manifests.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml
from pyproj import Geod

from ml.tracking.lifecycle import build_lifecycle, load_phase_rules
from ml.tracking.track import load_outputs, run_tracking
from pipelines.preprocess.build_cube import OUT_DIR as CUBE_DIR, build
from scripts import make_figures as mf

FIG_DIR = Path("data/figures")
MIN_TRAJ_LIFETIME_MIN = 120
NEAR_STATION_KM = 50
DEEP_K = 235.0
MIN_LIFECYCLE_MIN = 120


def select_lifecycle_cell(per_frame: pd.DataFrame, summary: pd.DataFrame, stations: list[dict]) -> tuple[int, str]:
    """Deterministic rule (v2, see docs/FIRST_EVENT.md §6): among deep-convective cells (min BT < DEEP_K) living
    >= MIN_LIFECYCLE_MIN whose track passes within NEAR_STATION_KM of a geocoded hail station, take the coldest
    cloud top (hail is associated with deep, cold tops); ties -> longest lifetime. v1 ("longest-lived") was
    dropped because it favours chained linking errors (it picked a track moving ~120 km/h)."""
    geod = Geod(ellps="WGS84")
    pts = [(s["lon"], s["lat"], s["name"]) for s in stations if s.get("lat") is not None]
    near = {}
    for cell, g in per_frame.groupby("cell"):
        best = None
        for lon, lat, name in pts:
            _, _, d = geod.inv(g["lon"].values, g["lat"].values, np.full(len(g), lon), np.full(len(g), lat))
            dmin = float(np.min(d)) / 1000
            if dmin <= NEAR_STATION_KM and (best is None or dmin < best[1]):
                best = (name, dmin)
        if best:
            near[cell] = best
    summary = summary[(summary["min_bt_K"] < DEEP_K) & (summary["lifetime_min"] >= MIN_LIFECYCLE_MIN)]
    cand = summary[summary["cell"].isin(near)]
    if len(cand):
        row = cand.sort_values(["min_bt_K", "lifetime_min"], ascending=[True, False]).iloc[0]
        name, d = near[row["cell"]]
        return int(row["cell"]), (f"rule v2: coldest deep cell living ≥ {MIN_LIFECYCLE_MIN / 60:.0f} h within "
                                  f"{NEAR_STATION_KM} km of a reported hail station (closest: {name}, {d:.0f} km)")
    row = summary.sort_values("lifetime_min", ascending=False).iloc[0]
    return int(row["cell"]), f"no deep cell within {NEAR_STATION_KM} km of a station; longest-lived deep cell shown"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()

    cube = CUBE_DIR / f"{a.event}.nc"
    if a.rebuild or not cube.exists():
        cube = build(a.event)
    out_dir = Path("data/processed") / a.event
    if a.rebuild or not (out_dir / "features.parquet").exists():
        run_tracking(cube, out_dir)
    feats, mask, ms = load_outputs(out_dir)
    ds = xr.open_dataset(cube)

    per_frame, summary = build_lifecycle(feats, ds["bt"], mask, ds.attrs["crs_proj4"], float(ds.attrs["resolution_m"]),
                                         load_phase_rules(), ms.get("cell_to_track", {}))
    per_frame.to_csv(out_dir / "cells_per_frame.csv", index=False)
    summary.to_csv(out_dir / "cells_summary.csv", index=False)

    event_cfg = yaml.safe_load(Path("config/events.yaml").read_text())[a.event]
    stations = json.loads(Path(f"data/raw/hail_reports/geocoded_{event_cfg['date']}.json").read_text())

    # Figure frame rule: the frame with the largest in-domain area colder than 221 K.
    cold = ((ds.bt < 221) & ds.in_domain).sum(("y", "x")).values
    t_idx = int(np.argmax(cold))
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    cell, note = select_lifecycle_cell(per_frame, summary, stations)
    figs = {
        "fig1_satellite_frame": mf.fig_satellite(ds, t_idx, stations, FIG_DIR / f"{a.event}_fig1_satellite_frame.png"),
        "fig2_detected_cells": mf.fig_cells(ds, mask, per_frame, t_idx, stations, FIG_DIR / f"{a.event}_fig2_detected_cells.png"),
        "fig3_trajectories": mf.fig_trajectories(ds, per_frame, summary, stations, MIN_TRAJ_LIFETIME_MIN,
                                                 FIG_DIR / f"{a.event}_fig3_trajectories.png"),
        "fig4_lifecycle": mf.fig_lifecycle(per_frame, cell, note, FIG_DIR / f"{a.event}_fig4_lifecycle_cell{cell}.png"),
    }

    run = {
        "event": a.event,
        "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cube": str(cube), "n_frames": int(ds.sizes["time"]),
        "qc_fail_frames": int((ds.qc_status.values != "OK").sum()),
        "qc_fail_times_utc": [str(pd.Timestamp(t)) for t, q in zip(ds.time.values, ds.qc_status.values) if q != "OK"],
        "residual_missing_frac_max": float(ds.qc_missing_frac.max()),
        "cells_with_frames_touching_missing": int((summary["frames_touching_missing"] > 0).sum()),
        "grid_shape_yx": [int(ds.sizes["y"]), int(ds.sizes["x"])],
        "n_features_total": int(len(feats)), "n_features_linked": int((feats["cell"] != -1).sum()),
        "n_cells": int(summary.shape[0]),
        "n_cells_ge_2h": int((summary["lifetime_min"] >= 120).sum()),
        "n_cells_reaching_221K": int((summary["min_bt_K"] < 221).sum()),
        "merge_split_status": ms["status"],
        "n_merge_split_families_gt1": int(summary.loc[summary["merge_split_family_size"] > 1, "track_family"].nunique()),
        "figure_frame_utc": str(pd.Timestamp(ds.time.values[t_idx])),
        "lifecycle_cell": cell, "lifecycle_selection": note,
        "figures": {k: str(v) for k, v in figs.items()},
    }
    (out_dir / "run_summary.json").write_text(json.dumps(run, indent=2))
    print(json.dumps(run, indent=2))


if __name__ == "__main__":
    main()
