"""Phase-6 diagnostic: permutation importance of the frozen model on a VALIDATION-day subsample (never test).

  python -m scripts.ml_importance
Metric: increase in weighted log-loss when one feature column is shuffled (fixed seed). Not used for any choice.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import log_loss

from ml.features.grid_features import FEATURES
from scripts.train_ml import load


def main() -> None:
    cfg = yaml.safe_load(Path("config/ml_dataset.yaml").read_text())
    md = Path(f"data/models/{cfg['version']}")
    man = json.loads(Path("data/processed/ml_dataset/dataset_manifest.json").read_text())
    va = load("validation", man).sample(n=200_000, random_state=0)
    clf = joblib.load(md / "model.joblib")
    X, y, w = va[FEATURES].to_numpy(np.float32), va["y"].to_numpy(), va["weight"].to_numpy()
    base = log_loss(y, clf.predict_proba(X)[:, 1], sample_weight=w)
    rng = np.random.default_rng(0)
    rows = []
    for j, f in enumerate(FEATURES):
        Xp = X.copy()
        Xp[:, j] = X[rng.permutation(len(X)), j]
        rows.append({"feature": f, "logloss_increase": log_loss(y, clf.predict_proba(Xp)[:, 1], sample_weight=w) - base})
    out = pd.DataFrame(rows).sort_values("logloss_increase", ascending=False)
    out.to_csv(md / "permutation_importance_validation.csv", index=False)
    print(f"base weighted log-loss {base:.5f}")
    print(out.to_string(index=False, float_format=lambda v: f"{v:.5f}"))


if __name__ == "__main__":
    main()
