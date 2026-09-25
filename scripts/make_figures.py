"""Four Phase-1 figures from real data (satellite frame, detected cells, trajectories, lifecycle curve).

International/state boundaries are intentionally NOT drawn: official Indian map display must use
Survey of India boundaries (licensed source NEEDS VERIFICATION). Orientation is given by a lat/lon
graticule and the geocoded IMD hail-report stations.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Transformer

IST = pd.Timedelta(hours=5, minutes=30)
MISSING_COLOR = "#E377C2"
PHASE_COLORS = {"Initiation": "#2A9D8F", "Developing": "#E9A23B", "Mature": "#C0392B",
                "Decaying": "#7D6B91", "Unclassified": "#BBBBBB"}


def ir_cmap() -> tuple[mcolors.Colormap, mcolors.Normalize]:
    """Enhanced IR: greys for warm (> 253 K), colour for cold cloud tops (190-253 K)."""
    vmin, split, vmax = 190.0, 253.0, 320.0
    n_cold = int(256 * (split - vmin) / (vmax - vmin))
    cold = plt.get_cmap("turbo_r")(np.linspace(0.0, 0.85, n_cold))[::-1][::-1]
    warm = plt.get_cmap("Greys")(np.linspace(0.75, 0.05, 256 - n_cold))
    cmap = mcolors.ListedColormap(np.vstack([cold, warm]))
    cmap.set_bad(MISSING_COLOR)  # missing source pixels: never rendered as white/cloud
    return cmap, mcolors.Normalize(vmin, vmax)


def _km_extent(ds: xr.Dataset) -> list[float]:
    r = float(ds.attrs["resolution_m"]) / 2
    return [(ds.x.values[0] - r) / 1e3, (ds.x.values[-1] + r) / 1e3, (ds.y.values[0] - r) / 1e3, (ds.y.values[-1] + r) / 1e3]


def _graticule(ax, crs: str, lat_range=(24, 36), lon_range=(70, 86), step=2) -> None:
    to_xy = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    for lat in range(lat_range[0], lat_range[1] + 1, step):
        lons = np.linspace(*lon_range, 200)
        x, y = to_xy.transform(lons, np.full_like(lons, lat))
        ax.plot(x / 1e3, y / 1e3, color="k", lw=0.3, alpha=0.5)
        ax.text(x[-1] / 1e3, y[-1] / 1e3, f"{lat}°N", fontsize=6, alpha=0.7, clip_on=True)
    for lon in range(lon_range[0], lon_range[1] + 1, step):
        lats = np.linspace(*lat_range, 200)
        x, y = to_xy.transform(np.full_like(lats, lon), lats)
        ax.plot(x / 1e3, y / 1e3, color="k", lw=0.3, alpha=0.5)
        ax.text(x[0] / 1e3, y[0] / 1e3, f"{lon}°E", fontsize=6, alpha=0.7, clip_on=True)


def _stations(ax, stations: list[dict], crs: str, label=True) -> None:
    to_xy = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    for s in stations:
        if s.get("lat") is None:
            continue
        x, y = to_xy.transform(s["lon"], s["lat"])
        ax.plot(x / 1e3, y / 1e3, marker="^", ms=5, mfc="white", mec="black", mew=0.8, zorder=5)
        if label:
            ax.text(x / 1e3 + 8, y / 1e3 + 8, s["name"], fontsize=6, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))


def _frame_axes(ds, title):
    fig, ax = plt.subplots(figsize=(10, 7.4), dpi=150)
    ax.set_title(title, fontsize=9, loc="left")
    ax.set_xlabel("x (km, LAEA 30°N 78°E)", fontsize=7)
    ax.set_ylabel("y (km)", fontsize=7)
    ax.tick_params(labelsize=6)
    return fig, ax


def _footer(fig, ds):
    fig.text(0.01, 0.005, f"Data: {ds.attrs['source']} (NOAA). Grid 2 km LAEA; effective resolution ~4 km. Pink = missing "
             "source data. Triangles: IMD RMC New Delhi hail reports for 14-05-2026. Boundaries omitted (see docs/FIRST_EVENT.md).",
             fontsize=6, alpha=0.8)


def fig_satellite(ds, t_idx, stations, out: Path) -> Path:
    cmap, norm = ir_cmap()
    t = pd.Timestamp(ds.time.values[t_idx])
    fig, ax = _frame_axes(ds, f"Merged IR brightness temperature — {t:%Y-%m-%d %H:%M} UTC ({t + IST:%H:%M} IST)")
    im = ax.imshow(ds.bt.isel(time=t_idx).values, origin="lower", extent=_km_extent(ds), cmap=cmap, norm=norm)
    ax.contour(ds.x / 1e3, ds.y / 1e3, ds.in_domain.values.astype(float), levels=[0.5], colors="k", linewidths=0.8, linestyles="--")
    _graticule(ax, ds.attrs["crs_proj4"])
    _stations(ax, stations, ds.attrs["crs_proj4"])
    fig.colorbar(im, ax=ax, shrink=0.8, label="BT (K)")
    _footer(fig, ds)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_cells(ds, mask, per_frame, t_idx, stations, out: Path) -> Path:
    cmap, norm = ir_cmap()
    t = pd.Timestamp(ds.time.values[t_idx])
    fig, ax = _frame_axes(ds, f"Detected cells (tobac, segmentation < 245 K) — {t:%Y-%m-%d %H:%M} UTC ({t + IST:%H:%M} IST)")
    ax.imshow(ds.bt.isel(time=t_idx).values, origin="lower", extent=_km_extent(ds), cmap=cmap, norm=norm, alpha=0.55)
    lab = mask.isel(time=t_idx).values
    fr = per_frame[per_frame["frame"] == t_idx]
    for _, r in fr.iterrows():
        seg = (lab == int(r["feature"])).astype(float)
        if seg.any():
            ax.contour(ds.x / 1e3, ds.y / 1e3, seg, levels=[0.5], colors=[PHASE_COLORS[r["phase"]]], linewidths=1.0)
        ax.plot(r["x_m"] / 1e3, r["y_m"] / 1e3, "k+", ms=4 if seg.any() else 2, alpha=1 if seg.any() else 0.4)
        if seg.any():  # label only cells with a < 245 K segment; warmer features get an unlabelled marker
            ax.text(r["x_m"] / 1e3 + 5, r["y_m"] / 1e3 + 5, f"#{int(r['cell'])}", fontsize=6)
    for p, c in PHASE_COLORS.items():
        ax.plot([], [], color=c, label=p)
    ax.legend(fontsize=6, loc="lower right", title="Phase (rules v0)", title_fontsize=6)
    _graticule(ax, ds.attrs["crs_proj4"])
    _stations(ax, stations, ds.attrs["crs_proj4"], label=False)
    _footer(fig, ds)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_trajectories(ds, per_frame, summary, stations, min_lifetime_min, out: Path, deep_K: float = 235.0) -> Path:
    long = summary["lifetime_min"] >= min_lifetime_min
    deep = long & (summary["min_bt_K"] < deep_K)
    fig, ax = _frame_axes(ds, f"Cell trajectories, {pd.Timestamp(ds.time.values[0]):%-d %b %Y} — cells living ≥ {min_lifetime_min / 60:.0f} h: "
                              f"deep convective (min BT < {deep_K:.0f} K, n={int(deep.sum())}) coloured by time; "
                              f"others (n={int((long & ~deep).sum())}) grey")
    ax.imshow(ds.bt.min("time").values, origin="lower", extent=_km_extent(ds), cmap="Greys", vmin=190, vmax=320, alpha=0.5)
    t0 = pd.Timestamp(ds.time.values[0])
    tnorm = mcolors.Normalize(0, 24)
    for cell in summary.loc[long & ~deep, "cell"]:
        g = per_frame[per_frame["cell"] == cell].sort_values("time")
        ax.plot(g["x_m"] / 1e3, g["y_m"] / 1e3, color="0.55", lw=0.4, alpha=0.5)
    for cell in summary.loc[deep, "cell"]:
        g = per_frame[per_frame["cell"] == cell].sort_values("time")
        hrs = (pd.to_datetime(g["time"]) - t0).dt.total_seconds() / 3600
        ax.plot(g["x_m"] / 1e3, g["y_m"] / 1e3, color="k", lw=0.7, alpha=0.8)
        ax.scatter(g["x_m"] / 1e3, g["y_m"] / 1e3, c=hrs, cmap="viridis", norm=tnorm, s=9, zorder=3)
        ax.annotate("", xy=(g["x_m"].iloc[-1] / 1e3, g["y_m"].iloc[-1] / 1e3),
                    xytext=(g["x_m"].iloc[-2] / 1e3, g["y_m"].iloc[-2] / 1e3), arrowprops=dict(arrowstyle="->", lw=0.7))
        ax.text(g["x_m"].iloc[-1] / 1e3 + 6, g["y_m"].iloc[-1] / 1e3 + 6, f"#{int(cell)}", fontsize=6)
    fig.colorbar(plt.cm.ScalarMappable(norm=tnorm, cmap="viridis"), ax=ax, shrink=0.8, label="hours since 00 UTC")
    _graticule(ax, ds.attrs["crs_proj4"])
    _stations(ax, stations, ds.attrs["crs_proj4"])
    fig.text(0.01, 0.02, "Background: daily minimum BT (K).", fontsize=6)
    _footer(fig, ds)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_lifecycle(per_frame, cell: int, selection_note: str, out: Path) -> Path:
    g = per_frame[per_frame["cell"] == cell].sort_values("time")
    t = pd.to_datetime(g["time"]) + IST
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9, 7), dpi=150, sharex=True)
    a1.plot(t, g["min_bt_K"], "o-", color="#1C2433", ms=3)
    miss = g["touches_missing"].values.astype(bool)
    if miss.any():
        a1.plot(t[miss], g["min_bt_K"][miss], "o", mfc="none", mec=MISSING_COLOR, ms=7, label="segment touches missing data")
    a1.axhline(221, color="#C0392B", lw=0.6, ls="--")
    a1.axhline(235, color="#E9A23B", lw=0.6, ls="--")
    a1.set_ylabel("min BT (K)", fontsize=7)
    a1.invert_yaxis()
    a2.plot(t, g["area_km2"], "o-", ms=3, label="area < 245 K")
    a2.plot(t, g["cold_core_km2"], "s-", ms=3, label="cold core < 221 K")
    a2.set_ylabel("area (km²)", fontsize=7)
    a2.legend(fontsize=6)
    a3.bar(t, g["d_min_bt_30"], width=0.015, color=np.where(g["d_min_bt_30"] < 0, "#2A6FB0", "#B23A2E"))
    a3.axhline(-8, color="k", lw=0.6, ls=":")
    a3.set_ylabel("ΔminBT (K/30 min)", fontsize=7)
    a3.set_xlabel("time (IST)", fontsize=7)
    for ax in (a1, a2, a3):
        ax.tick_params(labelsize=6)
        tt = list(t)
        for k, ph in enumerate(g["phase"]):
            left = tt[k] - pd.Timedelta(minutes=15)
            ax.axvspan(left, left + pd.Timedelta(minutes=30), color=PHASE_COLORS[ph], alpha=0.12, lw=0)
    for p, c in PHASE_COLORS.items():
        a1.fill_between([], [], color=c, alpha=0.3, label=p)
    a1.legend(fontsize=6, ncol=6, loc="lower left", bbox_to_anchor=(0.0, 1.02), title="phase (rules v0, shading)",
              title_fontsize=6, frameon=False)
    fig.suptitle(f"Lifecycle of cell #{cell} — {selection_note}", fontsize=8, x=0.01, ha="left")
    fig.text(0.01, 0.005, "Data: NOAA/NCEP/CPC merged IR (30 min). Rates per 30 min. Phase rules v0 (PROPOSED; D7 pending).",
             fontsize=6, alpha=0.8)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out
