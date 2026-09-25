"""Phase-6 training: sufficiency gate -> HistGradientBoosting on the train days -> n_iter on validation days ->
isotonic calibration per lead bin on validation days. Test events are never read.

  python -m scripts.train_ml

Writes data/models/ml-v0/: model.joblib, calibrators.joblib, model_card.json (hashes, days, curve, climatology).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import log_loss

from ml.features.grid_features import FEATURES

CFG_PATH = Path("config/ml_dataset.yaml")
DS = Path("data/processed/ml_dataset")


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gate(cfg: dict, man: dict) -> dict:
    s = cfg["sufficiency"]
    conv = {sp: [d["day"] for d in man["days"] if d["split"] == sp and d["n_frames"] == 48
                 and d["deep_frames_frac"] >= s["deep_frame_frac"]] for sp in ("train", "validation")}
    ok = len(conv["train"]) >= s["min_convective_train_days"] and len(conv["validation"]) >= s["min_convective_val_days"]
    return {"convective_days": conv, "rule": s, "decision": "PROCEED" if ok else "STOP"}


def load(split: str, man: dict) -> pd.DataFrame:
    parts = []
    for d in man["days"]:
        if d["split"] == split:
            if sha256(Path(d["parquet"])) != d["parquet_sha256"]:
                raise ValueError(f"{d['parquet']} changed since the manifest was written")
            parts.append(pd.read_parquet(d["parquet"]))
    return pd.concat(parts, ignore_index=True)


def lead_bin(lead_min: np.ndarray, bins: list) -> np.ndarray:
    out = np.full(len(lead_min), -1, int)
    for i, (lo, hi) in enumerate(bins):
        out[(lead_min >= lo) & (lead_min <= hi)] = i
    return out


def calibrate(cal: dict, p: np.ndarray, lead_min: np.ndarray, bins: list) -> np.ndarray:
    b = lead_bin(lead_min, bins)
    out = np.empty_like(p)
    for i, iso in cal.items():
        m = b == i
        if m.any():                      # a call may hold a single lead (evaluation), leaving other bins empty
            out[m] = iso.predict(p[m])
    return out


def main() -> None:
    cfg = yaml.safe_load(CFG_PATH.read_text())
    man = json.loads((DS / "dataset_manifest.json").read_text())
    if man["config_sha256"] != sha256(CFG_PATH):
        raise ValueError("config/ml_dataset.yaml changed after the dataset was built")
    out = Path(f"data/models/{cfg['version']}")
    out.mkdir(parents=True, exist_ok=True)
    g = gate(cfg, man)
    print(json.dumps(g, indent=2))
    if g["decision"] == "STOP":
        (out / "model_card.json").write_text(json.dumps({"gate": g, "trained": False}, indent=2))
        return

    tr, va = load("train", man), load("validation", man)
    Xtr, ytr, wtr = tr[FEATURES].to_numpy(np.float32), tr["y"].to_numpy(), tr["weight"].to_numpy(np.float64)
    Xva, yva, wva = va[FEATURES].to_numpy(np.float32), va["y"].to_numpy(), va["weight"].to_numpy(np.float64)
    params = dict(cfg["model"]["params"])
    clf = HistGradientBoostingClassifier(**params).fit(Xtr, ytr, sample_weight=wtr)
    curve = [float(log_loss(yva, p[:, 1], sample_weight=wva, labels=[0, 1])) for p in clf.staged_predict_proba(Xva)]
    best = int(np.argmin(curve)) + 1
    params["max_iter"] = best
    clf = HistGradientBoostingClassifier(**params).fit(Xtr, ytr, sample_weight=wtr)

    bins = cfg["calibration"]["lead_bins_min"]
    p_va = clf.predict_proba(Xva)[:, 1]
    b = lead_bin(va["lead_min"].to_numpy(), bins)
    cal = {i: IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(p_va[b == i], yva[b == i],
                                                                                 sample_weight=wva[b == i])
           for i in range(len(bins))}
    p_va_cal = calibrate(cal, p_va, va["lead_min"].to_numpy(), bins)
    clim = (tr.assign(yw=tr["y"] * tr["weight"]).groupby("lead_min")[["yw", "weight"]].sum()
            .pipe(lambda d: d["yw"] / d["weight"]))
    joblib.dump(clf, out / "model.joblib")
    joblib.dump(cal, out / "calibrators.joblib")
    card = {
        "version": cfg["version"], "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gate": g, "trained": True, "features": FEATURES, "params_final": params, "n_iter_selected": best,
        "validation_logloss_curve": curve, "validation_logloss_raw": float(log_loss(yva, p_va, sample_weight=wva)),
        "validation_logloss_calibrated": float(log_loss(yva, np.clip(p_va_cal, 1e-7, 1 - 1e-7), sample_weight=wva)),
        "n_train_rows": len(tr), "n_val_rows": len(va), "train_days": sorted(tr["day"].unique()),
        "validation_days": sorted(va["day"].unique()), "test_events_never_read": cfg["splits"]["test"],
        "train_climatology_by_lead": {str(int(k)): float(v) for k, v in clim.items()},
        "config_sha256": sha256(CFG_PATH), "dataset_manifest_sha256": sha256(DS / "dataset_manifest.json"),
        "artifacts": {n: sha256(out / n) for n in ("model.joblib", "calibrators.joblib")},
        "versions": {p: version(p) for p in ("scikit-learn", "numpy", "scipy", "pysteps", "pandas")},
    }
    (out / "model_card.json").write_text(json.dumps(card, indent=2))
    print(f"n_iter={best}  val logloss raw={card['validation_logloss_raw']:.5f} cal={card['validation_logloss_calibrated']:.5f}")


if __name__ == "__main__":
    main()
