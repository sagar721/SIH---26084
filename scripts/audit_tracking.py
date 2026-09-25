"""Phase-3 tracking audit on E8. Writes data/processed/<event>/audit/.

  python -m scripts.audit_tracking --event E8_20260514 --version v1          # audit Phase-1 tobac tracks
  python -m scripts.audit_tracking --event E8_20260514 --version v2_none     # audit a Phase-3 track version

Motion fields are the Phase-2 pySTEPS fields (frame k uses frames <= k); they are used only as an independent
reference for motion consistency, never to create truth.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from ml.tracking.audit import link_overlap, steps, summarize, zigzag_fraction

DXY = 2000.0


def load_common(event: str):
    p = Path(f"data/processed/{event}")
    mask = xr.open_dataset(p / "mask.nc")["segment_label"].values
    V = xr.open_dataset(p / "baseline/advection_forecasts.nc")["velocity_px_per_step"].values
    vel = {i + 2: V[i] for i in range(V.shape[0])}  # issue index i <-> frame i + 2 (see BASELINE_EVAL §1)
    return p, mask, vel


def positions(event: str, version: str) -> pd.DataFrame:
    p = Path(f"data/processed/{event}")
    if version == "v1":
        f = pd.read_parquet(p / "features.parquet")
        f = f[f["cell"] != -1]
        return f.assign(x=f["hdim_2"] * DXY, y=f["hdim_1"] * DXY)[["cell", "frame", "feature", "x", "y", "threshold_value"]]
    t = pd.read_csv(p / f"tracking_{version}" / "cells_per_frame.csv")  # e.g. v2_none, v2_none_ov0.1
    return t.assign(x=t["cx_idx"] * DXY, y=t["cy_idx"] * DXY)[["cell", "frame", "feature", "x", "y"]]


def v1_extra(event: str, pos: pd.DataFrame, mask: np.ndarray) -> dict:
    """Cause analysis specific to the tobac v1 tracks."""
    p = Path(f"data/processed/{event}")
    seg = set(np.unique(mask)) - {0}
    s = steps(pos)
    s["thr_prev"] = s.groupby("cell")["threshold_value"].shift()
    thr_step = pos.sort_values(["cell", "frame"]).groupby("cell")["threshold_value"].diff().abs() > 0
    pos = pos.sort_values(["cell", "frame"]).assign(thr_change=thr_step.values)
    s = s.merge(pos[["cell", "frame", "thr_change"]], on=["cell", "frame"])
    s["seg_par"] = s["prev_feature"].isin(seg)
    s["seg_chi"] = s["feature"].isin(seg)
    kinds = s.groupby([s["seg_par"], s["seg_chi"]]).size().rename(index={True: "seg", False: "warm"}).to_dict()
    # merge_split_MEST families: maximum distance between members present at the same frame.
    ms = json.loads((p / "merge_split.json").read_text())["cell_to_track"]
    pos["family"] = pos["cell"].astype(str).map(ms)
    spread = []
    for fam, g in pos.groupby("family"):
        if g["cell"].nunique() < 2:
            continue
        for _, gf in g.groupby("frame"):
            if len(gf) > 1:
                xy = gf[["x", "y"]].values / 1000.0
                d = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1)).max()
                spread.append(d)
    return {
        "step_kinds": {f"{a}->{b}": int(n) for (a, b), n in kinds.items()},
        "warm_feature_share_of_rows": float((~pos["feature"].isin(seg)).mean()),
        "thr_level_change_frac_of_steps": float(s["thr_change"].mean()),
        "median_step_km_thr_change": float(s.loc[s["thr_change"], "disp_km"].median()),
        "median_step_km_no_thr_change": float(s.loc[~s["thr_change"], "disp_km"].median()),
        "mest_families_multi": int(sum(1 for _, g in pos.groupby("family") if g["cell"].nunique() > 1)),
        "mest_simultaneous_member_spread_km_median": float(np.median(spread)) if spread else float("nan"),
        "mest_simultaneous_member_spread_km_p90": float(np.quantile(spread, 0.9)) if spread else float("nan"),
        "mest_simultaneous_member_spread_km_max": float(np.max(spread)) if spread else float("nan"),
    }


def suspicious_tracks(pos: pd.DataFrame, mask: np.ndarray, vel: dict, top: int = 15) -> pd.DataFrame:
    """Per-cell flags; ranked by the number of problem steps (for manual inspection)."""
    s = steps(pos).sort_values(["cell", "frame"])
    s["pdx"], s["pdy"] = s.groupby("cell")["dx_km"].shift(), s.groupby("cell")["dy_km"].shift()
    pd_ = np.hypot(s["pdx"], s["pdy"])
    cos = (s["dx_km"] * s["pdx"] + s["dy_km"] * s["pdy"]) / (s["disp_km"] * pd_)
    s["reversal"] = (cos < 0) & (s["disp_km"] >= 4) & (pd_ >= 4)
    lo = link_overlap(pos, mask, vel, DXY)
    per = s.groupby("cell").agg(n_steps=("frame", "size"), reversals=("reversal", "sum"),
                                max_step_km=("disp_km", "max"), first_frame=("frame", "min"))
    if len(lo):
        lo_c = lo.groupby("cell").agg(seg_links=("frame", "size"), id_switch_candidates=("better_other_none", "sum"),
                                      zero_overlap_links=("ov_none_linked_frac", lambda v: int((v == 0).sum())))
        per = per.join(lo_c, how="left").fillna({"seg_links": 0, "id_switch_candidates": 0, "zero_overlap_links": 0})
    per["problem_score"] = per["reversals"] + per.get("id_switch_candidates", 0) + per.get("zero_overlap_links", 0)
    return per.sort_values(["problem_score", "n_steps"], ascending=False).head(top).reset_index()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    ap.add_argument("--version", default="v1")
    a = ap.parse_args()
    p, mask, vel = load_common(a.event)
    out = p / "audit"
    out.mkdir(exist_ok=True)
    pos = positions(a.event, a.version)
    seg = set(np.unique(mask)) - {0}
    res = {"all_cells": summarize(pos, mask, vel, DXY, f"{a.version} all cells"),
           "segmented_rows_only": summarize(pos[pos["feature"].isin(seg)], mask, vel, DXY, f"{a.version} segmented rows")}
    if a.version == "v1":
        res["v1_causes"] = v1_extra(a.event, pos, mask)
    (out / f"audit_{a.version}.json").write_text(json.dumps(res, indent=2))
    suspicious_tracks(pos, mask, vel).to_csv(out / f"suspicious_tracks_{a.version}.csv", index=False)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
