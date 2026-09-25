"""Storm-cell detection, segmentation, linking and merge/split with tobac (ARCHITECTURE.md §3, stages 4-5).

Input: BT cube from ``pipelines.preprocess.build_cube``. Output (``data/processed/<event>/``):
  features.parquet  - one row per detected feature (tobac output + cell id)
  mask.nc           - segmentation labels per frame (feature id), threshold from config/tracking.yaml
  merge_split.json  - tobac merge_split_MEST grouping of cells into tracks (families)
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import tobac
import xarray as xr
import yaml

log = logging.getLogger(__name__)


def load_cfg(path: Path = Path("config/tracking.yaml")) -> dict:
    return yaml.safe_load(path.read_text())


def run_tracking(cube_path: Path, out_dir: Path, cfg: dict | None = None) -> dict[str, Path]:
    cfg = cfg or load_cfg()
    ds = xr.open_dataset(cube_path)
    dxy = float(ds.attrs["resolution_m"])
    dt = float((ds.time.values[1] - ds.time.values[0]) / np.timedelta64(1, "s"))
    # Pixels outside the lat/lon domain box are masked so no cell is seeded there.
    bt = ds["bt"].where(ds["in_domain"])

    features = tobac.feature_detection_multithreshold(
        bt, dxy=dxy, threshold=cfg["feature_thresholds_K"], target="minimum",
        position_threshold=cfg["position_threshold"], sigma_threshold=cfg["sigma_threshold"],
        n_min_threshold=cfg["n_min_threshold_px"],
    )
    if features is None or len(features) == 0:
        raise RuntimeError("no features detected")

    mask, features = tobac.segmentation_2D(
        features, bt, dxy=dxy, threshold=cfg["segmentation_threshold_K"], target="minimum",
    )
    tracks = tobac.linking_trackpy(
        features, bt, dt=dt, dxy=dxy, v_max=cfg["v_max_m_s"], memory=cfg["memory_frames"],
        stubs=cfg["stubs_frames"], method_linking=cfg["method_linking"],
        subnetwork_size=cfg.get("subnetwork_size_max"),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {"features": out_dir / "features.parquet", "mask": out_dir / "mask.nc",
             "merge_split": out_dir / "merge_split.json"}
    tracks.to_parquet(paths["features"])
    mask.rename("segment_label").to_dataset().to_netcdf(paths["mask"], encoding={"segment_label": {"zlib": True}})

    linked = tracks[tracks["cell"] != -1]
    try:
        ms = tobac.merge_split.merge_split_MEST(linked, dxy=dxy, distance=cfg["merge_split_distance_m"])
        cell_to_track = {int(c): int(t) for c, t in zip(ms["cell"].values, ms["cell_parent_track_id"].values)}
        status = "OK"
    except Exception as exc:  # recorded, not hidden: FIRST_EVENT.md reports the status
        log.warning("merge_split_MEST failed: %s", exc)
        cell_to_track, status = {}, f"FAILED: {exc}"
    paths["merge_split"].write_text(json.dumps({"status": status, "cell_to_track": cell_to_track}, indent=2))
    return paths


def load_outputs(out_dir: Path) -> tuple[pd.DataFrame, xr.DataArray, dict]:
    feats = pd.read_parquet(out_dir / "features.parquet")
    mask = xr.open_dataset(out_dir / "mask.nc")["segment_label"]
    ms = json.loads((out_dir / "merge_split.json").read_text())
    return feats, mask, ms
