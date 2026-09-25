"""Phase-1 tests.

Two kinds:
  * unit tests - check arithmetic on tiny hand-built arrays (test fixtures only; nothing here is
    used as weather data or reported as a result);
  * real-data tests - check the actual downloaded/processed E8 files; skipped if absent.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.tracking.lifecycle import assign_phases, load_phase_rules, movement
from pipelines.ingest.cpc_merged_ir import RAW_DIR, sha256_of
from pipelines.preprocess import decode
from pipelines.preprocess.qc import frame_qc, times_monotonic
from pipelines.preprocess.regrid import build_target_grid, load_domain

EVENT = "E8_20260514"
CUBE = Path(f"data/interim/grid2km/{EVENT}.nc")
PROC = Path(f"data/processed/{EVENT}")
needs_raw = pytest.mark.skipif(not (RAW_DIR / "manifest.json").exists(), reason="raw data not downloaded")
needs_cube = pytest.mark.skipif(not CUBE.exists(), reason="cube not built")
needs_tracks = pytest.mark.skipif(not (PROC / "cells_summary.csv").exists(), reason="tracking not run")


# ---------------- unit tests ----------------

def test_decode_scaling_missing_and_row_flip():
    counts = np.zeros((decode.FIELDS_PER_FILE, decode.NY, decode.NX), dtype=np.uint8)
    counts[0, 0, 0] = 200          # first stored row = northernmost
    counts[0, -1, 0] = decode.MISSING
    bt = decode.decode_bytes(counts.tobytes())
    assert bt.shape == (2, decode.NY, decode.NX)
    assert bt[0, -1, 0] == 275.0   # after flip, the northern row is last (ascending latitude)
    assert np.isnan(bt[0, 0, 0])
    assert bt[1, 5, 5] == 75.0


def test_decode_rejects_wrong_size():
    with pytest.raises(ValueError):
        decode.decode_bytes(b"\x00" * 10)


def test_source_grid_bounds():
    g = decode.SOURCE_GRID
    assert g.lat[0] == pytest.approx(-59.98, abs=0.01) and g.lat[-1] == pytest.approx(60.0, abs=0.05)
    assert g.lon[0] == pytest.approx(0.018, abs=0.001) and g.lon[-1] == pytest.approx(360.0, abs=0.05)


def test_target_grid_covers_domain_at_2km():
    dom = load_domain()
    tg = build_target_grid(dom)
    assert np.allclose(np.diff(tg.x), 2000) and np.allclose(np.diff(tg.y), 2000)
    inside = tg.lat[tg.in_domain]
    assert inside.min() >= dom["lat_min"] and inside.max() <= dom["lat_max"]
    assert tg.lat.min() <= dom["lat_min"] + 0.05 and tg.lat.max() >= dom["lat_max"] - 0.05


def test_movement_one_degree_north_in_one_hour():
    spd, hdg = movement(np.array([30.0, 31.0]), np.array([78.0, 78.0]), np.array([np.nan, 3600.0]))
    assert np.isnan(spd[0])
    assert spd[1] == pytest.approx(110.9, abs=0.5)
    assert hdg[1] == pytest.approx(0.0, abs=0.1)


def test_qc_flags_out_of_range_and_missing():
    ok = np.full((4, 4), 280.0, dtype=np.float32)
    dom = np.ones((4, 4), bool)
    assert frame_qc(ok, dom)["status"] == "OK"
    bad = ok.copy(); bad[0, 0] = 400.0
    assert frame_qc(bad, dom)["status"] == "QC_FAIL"
    miss = ok.copy(); miss[:2] = np.nan
    assert frame_qc(miss, dom)["status"] == "QC_FAIL"
    assert times_monotonic(["2026-05-14T00:00", "2026-05-14T00:30"])
    assert not times_monotonic(["2026-05-14T00:30", "2026-05-14T00:30"])


def test_phase_rules_v0_sequence():
    rules = load_phase_rules()
    rows = pd.DataFrame({
        "min_bt_K":            [265.0, 240.0, 215.0, 214.0, 222.0],
        "d_min_bt_30":         [np.nan, -25.0, -25.0, -1.0, 8.0],
        "area_change_frac_30": [np.nan, 1.0, 0.8, 0.05, -0.3],
        "d_cold_core_30":      [np.nan, 0.0, 400.0, 20.0, -300.0],
    })
    assert assign_phases(rows, rules) == ["Unclassified", "Developing", "Developing", "Mature", "Decaying"]


# ---------------- real-data tests ----------------

@needs_raw
def test_raw_files_match_manifest_checksums():
    manifest = json.loads((RAW_DIR / "manifest.json").read_text())
    assert manifest, "empty manifest"
    for name, rec in manifest.items():
        p = RAW_DIR / name
        assert p.exists(), name
        assert sha256_of(p) == rec["sha256"], name
        assert p.stat().st_size == rec["bytes"], name


@needs_cube
def test_cube_qc_and_timing():
    import xarray as xr
    ds = xr.open_dataset(CUBE)
    # QC must be internally consistent (failures are reported, not hidden): a frame fails only for >5 %
    # residual missing data or out-of-range BT, and gap filling can only reduce missing data.
    assert set(ds.qc_status.values) <= {"OK", "QC_FAIL"}
    fail = ds.qc_status.values == "QC_FAIL"
    assert np.all(ds.qc_missing_frac.values[fail] > 0.05)
    assert np.all(ds.qc_missing_frac.values <= ds.raw_missing_frac.values + 1e-6)
    assert fail.sum() <= len(fail) // 4, "more than a quarter of frames fail QC"
    steps = np.diff(ds.time.values) / np.timedelta64(1, "m")
    assert np.all(steps == 30)
    bt = ds.bt.where(ds.in_domain).values
    assert np.nanmin(bt) >= 170 and np.nanmax(bt) <= 330
    recorded = json.loads(ds.attrs["raw_sha256"])
    manifest = json.loads((RAW_DIR / "manifest.json").read_text())
    assert all(manifest[k]["sha256"] == v for k, v in recorded.items())


@needs_tracks
def test_tracks_are_physical():
    pf = pd.read_csv(PROC / "cells_per_frame.csv")
    sm = pd.read_csv(PROC / "cells_summary.csv")
    assert (sm["n_frames"] >= 2).all()
    assert (sm["n_frames"] >= 4).any(), "no cell tracked for >= 2 h"
    assert not pf.duplicated(["cell", "frame"]).any()
    assert (pf["area_km2"] >= 0).all()
    # Linker invariant: tobac feature positions move at most v_max * dt per step (+1 px tolerance).
    import yaml
    cfg = yaml.safe_load(Path("config/tracking.yaml").read_text())
    f = pd.read_parquet(PROC / "features.parquet")
    f = f[f["cell"] != -1].sort_values(["cell", "frame"])
    step_px = np.hypot(f.groupby("cell")["hdim_1"].diff(), f.groupby("cell")["hdim_2"].diff()).dropna()
    assert step_px.max() * 2000 <= cfg["v_max_m_s"] * 1800 + 2000
    # Derived segment-centroid motion is noisier (shape changes); sanity-check its median only.
    assert pf["speed_kmh"].dropna().median() < cfg["v_max_m_s"] * 3.6
    assert set(pf["phase"]) <= {"Initiation", "Developing", "Mature", "Decaying", "Unclassified"}
