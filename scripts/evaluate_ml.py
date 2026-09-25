"""Phase-6 held-out evaluation of the frozen ML model on the test events (run once per frozen model version).

  python -m scripts.evaluate_ml

Methods (identical pixels, identical scoring code):
  persistence, pysteps_advection  - the unchanged Phase-2/4 baselines;
  pysteps_np31                    - no-fit reference: fraction of pySTEPS BT < 235 K in 31x31 px (probability);
                                    deterministic event = fraction >= 0.5;
  ml_raw, ml                      - HistGradientBoosting probability, raw and isotonic-calibrated; event = p >= 0.5.
Masks: V = Phase-2/4 scoring mask (primary; both baselines valid); D = domain & valid observation (edge included; a
NaN pySTEPS forecast counts as "no event", persistence likewise where BT(t) is missing).
Probabilistic scores on V: Brier score, BSS vs the TRAINING climatology per lead (VALIDATION_PLAN §2), reliability.
Deterministic methods enter the Brier score as 0/1 probabilities.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ml.features.grid_features import issue_features, stack
from ml.verification.scores import FSSAccumulator, cat_scores, contingency
from scripts.run_multi_event import circular_block_indices, csi_bias
from scripts.train_ml import calibrate

CFG_PATH = Path("config/ml_dataset.yaml")
METHODS = ["persistence", "pysteps_advection", "pysteps_np31", "ml_raw", "ml"]
PROB_METHODS = ["pysteps_np31", "ml_raw", "ml"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate_event(ev: str, cfg: dict, cfg_b: dict, clf, cal, clim: dict, out: Path) -> tuple[list, dict, list]:
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    bt, dom = ds["bt"].values, ds["in_domain"].values
    times = pd.to_datetime(ds.time.values)
    thr, pthr = cfg["target_bt_K"], cfg["scoring"]["deterministic_threshold_p"]
    bins = cfg["calibration"]["lead_bins_min"]
    scales = cfg["scoring"]["fss_scales_px"]
    nb = cfg["scoring"]["reliability_bins"]
    n_lead, cad = cfg_b["max_lead_steps"], cfg_b["cadence_min"]
    issues = list(range(cfg_b["motion"]["n_past_frames"] - 1, bt.shape[0] - 1))
    prob_store = np.zeros((len(issues), n_lead) + bt.shape[1:], np.uint16)   # calibrated ML p x 10000 on D, else 0
    rows, rel = [], []
    fss = {(m, L, s): FSSAccumulator(s) for m in METHODS for L in range(1, n_lead + 1) for s in scales}
    for i, k in enumerate(issues):
        P = bt[k]
        for L, feats, F in issue_features(bt, k, dom, times, cfg_b, thr):
            if k + L >= bt.shape[0]:
                break
            obs = bt[k + L]
            D = dom & np.isfinite(obs)
            V = D & np.isfinite(P) & np.isfinite(F)
            o_ev = np.isfinite(obs) & (obs < thr)
            idx = np.flatnonzero(D)
            p_raw = np.zeros(bt.shape[1:], np.float64)
            p_raw.flat[idx] = clf.predict_proba(stack(feats, idx))[:, 1]
            p_cal = np.zeros_like(p_raw)
            p_cal.flat[idx] = calibrate(cal, p_raw.flat[idx], np.full(len(idx), L * cad), bins)
            prob_store[i, L - 1].flat[idx] = np.round(p_cal.flat[idx] * 10000).astype(np.uint16)
            prob = {"persistence": (np.isfinite(P) & (P < thr)).astype(float),
                    "pysteps_advection": (np.isfinite(F) & (F < thr)).astype(float),
                    "pysteps_np31": feats["adv_frac31"].astype(float), "ml_raw": p_raw, "ml": p_cal}
            c = clim[str(L * cad)]
            for m in METHODS:
                fc_ev = prob[m] >= (pthr if m in PROB_METHODS else 0.5)
                for tag, msk in (("V", V), ("D", D)):
                    ct = contingency(fc_ev, o_ev, msk)
                    e = (prob[m][msk] - o_ev[msk]) ** 2
                    rows.append({"event": ev, "method": m, "mask": tag, "issue_time_utc": str(times[k]),
                                 "issue_hour_utc": times[k].hour, "lead_min": L * cad, **ct,
                                 "brier_sum": float(e.sum()), "brier_clim_sum": float(((c - o_ev[msk]) ** 2).sum()),
                                 "n": int(msk.sum())})
                for s in scales:
                    fss[(m, L, s)].add(fc_ev, o_ev, V)
            for m in PROB_METHODS:
                pv, ov = prob[m][V], o_ev[V]
                b = np.minimum((pv * nb).astype(int), nb - 1)
                rel.append(pd.DataFrame({"event": ev, "method": m, "lead_min": L * cad, "bin": np.arange(nb),
                                         "n": np.bincount(b, minlength=nb),
                                         "sum_p": np.bincount(b, weights=pv, minlength=nb),
                                         "sum_o": np.bincount(b, weights=ov.astype(float), minlength=nb)}))
    xr.Dataset({"p_ml": (("issue_time", "lead_min", "y", "x"), prob_store,
                         {"scale_factor": 1e-4, "long_name": "calibrated P(BT < 235 K) on domain pixels with valid obs"})},
               coords={"issue_time": times[issues].values, "lead_min": np.arange(1, n_lead + 1) * cad,
                       "y": ds.y.values, "x": ds.x.values}
               ).to_netcdf(out / f"ml_probabilities_{ev}.nc", encoding={"p_ml": {"zlib": True, "complevel": 4}})
    fss_rows = [{"event": ev, "method": m, "lead_min": L * cad, f"FSS_{s * 2}km": acc.fss()}
                for (m, L, s), acc in fss.items()]
    return rows, fss_rows, rel


def summarise(per: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = per.groupby(by)[["H", "M", "F", "CN", "brier_sum", "brier_clim_sum", "n"]].sum().reset_index()
    sc = pd.DataFrame([cat_scores(*(int(v) for v in r)) for r in g[["H", "M", "F", "CN"]].to_numpy()])
    g = pd.concat([g, sc], axis=1)
    g["BS"] = g["brier_sum"] / g["n"]
    g["BSS_vs_train_clim"] = 1 - g["brier_sum"] / g["brier_clim_sum"]
    return g


def bootstrap(per: pd.DataFrame, cfg_boot: dict) -> pd.DataFrame:
    """Within-event circular block bootstrap over issue times (Phase-4 settings): ML minus pySTEPS, on V."""
    rows = []
    v = per[per["mask"] == "V"]
    for (ev, L), g in v.groupby(["event", "lead_min"]):
        a = {m: g[g["method"] == m].sort_values("issue_time_utc")
             for m in ("pysteps_advection", "ml", "persistence", "pysteps_np31")}
        n = len(a["ml"])
        rng = np.random.default_rng(cfg_boot["seed"])
        idx = np.stack([circular_block_indices(n, min(cfg_boot["block"], n), rng) for _ in range(cfg_boot["n"])])
        ct = {m: a[m][["H", "M", "F"]].to_numpy(float) for m in a}
        csi = {m: csi_bias(ct[m][idx].sum(1))[0] for m in a}
        bs = {m: a[m]["brier_sum"].to_numpy()[idx].sum(1) for m in a}
        pt = {m: csi_bias(ct[m].sum(0))[0] for m in a}
        d = csi["ml"] - csi["pysteps_advection"]
        dbs = bs["pysteps_advection"] - bs["ml"]
        dnp = bs["pysteps_np31"] - bs["ml"]
        clim = a["ml"]["brier_clim_sum"].to_numpy()[idx].sum(1)
        dbss = dnp / clim                                  # BSS(ml) - BSS(np31), same climatology reference
        rows.append({"event": ev, "lead_min": int(L), "n_issue_times": n,
                     "CSI_ml": pt["ml"], "CSI_pysteps": pt["pysteps_advection"], "CSI_persistence": pt["persistence"],
                     "CSI_diff_ml_minus_pysteps": pt["ml"] - pt["pysteps_advection"],
                     "CSI_diff_lo95": np.nanquantile(d, 0.025), "CSI_diff_hi95": np.nanquantile(d, 0.975),
                     "frac_boot_ml_better_CSI": float(np.nanmean(d > 0)),
                     "Brier_reduction_vs_pysteps": float((a["pysteps_advection"]["brier_sum"].sum() - a["ml"]["brier_sum"].sum())
                                                         / a["ml"]["n"].sum()),
                     "Brier_reduction_lo95": float(np.quantile(dbs, 0.025) / a["ml"]["n"].sum()),
                     "Brier_reduction_hi95": float(np.quantile(dbs, 0.975) / a["ml"]["n"].sum()),
                     "BSS_diff_ml_minus_np31": float((a["pysteps_np31"]["brier_sum"].sum() - a["ml"]["brier_sum"].sum())
                                                     / a["ml"]["brier_clim_sum"].sum()),
                     "BSS_diff_np31_lo95": float(np.quantile(dbss, 0.025)),
                     "BSS_diff_np31_hi95": float(np.quantile(dbss, 0.975)),
                     "frac_boot_ml_better_than_np31": float(np.mean(dnp > 0))})
    return pd.DataFrame(rows)


def main() -> None:
    cfg = yaml.safe_load(CFG_PATH.read_text())
    cfg_b = yaml.safe_load(Path("config/baseline.yaml").read_text())
    mdir = Path(f"data/models/{cfg['version']}")
    card = json.loads((mdir / "model_card.json").read_text())
    for n, dg in card["artifacts"].items():
        if sha256(mdir / n) != dg:
            raise ValueError(f"model artifact {n} does not match its model card")
    clf, cal = joblib.load(mdir / "model.joblib"), joblib.load(mdir / "calibrators.joblib")
    out = Path(f"data/processed/ml_eval/{cfg['version']}")
    out.mkdir(parents=True, exist_ok=True)
    if "--resummarise" in sys.argv:        # re-derive summaries from the saved per-issue scores; no new predictions
        per = pd.read_csv(out / "per_issue.csv")
        old_ev = pd.read_csv(out / "metrics_by_event_lead.csv")
        fss = old_ev[["event", "method", "lead_min", "FSS_10km", "FSS_20km", "FSS_40km"]].drop_duplicates()
        rel = None
    else:
        rows, fss_rows, rel = [], [], []
        for ev in cfg["splits"]["test"]:
            r, f, rl = evaluate_event(ev, cfg, cfg_b, clf, cal, card["train_climatology_by_lead"], out)
            rows += r; fss_rows += f; rel += rl
            print("done", ev, flush=True)
        per = pd.DataFrame(rows)
        per.to_csv(out / "per_issue.csv", index=False)
        fss = pd.DataFrame(fss_rows).groupby(["event", "method", "lead_min"]).first().reset_index()
    by_ev = summarise(per, ["event", "method", "mask", "lead_min"]).merge(fss, on=["event", "method", "lead_min"], how="left")
    by_ev.to_csv(out / "metrics_by_event_lead.csv", index=False)
    summarise(per, ["method", "mask", "lead_min"]).to_csv(out / "metrics_pooled_lead.csv", index=False)
    summarise(per.assign(block=(per["issue_hour_utc"] // 6 * 6)), ["event", "method", "mask", "block", "lead_min"]
              ).to_csv(out / "metrics_by_issue_block.csv", index=False)
    if rel is not None:
        rel = pd.concat(rel).groupby(["method", "lead_min", "bin"])[["n", "sum_p", "sum_o"]].sum().reset_index()
        rel.to_csv(out / "reliability.csv", index=False)
    # Edge-only scores: pixels in D but not in V (inflow edge + missing BT(t)), where pySTEPS has no forecast.
    key = ["event", "method", "issue_time_utc", "lead_min"]
    cols = ["H", "M", "F", "CN", "brier_sum", "brier_clim_sum", "n"]
    edge = (per[per["mask"] == "D"].set_index(key)[cols] - per[per["mask"] == "V"].set_index(key)[cols]).reset_index()
    summarise(edge.assign(mask="edge_only", issue_hour_utc=0), ["method", "mask", "lead_min"]).to_csv(
        out / "metrics_edge_only.csv", index=False)
    boot = bootstrap(per, {"seed": 20260925, "block": 12, "n": 1000})
    boot.to_csv(out / "bootstrap_ml_vs_pysteps.csv", index=False)
    csvs = sorted(out.glob("*.csv"))
    prov = {"evaluated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "model_card": card["artifacts"],
            "model_version": cfg["version"], "test_events": cfg["splits"]["test"],
            "config_sha256": sha256(CFG_PATH), "config_baseline_sha256": sha256(Path("config/baseline.yaml")),
            "inputs": {f"{ev}.nc": sha256(Path(f"data/interim/grid2km/{ev}.nc")) for ev in cfg["splits"]["test"]},
            "outputs": {p.name: sha256(p) for p in csvs}}
    (out / "evaluation_provenance.json").write_text(json.dumps(prov, indent=2))
    pooled = pd.read_csv(out / "metrics_pooled_lead.csv")
    pv = pooled[(pooled["mask"] == "V") & pooled["lead_min"].isin([30, 60, 120, 180, 240, 360])]
    print(pv.pivot_table(index="lead_min", columns="method", values=["CSI", "bias", "BSS_vs_train_clim"]).round(3).to_string())


if __name__ == "__main__":
    main()
