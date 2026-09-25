"""Regrid source lat/lon BT onto the common 2 km Lambert Azimuthal Equal-Area grid.

The grid is defined in ``config/domain.yaml``. BT uses NaN-aware bilinear interpolation
(normalised weights): a target pixel is valid if at least half of its bilinear weight falls on valid
source pixels, otherwise NaN. Small source gaps are filled beforehand by ``gapfill`` and flagged.
Regridding a ~4 km source to 2 km adds no information: the effective resolution stays ~4 km.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml
from pyproj import CRS, Transformer
from scipy.ndimage import map_coordinates

from pipelines.preprocess.decode import SourceGrid


@dataclass(frozen=True)
class TargetGrid:
    crs: CRS
    x: np.ndarray  # (nx,) metres, ascending
    y: np.ndarray  # (ny,) metres, ascending
    lon: np.ndarray  # (ny, nx)
    lat: np.ndarray  # (ny, nx)
    in_domain: np.ndarray  # (ny, nx) bool: inside the lat/lon box
    resolution_m: float


def load_domain(path: Path = Path("config/domain.yaml")) -> dict:
    return yaml.safe_load(path.read_text())


def build_target_grid(domain: dict) -> TargetGrid:
    crs = CRS.from_proj4(domain["grid"]["crs"])
    res = float(domain["grid"]["resolution_m"])
    to_xy = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    # Project the densified lat/lon box boundary to get the enclosing LAEA rectangle.
    lons = np.linspace(domain["lon_min"], domain["lon_max"], 200)
    lats = np.linspace(domain["lat_min"], domain["lat_max"], 200)
    edge_lon = np.concatenate([lons, np.full_like(lats, domain["lon_max"]), lons[::-1], np.full_like(lats, domain["lon_min"])])
    edge_lat = np.concatenate([np.full_like(lons, domain["lat_min"]), lats, np.full_like(lons, domain["lat_max"]), lats[::-1]])
    ex, ey = to_xy.transform(edge_lon, edge_lat)
    x = np.arange(np.floor(ex.min() / res) * res, np.ceil(ex.max() / res) * res + res / 2, res)
    y = np.arange(np.floor(ey.min() / res) * res, np.ceil(ey.max() / res) * res + res / 2, res)
    xx, yy = np.meshgrid(x, y)
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = to_ll.transform(xx, yy)
    in_dom = ((lat >= domain["lat_min"]) & (lat <= domain["lat_max"]) &
              (lon >= domain["lon_min"]) & (lon <= domain["lon_max"]))
    return TargetGrid(crs=crs, x=x, y=y, lon=lon, lat=lat, in_domain=in_dom, resolution_m=res)


def source_window(src: SourceGrid, tgt: TargetGrid) -> tuple[slice, slice, np.ndarray, np.ndarray]:
    """Row/col slices of the source covering the target, plus fractional target coords inside the window."""
    dlon = src.lon[1] - src.lon[0]
    dlat = src.lat[1] - src.lat[0]
    col = (np.mod(tgt.lon, 360.0) - src.lon[0]) / dlon
    row = (tgt.lat - src.lat[0]) / dlat
    r0, r1 = int(np.floor(row.min())) - 1, int(np.ceil(row.max())) + 2
    c0, c1 = int(np.floor(col.min())) - 1, int(np.ceil(col.max())) + 2
    return slice(r0, r1), slice(c0, c1), row - r0, col - c0


def regrid_window(sub: np.ndarray, row: np.ndarray, col: np.ndarray, min_weight: float = 0.5) -> np.ndarray:
    """NaN-aware bilinear interpolation of a cropped source window at fractional (row, col)."""
    valid = np.isfinite(sub)
    num = map_coordinates(np.where(valid, sub, 0.0).astype(np.float64), [row, col], order=1, mode="constant", cval=0.0)
    wt = map_coordinates(valid.astype(np.float64), [row, col], order=1, mode="constant", cval=0.0)
    out = np.full(row.shape, np.nan)
    ok = wt >= min_weight
    out[ok] = num[ok] / wt[ok]
    return out.astype(np.float32)


def regrid(field: np.ndarray, src: SourceGrid, tgt: TargetGrid) -> np.ndarray:
    """Bilinear lat/lon -> target. ``field`` is (ny_src, nx_src) with ascending lat/lon axes."""
    rs, cs, row, col = source_window(src, tgt)
    return regrid_window(field[rs, cs], row, col)
