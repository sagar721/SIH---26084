"""Raw CPC files for an event window -> QC'd BT cube on the 2 km LAEA grid (NetCDF).

Usage: python -m pipelines.preprocess.build_cube --event E8_20260514
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import xarray as xr
import yaml

from pipelines.ingest.cpc_merged_ir import RAW_DIR, hourly_filename
from pipelines.preprocess.decode import SOURCE_GRID, read_file
from pipelines.preprocess.gapfill import MAX_GAP_PX, fill_small_gaps
from pipelines.preprocess.qc import frame_qc, times_monotonic
from pipelines.preprocess.regrid import build_target_grid, load_domain, regrid_window, source_window

OUT_DIR = Path("data/interim/grid2km")


def build(event_key: str) -> Path:
    ev = yaml.safe_load(Path("config/events.yaml").read_text())[event_key]
    start = datetime.fromisoformat(ev["window_start_utc"].replace("Z", ""))
    end = datetime.fromisoformat(ev["window_end_utc"].replace("Z", ""))
    return build_window(event_key, start, end)


def build_window(event_key: str, start: datetime, end: datetime) -> Path:
    """Same processing for any UTC window (Phase 6 uses it for non-event training/validation days)."""
    domain = load_domain()
    tgt = build_target_grid(domain)
    manifest = json.loads((RAW_DIR / "manifest.json").read_text())

    rs, cs, row, col = source_window(SOURCE_GRID, tgt)
    times, frames, filled, qcs, sources, raw_missing = [], [], [], [], [], []
    hour = start.replace(minute=0)
    while hour <= end:
        path = RAW_DIR / hourly_filename(hour)
        ftimes, fields = read_file(path)
        for t, f in zip(ftimes, fields):
            if start <= t <= end:
                sub = f[rs, cs]
                sub_filled, fill_mask = fill_small_gaps(sub)
                bt = regrid_window(sub_filled, row, col)
                fill_on_grid = regrid_window(fill_mask.astype(np.float32), row, col, min_weight=0.0) > 0
                times.append(t)
                frames.append(bt)
                filled.append(fill_on_grid & tgt.in_domain)
                raw_missing.append(float(np.isnan(regrid_window(sub, row, col))[tgt.in_domain].mean()))
                qcs.append(frame_qc(bt, tgt.in_domain))
                sources.append(path.name)
        hour += timedelta(hours=1)
    if not times_monotonic(times):
        raise ValueError("frame times are not strictly increasing")

    ds = xr.Dataset(
        {
            "bt": (("time", "y", "x"), np.stack(frames), {"units": "K", "long_name": "merged IR brightness temperature (~10.7-11 um window)"}),
            "lat": (("y", "x"), tgt.lat.astype(np.float32)),
            "lon": (("y", "x"), tgt.lon.astype(np.float32)),
            "in_domain": (("y", "x"), tgt.in_domain),
            "qc_status": (("time",), np.array([q["status"] for q in qcs])),
            "qc_missing_frac": (("time",), np.array([q["missing_frac"] for q in qcs], dtype=np.float32)),
            "raw_missing_frac": (("time",), np.array(raw_missing, dtype=np.float32)),
            "gapfilled": (("time", "y", "x"), np.stack(filled), {"long_name": "pixel influenced by a filled source gap"}),
            "source_file": (("time",), np.array(sources)),
        },
        coords={"time": np.array(times, dtype="datetime64[ns]"), "y": tgt.y, "x": tgt.x},
        attrs={
            "event": event_key,
            "source": "NOAA/NCEP/CPC Globally Merged IR 4 km, 30 min",
            "crs_proj4": domain["grid"]["crs"],
            "resolution_m": tgt.resolution_m,
            "effective_resolution_note": "source ~4 km; 2 km grid adds no information",
            "regrid_method": "NaN-aware bilinear (normalised weights, min weight 0.5)",
            "gapfill": f"source gaps <= {MAX_GAP_PX} connected native pixels filled from valid 8-neighbours; flagged in 'gapfilled'",
            "raw_sha256": json.dumps({s: manifest[s]["sha256"] for s in sorted(set(sources))}),
        },
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{event_key}.nc"
    ds.to_netcdf(out, encoding={"bt": {"zlib": True, "complevel": 4}, "gapfilled": {"zlib": True}})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    print(build(ap.parse_args().event))


if __name__ == "__main__":
    main()
