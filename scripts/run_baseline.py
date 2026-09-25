"""Phase-2 baseline run: 0-6 h persistence and pySTEPS advection forecasts on the Phase-1 event, evaluated
against the observed satellite evolution.

  python -m scripts.run_baseline --event E8_20260514

Inputs (Phase-1 outputs, read-only): data/interim/grid2km/<event>.nc, data/processed/<event>/features.parquet,
mask.nc. Outputs: data/processed/<event>/baseline/ (forecasts, motion, object predictions, metrics, provenance).
Nothing is fitted: both baselines have no trainable parameters, and settings are fixed in config/baseline.yaml.
Every forecast issued at frame k reads only frames <= k (time-ordered; no pixel or random splits).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ml.forecasting.baselines import advection_grid, object_forecasts, persistence_grid, shifted_iou
from ml.verification.scores import FSSAccumulator, cat_scores, contingency

METHODS = ("persistence", "pysteps_advection")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(event: str) -> dict:
    cfg = yaml.safe_load(Path("config/baseline.yaml").read_text())
    cube_path = Path(f"data/interim/grid2km/{event}.nc")
    proc = Path(f"data/processed/{event}")
    out = proc / "baseline"
    out.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(cube_path)
    bt = ds["bt"].values
    in_dom = ds["in_domain"].values
    times = pd.to_datetime(ds.time.values)
    step_min = int((times[1] - times[0]).total_seconds() // 60)
    if step_min != cfg["cadence_min"]:
        raise ValueError(f"cube cadence {step_min} min != config {cfg['cadence_min']} min")
    n_t, n_lead = bt.shape[0], cfg["max_lead_steps"]
    thr = cfg["event"]["bt_threshold_K"]
    scales = cfg["fss_scales_px"]
    dxy = float(ds.attrs["resolution_m"])
    issues = list(range(cfg["motion"]["n_past_frames"] - 1, n_t - 1))  # need 3 past frames and >= 1 future frame

    # ---- grid forecasts + scoring ----
    adv_store = np.full((len(issues), n_lead) + bt.shape[1:], np.nan, dtype=np.float32)
    vel_store = np.zeros((len(issues), 2) + bt.shape[1:], dtype=np.float32)
    pooled = {(m, L): {"H": 0, "M": 0, "F": 0, "CN": 0} for m in METHODS for L in range(1, n_lead + 1)}
    fss = {(m, L, s): FSSAccumulator(s) for m in METHODS for L in range(1, n_lead + 1) for s in scales}
    per_issue, excluded = [], {L: [] for L in range(1, n_lead + 1)}
    for i, k in enumerate(issues):
        fc_p = persistence_grid(bt, k, n_lead)
        fc_a, vel = advection_grid(bt, k, n_lead, cfg)
        adv_store[i], vel_store[i] = fc_a, vel
        for L in range(1, n_lead + 1):
            if k + L >= n_t:
                break
            obs = bt[k + L]
            # Like-for-like: both methods scored on pixels valid for obs AND both forecasts, inside the domain.
            valid = in_dom & np.isfinite(obs) & np.isfinite(fc_p[L - 1]) & np.isfinite(fc_a[L - 1])
            excluded[L].append(1.0 - valid.sum() / in_dom.sum())
            obs_ev = np.isfinite(obs) & (obs < thr)
            for m, fc in (("persistence", fc_p[L - 1]), ("pysteps_advection", fc_a[L - 1])):
                fc_ev = np.isfinite(fc) & (fc < thr)
                ct = contingency(fc_ev, obs_ev, valid)
                for key in ct:
                    pooled[(m, L)][key] += ct[key]
                for s in scales:
                    fss[(m, L, s)].add(fc_ev, obs_ev, valid)
                one = FSSAccumulator(scales[1]); one.add(fc_ev, obs_ev, valid)
                per_issue.append({"method": m, "issue_time_utc": str(times[k]), "lead_min": L * step_min,
                                  **ct, **cat_scores(**ct), f"FSS_{scales[1] * dxy / 1000:.0f}km": one.fss()})

    grid_rows = []
    for m in METHODS:
        for L in range(1, n_lead + 1):
            ct = pooled[(m, L)]
            row = {"method": m, "lead_min": L * step_min, "n_issue_times": len(excluded[L]),
                   "n_scored_pixels": ct["H"] + ct["M"] + ct["F"] + ct["CN"],
                   "excluded_frac_mean": float(np.mean(excluded[L])), **ct, **cat_scores(**ct)}
            for s in scales:
                acc = fss[(m, L, s)]
                row[f"FSS_{s * dxy / 1000:.0f}km"] = acc.fss()
                row[f"FSS_useful_threshold_{s * dxy / 1000:.0f}km"] = acc.uniform_target()
            grid_rows.append(row)
    grid_df = pd.DataFrame(grid_rows)
    grid_df.to_csv(out / "grid_metrics_by_lead.csv", index=False)
    pd.DataFrame(per_issue).to_csv(out / "grid_metrics_per_issue.csv", index=False)

    # Predictions: advection forecasts stored (0.01 K int16); persistence(t+L) is by definition the observed frame
    # at the issue time, already in the cube, so it is referenced rather than duplicated.
    fc_ds = xr.Dataset(
        {"bt_forecast": (("issue_time", "lead_min", "y", "x"), adv_store,
                         {"units": "K", "method": "pySTEPS Lucas-Kanade + semi-Lagrangian (config/baseline.yaml)"}),
         "velocity_px_per_step": (("issue_time", "component", "y", "x"), vel_store)},
        coords={"issue_time": times[issues].values, "lead_min": np.arange(1, n_lead + 1) * step_min,
                "component": ["x", "y"], "y": ds.y.values, "x": ds.x.values},
        attrs={"persistence": "forecast(issue_time, lead) = cube bt(issue_time) for every lead", "cube": str(cube_path)})
    enc = {"bt_forecast": {"dtype": "int16", "scale_factor": 0.01, "add_offset": 250.0, "_FillValue": -32768, "zlib": True},
           "velocity_px_per_step": {"zlib": True}}
    fc_ds.to_netcdf(out / "advection_forecasts.nc", encoding=enc)

    # ---- object baselines ----
    feats = pd.read_parquet(proc / "features.parquet")
    obj = object_forecasts(feats, n_lead, cfg["objects"]["velocity_window_steps"], dxy)
    # Same sample for every object method: issue frames that have a pySTEPS motion field (k >= n_past - 1).
    obj = obj[obj["issue_frame"].isin(issues)].copy()
    # Third object baseline (research Part 11 "pySTEPS field motion"): the LK motion field at issue time,
    # sampled at the cell's position, extrapolated at constant velocity.
    fa = obj[obj["method"] == "persistence"].copy()
    idx = {k: i for i, k in enumerate(issues)}
    iy = np.clip(np.round(fa["y0"].values / dxy).astype(int), 0, bt.shape[1] - 1)
    ix = np.clip(np.round(fa["x0"].values / dxy).astype(int), 0, bt.shape[2] - 1)
    ii = fa["issue_frame"].map(idx).values
    u = vel_store[ii, 0, iy, ix] * dxy
    v = vel_store[ii, 1, iy, ix] * dxy
    fa["method"] = "field_advection"
    fa["pred_x"] = fa["x0"] + u * fa["lead_steps"]
    fa["pred_y"] = fa["y0"] + v * fa["lead_steps"]
    fa["centroid_err_km"] = np.hypot(fa["pred_x"] - fa["obs_x"], fa["pred_y"] - fa["obs_y"]) / 1000.0
    obj = pd.concat([obj, fa], ignore_index=True)
    mask = xr.open_dataset(proc / "mask.nc")["segment_label"].values
    ious = []
    for r in obj.itertuples(index=False):
        if not r.survived:
            ious.append(np.nan); continue
        m_t = mask[r.issue_frame] == r.issue_feature
        m_o = mask[r.issue_frame + r.lead_steps] == r.obs_feature
        if not (m_t.any() and m_o.any()):
            ious.append(np.nan); continue  # IoU only for cells segmented (< 245 K) at both times
        shift = (int(round((r.pred_y - r.y0) / dxy)), int(round((r.pred_x - r.x0) / dxy)))
        ious.append(shifted_iou(m_t, m_o, shift))
    obj["iou"] = ious
    obj["lead_min"] = obj["lead_steps"] * step_min
    obj.to_csv(out / "object_predictions.csv", index=False)

    obj_rows = []
    for (m, L), g in obj.groupby(["method", "lead_min"]):
        s = g[g["survived"]]
        e = s["centroid_err_km"]
        iou = s["iou"].dropna()
        obj_rows.append({"method": m, "lead_min": L, "n_cell_issues": len(g), "n_survived": len(s),
                         "survival_frac": len(s) / len(g),
                         "centroid_err_km_median": e.median(), "centroid_err_km_p25": e.quantile(0.25),
                         "centroid_err_km_p75": e.quantile(0.75), "centroid_err_km_mean": e.mean(),
                         "n_iou": len(iou), "iou_median": iou.median() if len(iou) else np.nan,
                         "iou_mean": iou.mean() if len(iou) else np.nan})
    obj_df = pd.DataFrame(obj_rows).sort_values(["method", "lead_min"])
    obj_df.to_csv(out / "object_metrics_by_lead.csv", index=False)

    prov = {
        "event": event, "run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {str(p): sha256(p) for p in [cube_path, proc / "features.parquet", proc / "mask.nc",
                                               Path("config/baseline.yaml")]},
        "outputs": {p.name: sha256(p) for p in sorted(out.glob("*.csv"))},
        "issue_times_utc": [str(times[k]) for k in issues],
        "n_issue_times": len(issues), "leads_min": [L * step_min for L in range(1, n_lead + 1)],
        "fitted_parameters": "none (baselines only; no training, no tuning)",
        "versions": {p: version(p) for p in ["pysteps", "opencv-python-headless", "numpy", "scipy", "xarray", "tobac"]},
        "pysteps_build_note": "pysteps 1.21.5 built from the PyPI sdist with -fopenmp removed from setup.py (Apple clang "
                              "has no OpenMP); affects only multithreading of the Proesmans/VET C extensions, which are "
                              "not used here. Lucas-Kanade and semi-Lagrangian code paths are unmodified.",
    }
    (out / "baseline_provenance.json").write_text(json.dumps(prov, indent=2))
    return {"grid": grid_df, "objects": obj_df, "provenance": prov}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    r = run(ap.parse_args().event)
    cols = ["method", "lead_min", "n_issue_times", "excluded_frac_mean", "POD", "FAR", "CSI", "bias", "FSS_20km", "FSS_40km"]
    print(r["grid"][cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(r["objects"][["method", "lead_min", "n_survived", "survival_frac", "centroid_err_km_median", "n_iou", "iou_median"]]
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))


if __name__ == "__main__":
    main()
