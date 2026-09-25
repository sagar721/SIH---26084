"""Phase-6 tests: split/leakage rules, feature causality, unbiased weighted sampling, dataset/training/evaluation
reproducibility, calibration fitted on validation only, baselines unchanged, provenance.
Unit tests use tiny fixtures (arithmetic only); real-data tests skip when outputs are absent."""
from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

CFG = yaml.safe_load(Path("config/ml_dataset.yaml").read_text())
DS = Path("data/processed/ml_dataset")
MD = Path(f"data/models/{CFG['version']}")
EV = Path(f"data/processed/ml_eval/{CFG['version']}")
needs_ds = pytest.mark.skipif(not (DS / "dataset_manifest.json").exists(), reason="dataset not built")
needs_model = pytest.mark.skipif(not (MD / "model.joblib").exists(), reason="model not trained")
needs_eval = pytest.mark.skipif(not (EV / "evaluation_provenance.json").exists(), reason="not evaluated")
h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------- splits / leakage ----------------

def test_splits_exclude_events_and_buffers():
    from scripts.build_ml_dataset import forbidden_days, splits
    s = splits(CFG)
    ev = yaml.safe_load(Path("config/events.yaml").read_text())
    event_days = {date.fromisoformat(v["date"]) for v in ev.values()}          # every events.yaml day incl. E8a
    for days in s.values():
        for d in days:
            assert all(abs((d - e).days) > CFG["splits"]["buffer_days"] for e in event_days)
    assert not set(s["train"]) & set(s["validation"])
    assert event_days <= forbidden_days(CFG)


def test_splits_reject_a_block_touching_a_test_day():
    from scripts.build_ml_dataset import splits
    bad = json.loads(json.dumps(CFG))
    bad["splits"]["validation"] = {"start": "2026-05-12", "end": "2026-05-13"}   # 13 May = E8 buffer
    with pytest.raises(ValueError):
        splits(bad)


@needs_ds
def test_dataset_has_no_test_or_buffer_days():
    man = json.loads((DS / "dataset_manifest.json").read_text())
    forbidden = set(man["forbidden_days"])
    for rec in man["days"]:
        assert rec["day"] not in forbidden
        days = pd.read_parquet(rec["parquet"], columns=["day"])["day"].unique()
        assert set(days) == {rec["day"]}
        assert h(rec["parquet"]) == rec["parquet_sha256"]


def _training_cube():
    import xarray as xr
    man = json.loads((DS / "dataset_manifest.json").read_text())
    rec = next(r for r in man["days"] if r["split"] == "train")
    ds = xr.open_dataset(rec["cube"])
    return rec, ds["bt"].values, ds["in_domain"].values, pd.to_datetime(ds.time.values)


@needs_ds
def test_features_are_causal():
    from ml.features.grid_features import FEATURES, issue_features
    cfg_b = yaml.safe_load(Path("config/baseline.yaml").read_text())
    _, bt, dom, times = _training_cube()
    k = 20
    fut = bt.copy()
    fut[k + 1:] = 180.0 + np.random.default_rng(0).random(fut[k + 1:].shape) * 100   # destroy the future
    a = issue_features(bt, k, dom, times, cfg_b)
    b = issue_features(fut, k, dom, times, cfg_b)
    for _ in range(3):
        (La, fa, _), (Lb, fb, _) = next(a), next(b)
        assert La == Lb and all(np.array_equal(fa[f], fb[f], equal_nan=True) for f in FEATURES)


@needs_ds
def test_sample_weights_reproduce_population_counts_and_rows():
    from scripts.build_ml_dataset import sample_issue
    cfg_b = yaml.safe_load(Path("config/baseline.yaml").read_text())
    rec, bt, dom, times = _training_cube()
    k = 25
    rows = pd.concat(sample_issue(bt, dom, times, k, date.fromisoformat(rec["day"]), CFG, cfg_b), ignore_index=True)
    stored = pd.read_parquet(rec["parquet"])
    stored = stored[stored["issue_frame"] == k].drop(columns=["day", "split"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(rows, stored)                                  # deterministic re-sampling
    for L, g in rows.groupby("lead_min"):
        obs = bt[k + int(L) // 30]
        D = dom & np.isfinite(obs)
        assert g["weight"].sum() == pytest.approx(D.sum(), rel=1e-5)             # IPW total = population
        assert (g["y"] * g["weight"]).sum() == pytest.approx((D & (obs < 235.0)).sum(), rel=1e-5)


# ---------------- training ----------------

@needs_model
def test_model_card_and_artifacts():
    card = json.loads((MD / "model_card.json").read_text())
    assert card["gate"]["decision"] == "PROCEED" and card["trained"]
    for n, d in card["artifacts"].items():
        assert h(MD / n) == d
    assert card["config_sha256"] == h("config/ml_dataset.yaml")
    assert not set(card["train_days"]) & set(card["validation_days"])
    ev = yaml.safe_load(Path("config/events.yaml").read_text())
    test_days = {ev[e]["date"] for e in CFG["splits"]["test"]}
    assert not test_days & (set(card["train_days"]) | set(card["validation_days"]))
    assert card["n_iter_selected"] == int(np.argmin(card["validation_logloss_curve"])) + 1


@needs_model
def test_training_is_reproducible_and_calibration_uses_validation():
    import joblib
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import log_loss
    from ml.features.grid_features import FEATURES
    from scripts.train_ml import calibrate, load
    card = json.loads((MD / "model_card.json").read_text())
    man = json.loads((DS / "dataset_manifest.json").read_text())
    tr = load("train", man)
    sub = tr.iloc[:: 20]
    fit = lambda: HistGradientBoostingClassifier(**{**card["params_final"], "max_iter": 30}).fit(
        sub[FEATURES].to_numpy(np.float32), sub["y"], sample_weight=sub["weight"])
    X = sub[FEATURES].to_numpy(np.float32)[:5000]
    assert np.array_equal(fit().predict_proba(X), fit().predict_proba(X))       # same data + seed -> same model
    va = load("validation", man)
    clf, cal = joblib.load(MD / "model.joblib"), joblib.load(MD / "calibrators.joblib")
    p = clf.predict_proba(va[FEATURES].to_numpy(np.float32))[:, 1]
    assert log_loss(va["y"], p, sample_weight=va["weight"]) == pytest.approx(card["validation_logloss_raw"], rel=1e-9)
    pc = calibrate(cal, p, va["lead_min"].to_numpy(), CFG["calibration"]["lead_bins_min"])
    assert log_loss(va["y"], np.clip(pc, 1e-7, 1 - 1e-7), sample_weight=va["weight"]) == pytest.approx(
        card["validation_logloss_calibrated"], rel=1e-9)


# ---------------- evaluation ----------------

@needs_eval
def test_baselines_rescored_equal_phase4():
    per = pd.read_csv(EV / "per_issue.csv")
    for ev, g in per[per["mask"] == "V"].groupby("event"):
        pi = pd.read_csv(f"data/processed/{ev}/baseline/grid_metrics_per_issue.csv")
        for m in ("persistence", "pysteps_advection"):
            a = g[g["method"] == m].set_index(["issue_time_utc", "lead_min"])[["H", "M", "F", "CN"]]
            b = pi[pi["method"] == m].set_index(["issue_time_utc", "lead_min"])[["H", "M", "F", "CN"]]
            assert (a.loc[b.index] == b).all().all()


@needs_eval
def test_all_methods_scored_on_identical_pixels_and_outputs_hashed():
    per = pd.read_csv(EV / "per_issue.csv")
    n = per.pivot_table(index=["event", "mask", "issue_time_utc", "lead_min"], columns="method", values="n")
    assert (n.nunique(axis=1) == 1).all()
    prov = json.loads((EV / "evaluation_provenance.json").read_text())
    for name, d in prov["outputs"].items():
        assert h(EV / name) == d
    card = json.loads((MD / "model_card.json").read_text())
    assert prov["model_card"] == card["artifacts"]


@needs_eval
def test_pooled_metrics_equal_sum_of_events():
    from ml.verification.scores import cat_scores
    ev = pd.read_csv(EV / "metrics_by_event_lead.csv")
    po = pd.read_csv(EV / "metrics_pooled_lead.csv").set_index(["method", "mask", "lead_min"])
    for key, g in ev.groupby(["method", "mask", "lead_min"]):
        s = cat_scores(*[int(v) for v in g[["H", "M", "F", "CN"]].sum().values])
        assert s["CSI"] == pytest.approx(po.loc[key, "CSI"], abs=1e-12)


# ---------------- ingest / preprocess changes ----------------

def test_download_resumes_partial_file(tmp_path, monkeypatch):
    import requests
    from pipelines.ingest import cpc_merged_ir as ing
    payload = bytes(range(256)) * 40
    (tmp_path / "f.Z.part").write_bytes(payload[:1000])

    class R:
        def __init__(self, headers):
            start = int(headers["Range"].split("=")[1].rstrip("-")) if "Range" in headers else 0
            self.status_code = 206 if start else 200
            self.body = payload[start:]
            self.headers = {"Content-Length": str(len(self.body)), "Last-Modified": "x"}
            if start:
                self.headers["Content-Range"] = f"bytes {start}-{len(payload) - 1}/{len(payload)}"
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def raise_for_status(self): pass
        def iter_content(self, n): yield self.body

    monkeypatch.setattr(requests, "get", lambda url, stream, timeout, headers: R(headers))
    out = ing.download("f.Z", raw_dir=tmp_path)
    assert out.read_bytes() == payload
    assert json.loads((tmp_path / "manifest.json").read_text())["f.Z"]["bytes"] == len(payload)


def test_build_window_equals_event_build(tmp_path, monkeypatch):
    import xarray as xr
    from datetime import datetime
    from pipelines.preprocess import build_cube
    ref = Path("data/interim/grid2km/E11_20260516.nc")
    if not ref.exists():
        pytest.skip("E11 cube absent")
    monkeypatch.setattr(build_cube, "OUT_DIR", tmp_path)
    p = build_cube.build_window("E11_20260516", datetime(2026, 5, 16, 0, 0), datetime(2026, 5, 16, 23, 30))
    a, b = xr.open_dataset(p), xr.open_dataset(ref)
    assert np.array_equal(a["bt"].values, b["bt"].values, equal_nan=True)
    assert np.array_equal(a["gapfilled"].values, b["gapfilled"].values)


@needs_eval
def test_one_heldout_forecast_recomputed_from_frozen_model():
    import joblib
    import xarray as xr
    from ml.features.grid_features import issue_features, stack
    from ml.verification.scores import contingency
    from scripts.train_ml import calibrate
    ev, i, L = "E10_20260504", 20, 4
    cfg_b = yaml.safe_load(Path("config/baseline.yaml").read_text())
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    bt, dom, times = ds["bt"].values, ds["in_domain"].values, pd.to_datetime(ds.time.values)
    k = i + cfg_b["motion"]["n_past_frames"] - 1
    clf, cal = joblib.load(MD / "model.joblib"), joblib.load(MD / "calibrators.joblib")
    gen = issue_features(bt, k, dom, times, cfg_b)
    for _ in range(L):
        Lx, feats, F = next(gen)
    obs = bt[k + L]
    D = dom & np.isfinite(obs)
    idx = np.flatnonzero(D)
    p = np.zeros(bt.shape[1:])
    p.flat[idx] = calibrate(cal, clf.predict_proba(stack(feats, idx))[:, 1], np.full(len(idx), L * 30),
                            CFG["calibration"]["lead_bins_min"])
    stored = xr.open_dataset(EV / f"ml_probabilities_{ev}.nc")["p_ml"].values[i, L - 1].astype(float)
    stored = stored * 1e-4 if stored.max() > 1.5 else stored
    assert np.abs(stored - p).max() <= 0.5e-4 + 1e-9                          # uint16 storage at 1e-4
    V = D & np.isfinite(bt[k]) & np.isfinite(F)
    ct = contingency(p >= 0.5, np.isfinite(obs) & (obs < 235.0), V)
    per = pd.read_csv(EV / "per_issue.csv")
    row = per[(per["event"] == ev) & (per["method"] == "ml") & (per["mask"] == "V")
              & (per["issue_time_utc"] == str(times[k])) & (per["lead_min"] == L * 30)].iloc[0]
    assert {c: int(row[c]) for c in ct} == ct
