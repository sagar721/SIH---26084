"""Decode CPC merged-IR hourly files into brightness temperature (K).

Format (from the product descriptor ``merg_4km-pixel.ctl`` on the CPC server):
  * 1-byte unsigned integers, little-endian, two 9896 x 3298 fields per file (HH:00 and HH:30)
  * value = BT - 75 K; 255 = missing
  * XDEF 9896 LINEAR 0.0181891675 0.0363783345   (longitude, 0..360 E)
  * YDEF 3298 LINEAR -59.98181083 0.0363856885   (latitude)
  * OPTIONS yrev -> rows are stored north-to-south
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

NX, NY = 9896, 3298
LON0, DLON = 0.0181891675, 0.0363783345
LAT0, DLAT = -59.98181083, 0.0363856885
OFFSET_K = 75.0
MISSING = 255
FIELDS_PER_FILE = 2
MINUTES_PER_FIELD = 30


@dataclass(frozen=True)
class SourceGrid:
    """Regular lat/lon grid, rows ordered south-to-north after decoding."""
    lon: np.ndarray  # (NX,)
    lat: np.ndarray  # (NY,) ascending


SOURCE_GRID = SourceGrid(lon=LON0 + DLON * np.arange(NX), lat=LAT0 + DLAT * np.arange(NY))


def decode_bytes(raw: bytes) -> np.ndarray:
    """Raw bytes -> float32 array (FIELDS_PER_FILE, NY, NX) in K, rows south-to-north, NaN = missing."""
    expected = FIELDS_PER_FILE * NX * NY
    if len(raw) != expected:
        raise ValueError(f"expected {expected} bytes, got {len(raw)}")
    counts = np.frombuffer(raw, dtype=np.uint8).reshape(FIELDS_PER_FILE, NY, NX)
    bt = counts.astype(np.float32) + OFFSET_K
    bt[counts == MISSING] = np.nan
    return bt[:, ::-1, :]  # yrev: file is north-to-south; flip to ascending latitude


def decompress(path: Path) -> bytes:
    """Unix-compress (.Z, LZW) -> bytes, via the system gzip, which reads .Z."""
    return subprocess.run(["gzip", "-dc", str(path)], check=True, capture_output=True).stdout


def field_times(path: Path) -> list[datetime]:
    """merg_YYYYMMDDHH_4km-pixel.Z -> [HH:00, HH:30] (naive UTC)."""
    stamp = path.name.split("_")[1]
    t0 = datetime.strptime(stamp, "%Y%m%d%H")
    return [t0 + timedelta(minutes=MINUTES_PER_FIELD * k) for k in range(FIELDS_PER_FILE)]


def read_file(path: Path) -> tuple[list[datetime], np.ndarray]:
    return field_times(path), decode_bytes(decompress(path))
