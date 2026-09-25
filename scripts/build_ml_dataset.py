"""Phase-6 leakage-safe dataset: sampled pixel rows for the train and validation day blocks (config/ml_dataset.yaml).

  python -m scripts.build_ml_dataset            # builds missing cubes (raw files must be downloaded) and parquet rows

Rows: one pixel x one (issue frame k, lead L) of one calendar day. Features from frames <= k only; target = observed
BT(k + L) < 235 K. Sampling is stratified per (day, k, L) with inverse-probability weights, so weighted statistics
are unbiased for the full scored population (domain pixels with a valid observation). Test events are never read here.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ml.features.grid_features import FEATURES, issue_features, stack
from pipelines.preprocess.build_cube import OUT_DIR as CUBE_DIR, build_window

CFG_PATH = Path("config/ml_dataset.yaml")
OUT = Path("data/processed/ml_dataset")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def day_list(block: dict) -> list[date]:
    d0, d1 = date.fromisoformat(block["start"]), date.fromisoformat(block["end"])
    return [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]


def forbidden_days(cfg: dict) -> set[date]:
    ev = yaml.safe_load(Path("config/events.yaml").read_text())
    days = {date.fromisoformat(d) for d in cfg["splits"]["excluded_event_days"]}
    days |= {date.fromisoformat(ev[e]["date"]) for e in cfg["splits"]["test"]}
    b = cfg["splits"]["buffer_days"]
    return {d + timedelta(days=o) for d in days for o in range(-b, b + 1)}


def splits(cfg: dict) -> dict[str, list[date]]:
    s = {name: day_list(cfg["splits"][name]) for name in ("train", "validation")}
    bad = forbidden_days(cfg)
    for name, days in s.items():
        clash = sorted(set(days) & bad)
        if clash:
            raise ValueError(f"{name} block contains event days or buffers: {clash}")
    if set(s["train"]) & set(s["validation"]):
        raise ValueError("train and validation overlap")
    return s


def cube_for(d: date) -> Path:
    key = f"D{d:%Y%m%d}"
    p = CUBE_DIR / f"{key}.nc"
    if not p.exists():
        build_window(key, datetime(d.year, d.month, d.day, 0, 0), datetime(d.year, d.month, d.day, 23, 30))
    return p


def sample_issue(bt: np.ndarray, dom: np.ndarray, times: pd.DatetimeIndex, k: int, d: date, cfg: dict,
                 cfg_b: dict) -> list[pd.DataFrame]:
    """Stratified, weighted pixel sample for every lead of issue frame k on day d (deterministic seed)."""
    thr = cfg["target_bt_K"]
    caps = cfg["sampling"]["per_stratum"]
    rows = []
    for L, feats, _ in issue_features(bt, k, dom, times, cfg_b, thr):
        if k + L >= bt.shape[0]:
            break
        obs = bt[k + L]
        D = (dom & np.isfinite(obs)).ravel()
        y = (np.isfinite(obs) & (obs < thr)).ravel()
        near = ((feats["adv_frac31"] > 0) | (feats["pers_frac31"] > 0)).ravel()
        rng = np.random.default_rng([cfg["sampling"]["seed"], int(f"{d:%Y%m%d}"), k, L])
        for name, members in (("event", D & y), ("near_cold_non_event", D & ~y & near),
                              ("far_non_event", D & ~y & ~near)):
            idx = np.flatnonzero(members)
            if not len(idx):
                continue
            take = np.sort(rng.choice(idx, size=min(caps[name], len(idx)), replace=False))
            df = pd.DataFrame(stack(feats, take), columns=FEATURES)
            df["y"] = y[take].astype(np.int8)
            df["weight"] = np.float32(len(idx) / len(take))
            df["stratum"] = name
            df["pixel"] = take.astype(np.int32)
            df["issue_frame"] = np.int16(k)
            rows.append(df)
    return rows


def build_day(args) -> dict:
    d, split, cfg, cfg_b = args
    cube = cube_for(d)
    ds = xr.open_dataset(cube)
    bt, dom = ds["bt"].values, ds["in_domain"].values
    times = pd.to_datetime(ds.time.values)
    thr = cfg["target_bt_K"]
    rows = []
    for k in range(cfg_b["motion"]["n_past_frames"] - 1, bt.shape[0] - 1):
        rows += sample_issue(bt, dom, times, k, d, cfg, cfg_b)
    out = pd.concat(rows, ignore_index=True)
    out.insert(0, "day", f"{d:%Y-%m-%d}")
    out.insert(1, "split", split)
    dest = OUT / split / f"D{d:%Y%m%d}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest, index=False)
    deep = ((ds["bt"] < thr) & ds["in_domain"]).sum(("y", "x")).values
    return {"day": f"{d:%Y-%m-%d}", "split": split, "cube": str(cube), "cube_sha256": sha256(cube),
            "n_frames": int(ds.sizes["time"]), "qc_fail_frames": int((ds["qc_status"].values != "OK").sum()),
            "deep_frames_frac": float((deep > 0).mean()), "deep_area_frac_mean": float(deep.mean() / dom.sum()),
            "n_rows": len(out), "n_event_rows": int(out["y"].sum()),
            "weighted_base_rate": float((out["y"] * out["weight"]).sum() / out["weight"].sum()),
            "parquet": str(dest), "parquet_sha256": sha256(dest), "config_sha256": sha256(CFG_PATH)}


def build_day_cached(args) -> dict:
    """Reuse a day already built with the same config and unchanged parquet; otherwise build it."""
    d, split = args[0], args[1]
    rec_path = OUT / split / f"D{d:%Y%m%d}.json"
    if rec_path.exists():
        rec = json.loads(rec_path.read_text())
        if rec.get("config_sha256") == sha256(CFG_PATH) and Path(rec["parquet"]).exists() \
                and sha256(Path(rec["parquet"])) == rec["parquet_sha256"]:
            return rec
    rec = build_day(args)
    rec_path.write_text(json.dumps(rec, indent=2))
    return rec


def main() -> None:
    cfg = yaml.safe_load(CFG_PATH.read_text())
    cfg_b = yaml.safe_load(Path("config/baseline.yaml").read_text())
    s = splits(cfg)
    jobs = [(d, name, cfg, cfg_b) for name, days in s.items() for d in days]
    for d, *_ in jobs:            # build cubes serially first (netCDF writes), then features in parallel
        cube_for(d)
    with Pool(4) as pool:
        recs = pool.map(build_day_cached, jobs)
    man = {"built_at_utc": datetime.utcnow().isoformat(timespec="seconds"), "config_sha256": sha256(CFG_PATH),
           "config_baseline_sha256": sha256(Path("config/baseline.yaml")),
           "forbidden_days": sorted(str(d) for d in forbidden_days(cfg)), "days": recs}
    (OUT / "dataset_manifest.json").write_text(json.dumps(man, indent=2))
    print(pd.DataFrame(recs).drop(columns=["cube", "parquet", "cube_sha256", "parquet_sha256"]).to_string(index=False))


if __name__ == "__main__":
    main()
