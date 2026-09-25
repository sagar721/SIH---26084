"""Phase-8 replay bundle for the web prototype (REPLAY_SPEC §4, §7). Reads FROZEN outputs only; computes no new
science. Every input's SHA-256 is checked against docs/FREEZE_ml-v0.json before it is read.

  python -m pipelines.replay.build_bundle --event E8_20260514      # also E10_20260504, E11_20260516

Writes apps/web/public/bundles/<event>/:
  manifest.json        frames, issues, leads, display grid, envelope, input/output hashes
  obs/fKK.png          observed BT at frame KK (8-bit code: BT-160 K, 255 = no data), Web-Mercator display grid
  fc/pysteps_iII_lLLL.png, fc/ml_iII_lLLL.png   pySTEPS BT and ML probability (p*250, 255 = no data) per issue/lead
  cells/fKK.geojson    v2 cell polygons at frame KK (phase, min BT, area, motion, age so far)
  contours/fKK.geojson observed BT < 235 K outlines at frame KK
  tracks.json, cellfc/iII.json, scores.json, skill.json, health.json, places.json, alerts.json
Display resampling (LAEA 2 km -> Web-Mercator-aligned image, nearest neighbour) is for drawing only.
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
from PIL import Image
from pyproj import Transformer
from skimage.measure import approximate_polygon, find_contours

FREEZE = Path("docs/FREEZE_ml-v0.json")
WEB = Path("apps/web/public/bundles")
LEADS = [30, 60, 120, 180, 240, 360]          # REPLAY_SPEC lead set; 15 min is not produced (30-min source)
BBOX = (72.0, 26.0, 84.0, 34.0)               # frozen domain (config/domain.yaml)
WIDTH = 560
THR = 235.0
ALERT_P, ALERT_RADIUS_PX, ALERT_LEADS = 0.5, 5, (30, 60)
METHODS = ["persistence", "pysteps_advection", "pysteps_np31", "ml"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Frozen:
    """Opens frozen files only after checking their hash against the freeze manifest."""
    def __init__(self):
        self.files = json.loads(FREEZE.read_text())["files"]
        self.used: dict[str, str] = {}

    def path(self, p: str) -> Path:
        if p not in self.files:
            raise KeyError(f"{p} is not in the freeze manifest")
        d = sha256(Path(p))
        if d != self.files[p]:
            raise ValueError(f"{p} changed after the Phase-7 freeze")
        self.used[p] = d
        return Path(p)


def display_grid(ds: xr.Dataset) -> dict:
    """Nearest-neighbour index map from a Web-Mercator-aligned image over BBOX to the LAEA source grid."""
    w, s, e, n = BBOX
    merc = lambda lat: np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    H = int(round(WIDTH * (merc(n) - merc(s)) / np.radians(e - w)))
    lon = w + (np.arange(WIDTH) + 0.5) / WIDTH * (e - w)
    ym = merc(n) - (np.arange(H) + 0.5) / H * (merc(n) - merc(s))
    lat = np.degrees(2 * np.arctan(np.exp(ym)) - np.pi / 2)
    LON, LAT = np.meshgrid(lon, lat)
    tr = Transformer.from_crs("EPSG:4326", ds.attrs["crs_proj4"], always_xy=True)
    X, Y = tr.transform(LON, LAT)
    x0, y0, dx = float(ds.x[0]), float(ds.y[0]), float(ds.attrs["resolution_m"])
    col = np.round((X - x0) / dx).astype(int)
    row = np.round((Y - y0) / dx).astype(int)
    ok = (col >= 0) & (col < ds.sizes["x"]) & (row >= 0) & (row < ds.sizes["y"])
    col, row = np.clip(col, 0, ds.sizes["x"] - 1), np.clip(row, 0, ds.sizes["y"] - 1)
    ok &= ds["in_domain"].values[row, col]
    return {"row": row, "col": col, "ok": ok, "width": WIDTH, "height": H,
            "bounds": {"west": w, "south": s, "east": e, "north": n}}


def to_png(field: np.ndarray, g: dict, kind: str, path: Path) -> None:
    v = field[g["row"], g["col"]]
    if kind == "bt":
        code = np.clip(np.round(v - 160.0), 0, 254)
    else:
        code = np.clip(np.round(v * 250.0), 0, 250)
    code = np.where(g["ok"] & np.isfinite(v), code, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(code, mode="L").save(path, optimize=True)


def rings(mask2d: np.ndarray, ds: xr.Dataset, to_ll, tol: float, min_pts: int = 4) -> list[list[list[float]]]:
    pad = np.pad(mask2d.astype(np.uint8), 1)
    x0, y0, dx = float(ds.x[0]), float(ds.y[0]), float(ds.attrs["resolution_m"])
    out = []
    for c in find_contours(pad, 0.5):
        c = approximate_polygon(c - 1.0, tolerance=tol)
        if len(c) < min_pts:
            continue
        lon, lat = to_ll(x0 + c[:, 1] * dx, y0 + c[:, 0] * dx)
        out.append([[round(float(a), 4), round(float(b), 4)] for a, b in zip(lon, lat)])
    return out


def reliability_bins(rel: pd.DataFrame) -> list[dict]:
    """Aggregate the frozen 10-bin reliability counts into the calibration lead bins; ECE = sum|sum_p - sum_o| / n."""
    out = []
    for lo, hi in [(30, 30), (60, 60), (90, 120), (150, 360)]:
        for m, g in rel[(rel["lead_min"] >= lo) & (rel["lead_min"] <= hi)].groupby("method"):
            b = g.groupby("bin")[["n", "sum_p", "sum_o"]].sum()
            b = b[b["n"] > 0]
            out.append({"method": m, "lead_bin": f"{lo}-{hi}", "ece": float((b["sum_p"] - b["sum_o"]).abs().sum() / b["n"].sum()),
                        "bins": [{"bin": int(k), "n": int(r.n), "mean_p": float(r.sum_p / r.n), "obs_freq": float(r.sum_o / r.n)}
                                 for k, r in b.iterrows()]})
    return out


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, separators=(",", ":"), allow_nan=False))


def clean(v):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v


def build(event: str) -> Path:
    fz = Frozen()
    out = WEB / event
    ev_cfg = yaml.safe_load(fz.path("config/events.yaml").read_text())[event]
    ds = xr.open_dataset(fz.path(f"data/interim/grid2km/{event}.nc"))
    mask = xr.open_dataset(fz.path(f"data/processed/{event}/mask.nc"))["segment_label"].values
    fc = xr.open_dataset(fz.path(f"data/processed/{event}/baseline/advection_forecasts.nc"))
    pm = xr.open_dataset(fz.path(f"data/processed/ml_eval/ml-v0/ml_probabilities_{event}.nc"))
    cpf = pd.read_csv(fz.path(f"data/processed/{event}/tracking_v2_none/cells_per_frame.csv"))
    opred = pd.read_csv(fz.path(f"data/processed/{event}/tracking_v2_none/object_predictions.csv"))
    gen = pd.read_csv(fz.path(f"data/processed/{event}/tracking_v2_none/genealogy_events.csv"))
    per = pd.read_csv(fz.path("data/processed/ml_eval/ml-v0/per_issue.csv"))
    card = json.loads(fz.path("data/models/ml-v0/model_card.json").read_text())
    times = pd.to_datetime(ds.time.values)
    issues = pd.to_datetime(pm.issue_time.values)
    issue_frames = [int(np.where(ds.time.values == t)[0][0]) for t in pm.issue_time.values]
    lead_idx = {int(L): j for j, L in enumerate(pm.lead_min.values)}
    g = display_grid(ds)
    to_ll = Transformer.from_crs(ds.attrs["crs_proj4"], "EPSG:4326", always_xy=True).transform
    bt = ds["bt"].values
    dom = ds["in_domain"].values
    x0, y0, dx = float(ds.x[0]), float(ds.y[0]), float(ds.attrs["resolution_m"])

    pcache: dict[int, dict[int, np.ndarray]] = {}

    def p_ml(i: int, L: int) -> np.ndarray:
        if i not in pcache:
            pcache.clear()
            pcache[i] = {LL: pm["p_ml"].isel(issue_time=i, lead_min=lead_idx[LL]).values for LL in LEADS}
        return pcache[i][L]

    # ---- rasters ----
    for k in range(len(times)):
        to_png(bt[k], g, "bt", out / f"obs/f{k:02d}.png")
    fcb = fc["bt_forecast"]
    for i in range(len(issues)):
        for L in LEADS:
            to_png(fcb.isel(issue_time=i, lead_min=lead_idx[L]).values, g, "bt", out / f"fc/pysteps_i{i:02d}_l{L:03d}.png")
            to_png(p_ml(i, L), g, "p", out / f"fc/ml_i{i:02d}_l{L:03d}.png")

    # ---- cells (v2 tracks), tracks, contours ----
    cpf = cpf.sort_values(["cell", "frame"])
    first = cpf.groupby("cell")["frame"].transform("min")
    cpf["age_min"] = (cpf["frame"] - first) * 30
    gen_cells = {}
    for r in gen.itertuples():
        for c in (r.from_cell, r.into_cell):
            gen_cells.setdefault(int(c), []).append({"frame": int(r.frame), "type": r.type,
                                                     "from": int(r.from_cell), "into": int(r.into_cell)})
    for k in range(len(times)):
        feats = []
        for r in cpf[cpf["frame"] == k].itertuples():
            polys = rings(mask[k] == int(r.feature), ds, to_ll, tol=0.7)
            if not polys:
                continue
            props = {"cell": int(r.cell), "feature": int(r.feature), "phase": r.phase, "min_bt_K": round(float(r.min_bt_K), 1),
                     "area_km2": round(float(r.area_km2)), "cold_core_km2": round(float(r.cold_core_km2)),
                     "speed_kmh": clean(None if pd.isna(r.speed_kmh) else round(float(r.speed_kmh), 1)),
                     "heading_deg": clean(None if pd.isna(r.heading_deg) else round(float(r.heading_deg))),
                     "d_min_bt_30": clean(None if pd.isna(r.d_min_bt_30) else round(float(r.d_min_bt_30), 1)),
                     "age_min": int(r.age_min), "family": int(r.track_family), "touches_missing": bool(r.touches_missing),
                     "lon": round(float(r.lon), 4), "lat": round(float(r.lat), 4),
                     "merges_splits_so_far": sum(1 for e in gen_cells.get(int(r.cell), []) if e["frame"] <= k)}
            feats.append({"type": "Feature", "properties": props,
                          "geometry": {"type": "MultiPolygon", "coordinates": [[p] for p in polys]}})
        write_json(out / f"cells/f{k:02d}.geojson", {"type": "FeatureCollection", "features": feats})
        lines = rings((bt[k] < THR) & dom & np.isfinite(bt[k]), ds, to_ll, tol=1.0)
        write_json(out / f"contours/f{k:02d}.geojson", {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": lines}}]})
    tracks = {str(c): [{"frame": int(r.frame), "lon": round(float(r.lon), 4), "lat": round(float(r.lat), 4),
                        "min_bt_K": round(float(r.min_bt_K), 1), "area_km2": round(float(r.area_km2)),
                        "cold_core_km2": round(float(r.cold_core_km2)), "phase": r.phase}
                       for r in grp.itertuples()] for c, grp in cpf.groupby("cell")}
    write_json(out / "tracks.json", tracks)

    # ---- per-issue cell forecasts (Phase-3 v2 object predictions) + ML probability near the predicted position ----
    for i, k in enumerate(issue_frames):
        rows = opred[(opred["issue_frame"] == k) & opred["method"].isin(["field_advection", "persistence"])]
        cells = {}
        for (cell, meth), grp in rows.groupby(["cell", "method"]):
            for r in grp.itertuples():
                if int(r.lead_min) not in LEADS:
                    continue
                col, row = r.pred_x / dx, r.pred_y / dx
                lon, lat = to_ll(x0 + col * dx, y0 + row * dx)
                e = cells.setdefault(str(int(cell)), {"cell": int(cell), "by_lead": {}})["by_lead"].setdefault(str(int(r.lead_min)), {})
                e[meth] = {"lon": round(float(lon), 4), "lat": round(float(lat), 4)}
                if meth == "field_advection":
                    p = p_ml(i, int(r.lead_min))
                    ci, ri = int(round(col)), int(round(row))
                    win = p[max(ri - 2, 0): ri + 3, max(ci - 2, 0): ci + 3]
                    e["ml_p_max_10km"] = round(float(win.max()), 3) if win.size else None
        write_json(out / f"cellfc/i{i:02d}.json", cells)

    # ---- scores for this event (frozen per-issue table, mask V) ----
    pe = per[(per["event"] == event) & (per["mask"] == "V") & per["method"].isin(METHODS) & per["lead_min"].isin(LEADS)]
    scores = {}
    for r in pe.itertuples():
        H, M, F = int(r.H), int(r.M), int(r.F)
        scores.setdefault(r.issue_time_utc, {}).setdefault(str(int(r.lead_min)), {})[r.method] = {
            "H": H, "M": M, "F": F, "CN": int(r.CN), "n": int(r.n),
            "CSI": clean(H / (H + M + F) if H + M + F else None), "POD": clean(H / (H + M) if H + M else None),
            "bias": clean((H + F) / (H + M) if H + M else None), "BS": round(float(r.brier_sum) / int(r.n), 6)}
    write_json(out / "scores.json", scores)

    # ---- places + draft advisories (display rule on frozen ML probabilities; CAP status=Exercise) ----
    geo = json.loads(fz.path(f"data/raw/hail_reports/geocoded_{ev_cfg['date']}.json").read_text())
    places = [{"name": s["name"], "printed_as": s.get("printed_as", s["name"]), "lat": s["lat"], "lon": s["lon"],
               "state_hint": s["state_hint"], "source": ev_cfg["truth_source"], "report_date": ev_cfg["date"]}
              for s in geo if s.get("lat") is not None and BBOX[1] <= s["lat"] <= BBOX[3] and BBOX[0] <= s["lon"] <= BBOX[2]]
    write_json(out / "places.json", places)
    tr = Transformer.from_crs("EPSG:4326", ds.attrs["crs_proj4"], always_xy=True)
    pix = []
    for s in places:
        X, Y = tr.transform(s["lon"], s["lat"])
        pix.append((int(round((Y - y0) / dx)), int(round((X - x0) / dx))))
    alerts, place_p = {}, {}
    for i, t in enumerate(issues):
        lst, pp = [], {}
        for s, (ri, ci) in zip(places, pix):
            best = None
            for L in ALERT_LEADS:
                p = p_ml(i, L)
                win = p[max(ri - ALERT_RADIUS_PX, 0): ri + ALERT_RADIUS_PX + 1, max(ci - ALERT_RADIUS_PX, 0): ci + ALERT_RADIUS_PX + 1]
                v = float(win.max()) if win.size else 0.0
                pp[s["name"]] = max(pp.get(s["name"], 0.0), round(v, 3))
                if v >= ALERT_P and best is None:
                    best = (L, v)
            if best:
                pred = f"ml-v0/{event}/{t:%Y%m%dT%H%MZ}/L{best[0]}"      # source prediction = one grid forecast
                lst.append({"alert_id": f"{pred}#{s['name']}", "place": s["name"], "lat": s["lat"], "lon": s["lon"],
                            "lead_min": best[0], "p_max": round(best[1], 3), "prediction_id": pred})
        alerts[f"{t:%Y-%m-%d %H:%M:%S}"] = lst
        place_p[f"{t:%Y-%m-%d %H:%M:%S}"] = pp
    write_json(out / "alerts.json", {"rule": f"draft if ML P(BT < 235 K) >= {ALERT_P} within {ALERT_RADIUS_PX * 2} km of a "
                                             f"place at +30 or +60 min (frozen p >= 0.5 threshold); EXERCISE only",
                                     "by_issue": alerts, "place_max_p_60min": place_p})

    # ---- skill (frozen held-out metrics) ----
    pooled = pd.read_csv(fz.path("data/processed/ml_eval/ml-v0/metrics_pooled_lead.csv"))
    byev = pd.read_csv(fz.path("data/processed/ml_eval/ml-v0/metrics_by_event_lead.csv"))
    boot = pd.read_csv(fz.path("data/processed/ml_eval/ml-v0/bootstrap_ml_vs_pysteps.csv"))
    rel = pd.read_csv(fz.path("data/processed/ml_eval/ml-v0/reliability.csv"))
    cross = pd.read_csv(fz.path("data/processed/multi_event/cross_event_by_lead.csv"))
    decay = pd.read_csv(fz.path("data/processed/multi_event/decay_by_event.csv"))
    decomp = pd.read_csv(fz.path("data/processed/multi_event/phase5/decomposition_by_lead.csv"))
    pv = pooled[(pooled["mask"] == "V") & pooled["method"].isin(METHODS)]
    fss = byev[(byev["mask"] == "V")].groupby(["method", "lead_min"])["FSS_40km"].mean()
    skill = {"source": "frozen held-out evaluation ml-v0 (E8, E10, E11 pooled; mask V)", "leads": sorted(pv["lead_min"].unique().tolist()),
             "pooled": {m: [{"lead_min": int(r.lead_min), "CSI": clean(float(r.CSI)), "POD": clean(float(r.POD)),
                             "FAR": clean(float(r.FAR)), "bias": clean(float(r.bias)), "BSS": clean(float(r.BSS_vs_train_clim)),
                             "FSS_40km_event_mean": clean(float(fss.loc[(m, r.lead_min)])), "n_px": int(r.n)}
                            for r in g.sort_values("lead_min").itertuples()] for m, g in pv.groupby("method")},
             "by_event": {ev: {m: [{"lead_min": int(r.lead_min), "CSI": clean(float(r.CSI)), "BSS": clean(float(r.BSS_vs_train_clim)),
                                    "FSS_40km": clean(float(r.FSS_40km)), "bias": clean(float(r.bias))}
                                   for r in gm.sort_values("lead_min").itertuples()]
                               for m, gm in ge[ge["method"].isin(METHODS)].groupby("method")}
                          for ev, ge in byev[byev["mask"] == "V"].groupby("event")},
             "bootstrap": [{k: clean(float(v)) if isinstance(v, (int, float, np.floating)) else v for k, v in r._asdict().items()
                            if k != "Index"} for r in boot.itertuples()],
             "reliability": [{"method": r.method, "lead_min": int(r.lead_min), "bin": int(r.bin), "n": int(r.n),
                              "sum_p": float(r.sum_p), "sum_o": float(r.sum_o)} for r in rel.itertuples()],
             "reliability_by_bin": reliability_bins(rel),
             "phase4_cross_event": [{"lead_min": int(r.lead_min), "CSI_persistence": float(r.CSI_pooled_persistence),
                                     "CSI_pysteps": float(r.CSI_pooled_pysteps_advection),
                                     "n_events_pysteps_better": int(r.n_events_advection_better_CSI)} for r in cross.itertuples()],
             "phase4_decay": decay.to_dict("records"),
             "phase5_decomposition": decomp[["event", "lead_min", "bias_V", "E_edge", "C_advected_area", "G_unchanged_intensity",
                                             "frac_obs_events_in_edge"]].to_dict("records"),
             "claim_guard": "ML's advantage is in probability skill (BSS). As a yes/no forecast (p >= 0.5) ML does not beat "
                            "pySTEPS beyond 60 min (docs/FINAL_CLAIMS.md B1)."}
    write_json(out / "skill.json", skill)

    # ---- data health ----
    raw_man = json.loads(fz.path("data/raw/cpc_merged_ir/manifest.json").read_text())
    base = pd.read_csv(fz.path(f"data/processed/{event}/baseline/grid_metrics_by_lead.csv"))
    gf = ds["gapfilled"].values
    frames = [{"frame": k, "time_utc": f"{t:%Y-%m-%dT%H:%M:%SZ}", "qc_status": str(ds["qc_status"].values[k]),
               "qc_missing_frac": round(float(ds["qc_missing_frac"].values[k]), 4),
               "raw_missing_frac": round(float(ds["raw_missing_frac"].values[k]), 4),
               "gapfilled_frac": round(float(gf[k][dom].mean()), 4), "source_file": str(ds["source_file"].values[k]),
               "source_sha256": raw_man[str(ds["source_file"].values[k])]["sha256"]} for k, t in enumerate(times)]
    health = {"frames": frames,
              "unscorable_frac_by_lead": base[base["method"] == "persistence"][["lead_min", "excluded_frac_mean"]].to_dict("records"),
              "sources": [
                  {"source": "NOAA/NCEP/CPC merged IR (4 km, 30 min)", "status": "AVAILABLE (FALLBACK)", "role": "all inputs + truth",
                   "note": "approved Phase-1 substitute for Meteosat/INSAT; single ~11 um IR channel; US Government work"},
                  {"source": "Meteosat-9 IODC SEVIRI", "status": "NOT CONNECTED", "role": "planned primary",
                   "note": "EUMETSAT account needed; not used in any result"},
                  {"source": "INSAT-3DR/3DS Imager (MOSDAC)", "status": "NOT CONNECTED", "role": "planned",
                   "note": "general users: 3-day latency; not used"},
                  {"source": "IMD Doppler weather radar", "status": "UNAVAILABLE", "role": "independent truth",
                   "note": "no open access; no radar validation in any result"},
                  {"source": "Lightning (ISS-LIS / ground network)", "status": "UNAVAILABLE", "role": "independent truth",
                   "note": "not used; no lightning skill claimed"},
                  {"source": "IMD RMC New Delhi hail report (PDF)", "status": "AVAILABLE", "role": "event selection / context only",
                   "note": "archived with SHA-256; not a verification truth"}],
              "latency_note": "NOAA CPC product latency is not modelled; replay uses frames at nominal time (NEEDS VERIFICATION).",
              "model": {"version": card["version"], "artifacts": card["artifacts"], "n_iter": card["n_iter_selected"],
                        "train_days": card["train_days"], "validation_days": card["validation_days"],
                        "test_events": card["test_events_never_read"], "calibration": "isotonic per lead bin, validation days only",
                        "deterministic_threshold_p": 0.5},
              "freeze_manifest_sha256": sha256(FREEZE),
              "limitations": ["Only 3 held-out event days (E8, E10, E11), May 2026, NW India",
                              "Backward-in-time test: trained on 18-31 May, after the test days",
                              "Thin training data: 14 days, 7 convective",
                              "30-min satellite cadence; no 15-min leads",
                              "Single IR channel (NOAA CPC merged IR, 4 km)",
                              "No independent radar or lightning validation",
                              "Cell tracks/phases are diagnostic (phase rules v0 PROPOSED)"]}
    write_json(out / "health.json", health)

    # ---- manifest ----
    man = {"event": event, "code": ev_cfg["code"], "name": ev_cfg["name"], "date": ev_cfg["date"],
           "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "mode": "REPLAY", "data_tier": "SAT (IR only) · Radar ✗ · Lightning ✗",
           "envelope": {"model": {"name": "ml-v0", "version": card["version"], "artifacts": card["artifacts"]},
                        "baselines": ["persistence", "pySTEPS (Lucas-Kanade + semi-Lagrangian)", "pySTEPS 31-px neighbourhood (no fit)"],
                        "evidence_level": "PROBABILITY (ML); deterministic baselines", "calibrated": True},
           "held_out": event in card["test_events_never_read"],
           "grid": {k: g[k] for k in ("width", "height", "bounds")},
           "codes": {"bt": "value = BT - 160 K (0..254), 255 = no data", "p": "value = P x 250 (0..250), 255 = no data"},
           "frames": [f"{t:%Y-%m-%dT%H:%M:%SZ}" for t in times],
           "issues": [{"i": i, "frame": k, "time_utc": f"{t:%Y-%m-%dT%H:%M:%SZ}"} for i, (k, t) in enumerate(zip(issue_frames, issues))],
           "leads_min": LEADS, "freeze_manifest_sha256": sha256(FREEZE), "inputs": fz.used}
    man["outputs"] = {str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    write_json(out / "manifest.json", man)
    return out


def build_index(events: list[str]) -> None:
    """Event preset cards: REPLAY_SPEC E1-E9 plus the Phase-4 events, with honest availability."""
    cards = [
        {"code": "E1", "date": "May 2018", "place": "S. Kerala", "hazard": "Pre-monsoon thunderstorms", "status": "NOT AVAILABLE",
         "reason": "outside the NW-India domain; NOAA archive on this server starts 2026"},
        {"code": "E2", "date": "25 Jun 2020", "place": "Bihar / UP", "hazard": "Lightning", "status": "NOT AVAILABLE",
         "reason": "pre-2026; not in the approved archive"},
        {"code": "E3", "date": "13 May 2024", "place": "Mumbai / Thane", "hazard": "Squall", "status": "NOT AVAILABLE", "reason": "pre-2026"},
        {"code": "E4", "date": "2 May 2025", "place": "Delhi-NCR", "hazard": "Severe thunderstorm", "status": "NOT AVAILABLE", "reason": "pre-2026"},
        {"code": "E5", "date": "30 Jun-1 Jul 2025", "place": "Mandi (HP)", "hazard": "Cloudburst", "status": "NOT AVAILABLE", "reason": "pre-2026"},
        {"code": "E6", "date": "5 Aug 2025", "place": "Dharali (UK)", "hazard": "Cloudburst", "status": "NOT AVAILABLE", "reason": "pre-2026"},
        {"code": "E7", "date": "14 Aug 2025", "place": "Kishtwar (J&K)", "hazard": "Cloudburst", "status": "NOT AVAILABLE", "reason": "pre-2026"},
        {"code": "E8a", "date": "1 May 2026", "place": "Haryana / W. UP / UK", "hazard": "Hail", "status": "EXCLUDED",
         "reason": "Phase-4 suitability rule: too little cloud < 235 K"},
        {"code": "E9", "date": "21 Mar, 5 & 9 Apr 2026", "place": "UP / Haryana / Rajasthan", "hazard": "Hail", "status": "NOT AVAILABLE",
         "reason": "April 2026 missing from the NOAA archive"},
    ]
    ev = yaml.safe_load(Path("config/events.yaml").read_text())
    for e in events:
        m = json.loads((WEB / e / "manifest.json").read_text())
        cards.append({"code": m["code"], "event": e, "date": m["date"], "place": ev[e]["name"], "hazard": ev[e]["hazard"],
                      "status": "BUNDLED", "held_out": m["held_out"], "reason": "held-out test event (never used in training)"})
    write_json(WEB / "index.json", {"default": "E8_20260514", "events": cards})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", nargs="+", default=["E8_20260514"])
    a = ap.parse_args()
    for e in a.event:
        print(build(e))
    built = sorted(p.name for p in WEB.iterdir() if (p / "manifest.json").exists())
    build_index(built)


if __name__ == "__main__":
    main()
