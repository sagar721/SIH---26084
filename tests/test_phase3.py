"""Phase-3 tests: one or more tests per tracking fix, plus "grid metrics unchanged" and causality checks.

Unit tests use tiny hand-built label masks / paths (arithmetic fixtures only). Real-data tests use E8 outputs
and are skipped if they are absent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.tracking.audit import zigzag_fraction
from ml.tracking.overlap_link import LinkConfig, coldness_centroid, families, link_frames, track

EVENT = "E8_20260514"
P = Path(f"data/processed/{EVENT}")
needs_v2 = pytest.mark.skipif(not (P / "tracking_v2_none/run_summary.json").exists(), reason="v2 not run")


def _frames(*masks):
    mask = np.stack(masks)
    ff = {k: sorted(int(i) for i in np.unique(m) if i > 0) for k, m in enumerate(mask)}
    return mask, ff


# ---------------- fix 2: overlap linking ----------------

def test_continuation_keeps_id():
    a = np.zeros((10, 10), int); a[2:5, 2:5] = 1
    b = np.zeros((10, 10), int); b[3:6, 3:6] = 2   # overlaps 1
    mask, ff = _frames(a, b)
    assign, events = track(mask, ff, {}, LinkConfig("none", 0.2))
    assert assign.set_index("feature").loc[1, "cell"] == assign.set_index("feature").loc[2, "cell"]
    assert events.empty


def test_no_overlap_starts_new_cell():
    a = np.zeros((10, 10), int); a[0:2, 0:2] = 1
    b = np.zeros((10, 10), int); b[7:9, 7:9] = 2
    mask, ff = _frames(a, b)
    assign, _ = track(mask, ff, {}, LinkConfig("none", 0.2))
    assert assign["cell"].nunique() == 2


def test_merge_and_split_events_classified_once():
    a = np.zeros((12, 12), int); a[1:4, 1:4] = 1; a[1:4, 6:9] = 2     # two parents
    b = np.zeros((12, 12), int); b[1:4, 1:9] = 3                       # one child covering both -> MERGE
    c = np.zeros((12, 12), int); c[1:4, 1:4] = 4; c[1:4, 6:9] = 5     # splits again -> SPLIT
    mask, ff = _frames(a, b, c)
    assign, events = track(mask, ff, {}, LinkConfig("none", 0.2))
    cell = assign.set_index("feature")["cell"]
    assert cell[3] in (cell[1], cell[2])                 # child continues one parent
    assert list(events["type"]) == ["MERGE", "SPLIT"]    # each extra edge classified exactly once
    fam = families(events, sorted(assign["cell"].unique()))
    assert len(set(fam.values())) == 1                   # all cells in one family


def test_overlap_threshold_is_enforced():
    a = np.zeros((10, 10), int); a[0:5, 0:4] = 1        # 20 px
    b = np.zeros((10, 10), int); b[4:9, 3:7] = 2        # overlaps a in 1 px -> frac 1/20 = 0.05
    edges = link_frames(a, b, None, LinkConfig("none", 0.2))
    assert edges == []
    assert link_frames(a, b, None, LinkConfig("none", 0.05))[0]["overlap_px"] == 1


def test_flow_mode_shifts_parent():
    a = np.zeros((10, 10), int); a[2:4, 0:2] = 1
    b = np.zeros((10, 10), int); b[2:4, 5:7] = 2        # moved 5 px in +x: no Eulerian overlap
    flow = np.zeros((2, 10, 10)); flow[0] = 5.0         # u = +5 px/step
    assert link_frames(a, b, None, LinkConfig("none", 0.2)) == []
    assert link_frames(a, b, flow, LinkConfig("flow", 0.2))[0]["child"] == 2


def test_linking_is_causal():
    a = np.zeros((8, 8), int); a[1:4, 1:4] = 1
    b = np.zeros((8, 8), int); b[2:5, 2:5] = 2
    c1 = np.zeros((8, 8), int); c1[3:6, 3:6] = 3
    c2 = np.zeros((8, 8), int); c2[6:8, 0:2] = 3        # different future
    for fut in (c1, c2):
        mask, ff = _frames(a, b, fut)
        assign, _ = track(mask, ff, {}, LinkConfig("none", 0.2))
        early = assign[assign["frame"] <= 1].set_index("feature")["cell"]
        assert early[1] == early[2]                     # past links do not depend on frame 2


# ---------------- fix 3: coldness-weighted centroid ----------------

def test_coldness_centroid_weights_cold_pixels():
    seg = np.zeros((5, 5), bool); seg[2, 0:5] = True
    bt = np.full((5, 5), 244.0); bt[2, 4] = 200.0       # one very cold pixel at column 4
    r, c = coldness_centroid(seg, bt, 245.0)
    assert r == 2.0 and c > 3.5                         # pulled toward the cold pixel (plain centroid = 2.0)
    assert coldness_centroid(seg, np.full((5, 5), 250.0), 245.0) == (2.0, 2.0)  # no cold weight -> plain


# ---------------- audit metric ----------------

def test_zigzag_counts_reversals_only():
    straight = pd.DataFrame({"cell": 1, "frame": [0, 1, 2, 3], "feature": [1, 2, 3, 4],
                             "x": [0, 10000, 20000, 30000], "y": [0, 0, 0, 0]})
    zig = straight.assign(x=[0, 10000, 0, 10000])
    assert zigzag_fraction(straight)[0] == 0.0 and zigzag_fraction(zig)[0] == 1.0


# ---------------- real data ----------------

@needs_v2
@pytest.mark.parametrize("mode", ["none", "flow"])
def test_v2_tracks_valid(mode):
    import xarray as xr
    import yaml
    cfg = yaml.safe_load(Path("config/tracking_v2.yaml").read_text())
    pf = pd.read_csv(P / f"tracking_v2_{mode}/cells_per_frame.csv")
    mask = xr.open_dataset(P / "mask.nc")["segment_label"].values
    assert not pf.duplicated(["cell", "frame"]).any()
    assert set(pf["feature"]) <= set(np.unique(mask)) - {0}          # fix 1: cold segments only
    assert (pf["centroid_source"] == "coldness").all()               # fix 3
    # fix 2: every continuation step satisfies the overlap rule (Eulerian mode checked without shift)
    if mode == "none":
        s = pf.sort_values(["cell", "frame"])
        s["pfeat"], s["pframe"] = s.groupby("cell")["feature"].shift(), s.groupby("cell")["frame"].shift()
        s = s[s["frame"] - s["pframe"] == 1]
        for r in s.itertuples():
            par, chi = mask[int(r.pframe)] == int(r.pfeat), mask[int(r.frame)] == int(r.feature)
            assert (par & chi).sum() / min(par.sum(), chi.sum()) >= cfg["min_overlap_frac"]


@needs_v2
def test_phase1_and_phase2_outputs_unchanged():
    # Phase-1 lifecycle tables (hashes recorded in docs/FIRST_EVENT.md §3) and Phase-2 grid metrics
    # (hashes in baseline_provenance.json) must be byte-identical: Phase 3 must not touch them.
    h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert h(P / "cells_summary.csv").startswith("e14e0e7e")
    assert h(P / "cells_per_frame.csv").startswith("f3e9a4c6")
    prov = json.loads((P / "baseline/baseline_provenance.json").read_text())
    for name in ("grid_metrics_by_lead.csv", "grid_metrics_per_issue.csv"):
        assert h(P / "baseline" / name) == prov["outputs"][name]


@needs_v2
@pytest.mark.parametrize("mode", ["none", "flow"])
def test_v2_outputs_match_run_hashes(mode):
    run = json.loads((P / f"tracking_v2_{mode}/run_summary.json").read_text())
    for name, digest in run["outputs"].items():
        assert hashlib.sha256((P / f"tracking_v2_{mode}" / name).read_bytes()).hexdigest() == digest
