"""Phase-2 tests: score correctness, leakage (time-ordering), and reproducibility of saved baseline outputs.

Unit tests use tiny hand-built arrays for arithmetic only; everything else uses the real E8 cube/outputs
and is skipped if they are absent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from ml.forecasting.baselines import advection_grid, persistence_grid, shifted_iou
from ml.verification.scores import FSSAccumulator, cat_scores, contingency

EVENT = "E8_20260514"
CUBE = Path(f"data/interim/grid2km/{EVENT}.nc")
BASE = Path(f"data/processed/{EVENT}/baseline")
needs_cube = pytest.mark.skipif(not CUBE.exists(), reason="cube not built")
needs_base = pytest.mark.skipif(not (BASE / "baseline_provenance.json").exists(), reason="baseline not run")


def _cfg():
    return yaml.safe_load(Path("config/baseline.yaml").read_text())


# ---------------- unit tests ----------------

def test_contingency_and_scores():
    f = np.array([1, 1, 0, 0, 1], bool)
    o = np.array([1, 0, 1, 0, 1], bool)
    v = np.array([1, 1, 1, 1, 0], bool)  # last pixel invalid -> not scored
    ct = contingency(f, o, v)
    assert ct == {"H": 1, "M": 1, "F": 1, "CN": 1}
    s = cat_scores(**ct)
    assert s["POD"] == 0.5 and s["FAR"] == 0.5 and s["CSI"] == pytest.approx(1 / 3) and s["bias"] == 1.0


def test_shifted_iou():
    a = np.zeros((6, 6), bool); a[1:3, 1:3] = True
    b = np.zeros((6, 6), bool); b[2:4, 3:5] = True
    assert shifted_iou(a, b, (1, 2)) == 1.0
    assert shifted_iou(a, b, (0, 0)) == 0.0


def test_fss_perfect_and_disjoint():
    x = np.zeros((20, 20), bool); x[5:8, 5:8] = True
    v = np.ones_like(x)
    acc = FSSAccumulator(3); acc.add(x, x, v)
    assert acc.fss() == pytest.approx(1.0)
    y = np.zeros_like(x); y[14:17, 14:17] = True
    acc2 = FSSAccumulator(3); acc2.add(x, y, v)
    assert acc2.fss() == pytest.approx(0.0)


# ---------------- real-data tests ----------------

@needs_cube
def test_fss_matches_pysteps_on_real_nan_free_window():
    import xarray as xr
    from pysteps.verification.spatialscores import fss as ps_fss
    bt = xr.open_dataset(CUBE)["bt"].values
    # Find a real 60x60 window without missing data, with events, at two frames 1 h apart.
    for k in range(16, 40):
        for i0 in range(0, bt.shape[1] - 60, 20):
            for j0 in range(0, bt.shape[2] - 60, 20):
                a, b = bt[k, i0:i0 + 60, j0:j0 + 60], bt[k + 2, i0:i0 + 60, j0:j0 + 60]
                if np.isfinite(a).all() and np.isfinite(b).all() and (a < 235).any() and (b < 235).any():
                    acc = FSSAccumulator(10)
                    acc.add(a < 235, b < 235, np.ones(a.shape, bool))
                    # pySTEPS fss thresholds with X >= thr (precip convention): use "coldness" so events match ours.
                    ref = ps_fss(300.0 - a, 300.0 - b, 300.0 - 235.0 + 1e-9, 10)
                    assert acc.fss() == pytest.approx(ref, abs=1e-9)
                    return
    pytest.skip("no NaN-free window with events found")


@needs_cube
def test_forecasts_use_only_past_frames():
    import xarray as xr
    bt = xr.open_dataset(CUBE)["bt"].values
    k, n = 20, 12
    tampered = bt.copy(); tampered[k + 1:] = np.nan  # destroy the future
    fa, va = advection_grid(bt, k, n, _cfg())
    fb, vb = advection_grid(tampered, k, n, _cfg())
    assert np.array_equal(fa, fb, equal_nan=True) and np.array_equal(va, vb)
    assert np.array_equal(persistence_grid(bt, k, n), persistence_grid(tampered, k, n), equal_nan=True)
    assert np.array_equal(persistence_grid(bt, k, n)[3], bt[k], equal_nan=True)


@needs_base
def test_saved_outputs_match_provenance_hashes():
    prov = json.loads((BASE / "baseline_provenance.json").read_text())
    for name, digest in prov["outputs"].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == digest, name
    assert prov["fitted_parameters"].startswith("none")


@needs_base
def test_one_saved_score_recomputes_exactly():
    import xarray as xr
    ds = xr.open_dataset(CUBE)
    bt, dom = ds["bt"].values, ds["in_domain"].values
    fc = xr.open_dataset(BASE / "advection_forecasts.nc")
    per = pd.read_csv(BASE / "grid_metrics_per_issue.csv")
    issue = pd.Timestamp("2026-05-14T12:00:00"); lead = 60
    k = int(np.where(pd.to_datetime(ds.time.values) == issue)[0][0])
    i = int(np.where(pd.to_datetime(fc.issue_time.values) == issue)[0][0])
    # Recompute from scratch (not from the stored int16 forecast) to check the stored table.
    fa, _ = advection_grid(bt, k, 12, _cfg())
    obs, fp = bt[k + 2], bt[k]
    valid = dom & np.isfinite(obs) & np.isfinite(fp) & np.isfinite(fa[1])
    ct = contingency(np.isfinite(fa[1]) & (fa[1] < 235), np.isfinite(obs) & (obs < 235), valid)
    row = per[(per.method == "pysteps_advection") & (per.issue_time_utc == str(issue)) & (per.lead_min == lead)].iloc[0]
    assert (row.H, row.M, row.F, row.CN) == (ct["H"], ct["M"], ct["F"], ct["CN"])
    # Stored int16 forecast is within its 0.01 K quantisation of the recomputed field.
    stored = fc.bt_forecast.values[i, 1]
    both = np.isfinite(stored) & np.isfinite(fa[1])
    assert np.nanmax(np.abs(stored[both] - fa[1][both])) <= 0.006
