"""Phase-4 tests: event selection rule, identical protocol across events, reproducibility of per-event and
cross-event outputs, and the bootstrap code. Unit tests use tiny arithmetic fixtures; real-data tests are skipped
when the outputs are absent.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from ml.forecasting.baselines import advection_grid, persistence_grid, shifted_iou
from ml.verification.scores import cat_scores, contingency
from scripts.run_multi_event import EVENTS, block_bootstrap, circular_block_indices, csi_bias

M = Path("data/processed/multi_event")
NEW = [e for e in EVENTS if e != "E8_20260514"]
needs_multi = pytest.mark.skipif(not (M / "multi_event_provenance.json").exists(), reason="multi-event not run")
h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _used():
    return json.loads((M / "multi_event_provenance.json").read_text())["events_used"]


# ---------------- unit ----------------

def test_circular_blocks_are_contiguous_and_cover_n():
    idx = circular_block_indices(10, 4, np.random.default_rng(0))
    assert len(idx) == 10 and idx.min() >= 0 and idx.max() < 10
    for b in range(0, 8, 4):                              # every full block is a run of consecutive (mod n) issues
        assert all((idx[b + i + 1] - idx[b + i]) % 10 == 1 for i in range(3))


def test_block_bootstrap_degenerate_and_deterministic():
    same = np.tile([[2.0, 1.0, 1.0]], (24, 1))            # identical issue rows -> every resample gives CSI 0.5
    bs = block_bootstrap({"persistence": same, "pysteps_advection": same}, 50, 12, 1)
    assert np.allclose(bs["CSI_persistence"], 0.5) and np.allclose(bs["CSI_diff"], 0.0)
    rnd = np.random.default_rng(3).integers(0, 9, (30, 3)).astype(float)
    a = block_bootstrap({"persistence": rnd, "pysteps_advection": rnd[::-1]}, 100, 12, 7)
    b = block_bootstrap({"persistence": rnd, "pysteps_advection": rnd[::-1]}, 100, 12, 7)
    assert all(np.array_equal(a[k], b[k], equal_nan=True) for k in a)
    assert csi_bias(np.array([2.0, 1.0, 1.0])) == (0.5, 1.0)


def test_shifted_iou_off_grid_shift_is_zero():
    # Phase-4 fix: on 4 May a long-lead constant-velocity forecast shifted a cell > grid size and crashed.
    a = np.zeros((6, 8), bool); a[1:3, 1:3] = True
    assert shifted_iou(a, a, (6, 0)) == 0.0 and shifted_iou(a, a, (0, -8)) == 0.0
    assert shifted_iou(a, np.zeros_like(a), (9, 9)) != shifted_iou(a, np.zeros_like(a), (9, 9))  # NaN: empty union
    assert shifted_iou(a, a, (0, 0)) == 1.0


# ---------------- selection rule / data ----------------

def test_phase4_events_follow_selection_rule():
    cfg = yaml.safe_load(Path("config/events.yaml").read_text())
    dates = {e: date.fromisoformat(cfg[e]["date"]) for e in EVENTS}
    for e in NEW:
        assert all(abs((dates[e] - dates[o]).days) > 1 for o in EVENTS if o != e)   # not within +/-1 day
        st = json.loads(Path(f"data/raw/hail_reports/geocoded_{cfg[e]['date']}.json").read_text())
        inside = [s for s in st if s["lat"] and 26 <= s["lat"] <= 34 and 72 <= s["lon"] <= 84]
        assert len(inside) >= 2
        assert cfg[e]["truth_url"] == cfg["E8_20260514"]["truth_url"]              # same archived IMD report


@pytest.mark.parametrize("ev", NEW)
def test_raw_files_match_manifest(ev):
    import xarray as xr
    cube = Path(f"data/interim/grid2km/{ev}.nc")
    if not cube.exists():
        pytest.skip("cube not built")
    man = json.loads(Path("data/raw/cpc_merged_ir/manifest.json").read_text())
    used = json.loads(xr.open_dataset(cube).attrs["raw_sha256"])
    assert len(used) == 24
    for name, digest in used.items():
        assert man[name]["sha256"] == digest == h(f"data/raw/cpc_merged_ir/{name}")


# ---------------- identical protocol ----------------

@needs_multi
def test_identical_protocol_across_events():
    cfg = h("config/baseline.yaml")
    for ev in _used():
        prov = json.loads(Path(f"data/processed/{ev}/baseline/baseline_provenance.json").read_text())
        assert prov["inputs"]["config/baseline.yaml"] == cfg
        assert prov["fitted_parameters"].startswith("none")
        run = json.loads(Path(f"data/processed/{ev}/tracking_v2_none/run_summary.json").read_text())
        assert run["inputs"]["config/tracking_v2.yaml"] == h("config/tracking_v2.yaml")


@needs_multi
def test_both_methods_scored_on_identical_pixels():
    for ev in _used():
        pi = pd.read_csv(f"data/processed/{ev}/baseline/grid_metrics_per_issue.csv")
        pi["n"] = pi[["H", "M", "F", "CN"]].sum(axis=1)
        piv = pi.pivot_table(index=["issue_time_utc", "lead_min"], columns="method", values="n")
        assert (piv["persistence"] == piv["pysteps_advection"]).all()


@needs_multi
@pytest.mark.parametrize("ev", NEW)
def test_one_new_event_score_recomputed_from_cube(ev):
    import xarray as xr
    if ev not in _used():
        pytest.skip("event not used")
    cfg = yaml.safe_load(Path("config/baseline.yaml").read_text())
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    bt, dom = ds["bt"].values, ds["in_domain"].values
    k, L = 20, 2
    fp, (fa, _) = persistence_grid(bt, k, 12), advection_grid(bt, k, 12, cfg)
    obs = bt[k + L]
    valid = dom & np.isfinite(obs) & np.isfinite(fp[L - 1]) & np.isfinite(fa[L - 1])
    pi = pd.read_csv(f"data/processed/{ev}/baseline/grid_metrics_per_issue.csv")
    t = str(pd.Timestamp(ds.time.values[k]))
    for m, fc in (("persistence", fp[L - 1]), ("pysteps_advection", fa[L - 1])):
        ct = contingency(np.isfinite(fc) & (fc < 235.0), np.isfinite(obs) & (obs < 235.0), valid)
        row = pi[(pi["method"] == m) & (pi["issue_time_utc"] == t) & (pi["lead_min"] == L * 30)].iloc[0]
        assert {k2: int(row[k2]) for k2 in ct} == ct


# ---------------- reproducibility of outputs ----------------

@needs_multi
def test_per_event_outputs_match_provenance():
    for ev in _used():
        b = Path(f"data/processed/{ev}/baseline")
        prov = json.loads((b / "baseline_provenance.json").read_text())
        for name, digest in prov["outputs"].items():
            assert h(b / name) == digest


@needs_multi
def test_multi_event_outputs_match_provenance():
    prov = json.loads((M / "multi_event_provenance.json").read_text())
    for name, digest in prov["outputs"].items():
        assert h(M / name) == digest
    for rel, digest in prov["inputs"].items():
        assert h(Path("data/processed") / rel) == digest


@needs_multi
def test_cross_event_pooled_csi_equals_summed_contingency():
    bl = pd.read_csv(M / "event_metrics_by_lead.csv")
    cross = pd.read_csv(M / "cross_event_by_lead.csv").set_index("lead_min")
    for (m, L), g in bl.groupby(["method", "lead_min"]):
        s = cat_scores(*[int(v) for v in g[["H", "M", "F", "CN"]].sum().values])
        assert s["CSI"] == pytest.approx(cross.loc[L, f"CSI_pooled_{m}"], abs=1e-12)
    # per-event pooled values equal the sum of that event's per-issue contingency tables
    for ev in _used():
        pi = pd.read_csv(f"data/processed/{ev}/baseline/grid_metrics_per_issue.csv")
        tot = pi.groupby(["method", "lead_min"])[["H", "M", "F", "CN"]].sum()
        e = bl[bl["event"] == ev].set_index(["method", "lead_min"])[["H", "M", "F", "CN"]]
        assert (tot.loc[e.index] == e).all().all()


@needs_multi
def test_e8_phase1_to_3_outputs_unchanged():
    P = Path("data/processed/E8_20260514")
    assert h(P / "cells_summary.csv").startswith("e14e0e7e")
    assert h(P / "cells_per_frame.csv").startswith("f3e9a4c6")
    prov = json.loads((P / "baseline/baseline_provenance.json").read_text())
    for name in ("grid_metrics_by_lead.csv", "grid_metrics_per_issue.csv"):
        assert h(P / "baseline" / name) == prov["outputs"][name]
