"""Phase-3 tracking v2: overlap linking of cold segments -> lifecycle -> object diagnostics.

  python -m scripts.run_tracking_v2 --event E8_20260514 --mode none    # Eulerian overlap
  python -m scripts.run_tracking_v2 --event E8_20260514 --mode flow    # overlap after shifting by pySTEPS flow

Reads Phase-1 features/mask/cube and Phase-2 motion fields (read-only). Writes data/processed/<event>/tracking_v2_<mode>/.
Object diagnostics reuse the Phase-2 baseline definitions (persistence, constant velocity, field advection) and the
Phase-2 motion fields; grid metrics are not touched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ml.forecasting.baselines import object_forecasts_from_positions, shifted_iou
from ml.tracking.lifecycle import build_lifecycle, load_phase_rules
from ml.tracking.overlap_link import LinkConfig, families, track

DXY = 2000.0


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def object_diagnostics(pos: pd.DataFrame, mask: np.ndarray, vel_store: np.ndarray, issues: list[int],
                       n_lead: int, window: int, step_min: int, shape: tuple) -> tuple[pd.DataFrame, pd.DataFrame]:
    obj = object_forecasts_from_positions(pos, n_lead, window)
    obj = obj[obj["issue_frame"].isin(issues)].copy()
    fa = obj[obj["method"] == "persistence"].copy()
    idx = {k: i for i, k in enumerate(issues)}
    iy = np.clip(np.round(fa["y0"].values / DXY).astype(int), 0, shape[0] - 1)
    ix = np.clip(np.round(fa["x0"].values / DXY).astype(int), 0, shape[1] - 1)
    ii = fa["issue_frame"].map(idx).values
    fa["method"] = "field_advection"
    fa["pred_x"] = fa["x0"] + vel_store[ii, 0, iy, ix] * DXY * fa["lead_steps"]
    fa["pred_y"] = fa["y0"] + vel_store[ii, 1, iy, ix] * DXY * fa["lead_steps"]
    fa["centroid_err_km"] = np.hypot(fa["pred_x"] - fa["obs_x"], fa["pred_y"] - fa["obs_y"]) / 1000.0
    obj = pd.concat([obj, fa], ignore_index=True)
    ious = []
    for r in obj.itertuples(index=False):
        if not r.survived:
            ious.append(np.nan); continue
        m_t, m_o = mask[r.issue_frame] == r.issue_feature, mask[r.issue_frame + r.lead_steps] == r.obs_feature
        shift = (int(round((r.pred_y - r.y0) / DXY)), int(round((r.pred_x - r.x0) / DXY)))
        ious.append(shifted_iou(m_t, m_o, shift) if (m_t.any() and m_o.any()) else np.nan)
    obj["iou"] = ious
    obj["lead_min"] = obj["lead_steps"] * step_min
    rows = []
    for (m, L), g in obj.groupby(["method", "lead_min"]):
        s = g[g["survived"]]
        e, iou = s["centroid_err_km"], s["iou"].dropna()
        rows.append({"method": m, "lead_min": L, "n_cell_issues": len(g), "n_survived": len(s),
                     "n_distinct_cells": s["cell"].nunique(), "survival_frac": len(s) / len(g) if len(g) else np.nan,
                     "centroid_err_km_median": e.median(), "centroid_err_km_p25": e.quantile(0.25),
                     "centroid_err_km_p75": e.quantile(0.75), "n_iou": len(iou),
                     "iou_median": iou.median() if len(iou) else np.nan})
    return obj, pd.DataFrame(rows).sort_values(["method", "lead_min"])


def paired_comparison(obj: pd.DataFrame) -> pd.DataFrame:
    """Per lead: on identical (cell, issue) pairs, fraction where field_advection error < persistence error,
    with the number of distinct cells (pairs from one cell are not independent)."""
    s = obj[obj["survived"]].pivot_table(index=["cell", "issue_frame", "lead_min"], columns="method",
                                         values="centroid_err_km").dropna().reset_index()
    out = []
    for L, g in s.groupby("lead_min"):
        out.append({"lead_min": L, "n_pairs": len(g), "n_distinct_cells": g["cell"].nunique(),
                    "frac_field_better_than_persistence": float((g["field_advection"] < g["persistence"]).mean()),
                    "frac_cv_better_than_persistence": float((g["constant_velocity"] < g["persistence"]).mean()),
                    "median_err_diff_field_minus_persistence_km": float((g["field_advection"] - g["persistence"]).median())})
    return pd.DataFrame(out)


def run(event: str, mode: str, min_overlap: float | None = None) -> dict:
    cfg_t = yaml.safe_load(Path("config/tracking_v2.yaml").read_text())
    suffix = ""
    if min_overlap is not None and min_overlap != cfg_t["min_overlap_frac"]:
        cfg_t["min_overlap_frac"] = min_overlap  # sensitivity run only; the declared value stays in config
        suffix = f"_ov{min_overlap:g}"
    cfg_b = yaml.safe_load(Path("config/baseline.yaml").read_text())
    p = Path(f"data/processed/{event}")
    out = p / f"tracking_v2_{mode}{suffix}"
    out.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(f"data/interim/grid2km/{event}.nc")
    mask_da = xr.open_dataset(p / "mask.nc")["segment_label"]
    mask = mask_da.values
    feats = pd.read_parquet(p / "features.parquet")
    fc = xr.open_dataset(p / "baseline/advection_forecasts.nc")
    V = fc["velocity_px_per_step"].values
    vel = {i + 2: V[i] for i in range(V.shape[0])}

    seg_ids = set(np.unique(mask)) - {0}
    seg_feats = feats[feats["feature"].isin(seg_ids)].copy()
    frames_features = {int(k): sorted(g["feature"].astype(int).tolist()) for k, g in seg_feats.groupby("frame")}
    for k in range(ds.sizes["time"]):
        frames_features.setdefault(k, [])
    lcfg = LinkConfig(mode=mode, min_overlap_frac=cfg_t["min_overlap_frac"])
    assign, events = track(mask, frames_features, vel, lcfg)

    # Keep cells with >= min_frames (same stub rule as Phase 1).
    life = assign.groupby("cell")["frame"].size()
    keep = life[life >= cfg_t["min_frames"]].index
    assign = assign[assign["cell"].isin(keep)]
    fams = families(events[events["from_cell"].isin(keep) & events["into_cell"].isin(keep)], sorted(keep))
    v2 = seg_feats.drop(columns=["cell"]).merge(assign[["feature", "cell"]], on="feature", how="inner")

    per_frame, summary = build_lifecycle(v2, ds["bt"], mask_da, ds.attrs["crs_proj4"], DXY, load_phase_rules(),
                                         {str(c): f for c, f in fams.items()}, centroid=cfg_t["centroid"])
    per_frame.to_csv(out / "cells_per_frame.csv", index=False)
    summary.to_csv(out / "cells_summary.csv", index=False)
    events.to_csv(out / "genealogy_events.csv", index=False)

    pos = per_frame.assign(x=per_frame["cx_idx"] * DXY, y=per_frame["cy_idx"] * DXY)[["cell", "frame", "feature", "x", "y"]]
    issues = [int(k) for k in range(cfg_b["motion"]["n_past_frames"] - 1, ds.sizes["time"] - 1)]
    obj, obj_sum = object_diagnostics(pos, mask, V, issues, cfg_b["max_lead_steps"],
                                      cfg_b["objects"]["velocity_window_steps"], cfg_b["cadence_min"], mask.shape[1:])
    obj.to_csv(out / "object_predictions.csv", index=False)
    obj_sum.to_csv(out / "object_metrics_by_lead.csv", index=False)
    paired = paired_comparison(obj)
    paired.to_csv(out / "object_paired_comparison.csv", index=False)

    run_info = {
        "event": event, "mode": mode, "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": cfg_t, "n_segmented_features": int(len(seg_feats)), "n_cells": int(summary.shape[0]),
        "n_cells_ge_2h": int((summary["lifetime_min"] >= 120).sum()),
        "n_merge_events": int((events["type"] == "MERGE").sum()), "n_split_events": int((events["type"] == "SPLIT").sum()),
        "n_families_gt1": int(pd.Series(fams).value_counts().gt(1).sum()),
        "inputs": {str(x): sha256(x) for x in [Path(f"data/interim/grid2km/{event}.nc"), p / "features.parquet",
                                                p / "mask.nc", p / "baseline/advection_forecasts.nc",
                                                Path("config/tracking_v2.yaml"), Path("config/baseline.yaml")]},
        "outputs": {x.name: sha256(x) for x in sorted(out.glob("*.csv"))},
    }
    (out / "run_summary.json").write_text(json.dumps(run_info, indent=2))
    return {"run": run_info, "obj": obj_sum, "paired": paired}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    ap.add_argument("--mode", choices=["none", "flow"], default="none")
    ap.add_argument("--min-overlap", type=float, default=None, help="sensitivity run (writes a suffixed directory)")
    a = ap.parse_args()
    r = run(a.event, a.mode, a.min_overlap)
    print(json.dumps({k: v for k, v in r["run"].items() if k not in ("inputs", "outputs")}, indent=1, default=str))
    print(r["obj"][["method", "lead_min", "n_survived", "n_distinct_cells", "centroid_err_km_median", "n_iou", "iou_median"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print(r["paired"].to_string(index=False, float_format=lambda v: f"{v:.2f}"))


if __name__ == "__main__":
    main()
