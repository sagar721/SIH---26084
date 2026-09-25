"""Phase-2 evaluation figures from the saved baseline outputs (no recomputation of scores).

  python -m scripts.make_baseline_figures --event E8_20260514
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from scripts.make_figures import _graticule, _km_extent, ir_cmap

COL = {"persistence": "#6B6457", "pysteps_advection": "#1F6FB2", "constant_velocity": "#C9822B",
       "field_advection": "#1F6FB2"}
IST = pd.Timedelta(hours=5, minutes=30)


def fig_grid_skill(grid: pd.DataFrame, per_issue: pd.DataFrame, out: Path, label: str = "E8 14 May 2026") -> Path:
    fig, axs = plt.subplots(2, 2, figsize=(10, 7), dpi=150, sharex=True)
    for m, g in grid.groupby("method"):
        c = COL[m]
        pi = per_issue[per_issue["method"] == m].groupby("lead_min")["CSI"]
        axs[0, 0].fill_between(pi.quantile(0.25).index, pi.quantile(0.25), pi.quantile(0.75), color=c, alpha=0.15, lw=0)
        axs[0, 0].plot(g["lead_min"], g["CSI"], "o-", color=c, ms=3, label=f"{m} (pooled; band = per-issue IQR)")
        axs[0, 1].plot(g["lead_min"], g["FSS_20km"], "o-", color=c, ms=3, label=f"{m} 20 km")
        axs[0, 1].plot(g["lead_min"], g["FSS_40km"], "s--", color=c, ms=3, label=f"{m} 40 km")
        axs[1, 0].plot(g["lead_min"], g["POD"], "o-", color=c, ms=3, label=f"{m} POD")
        axs[1, 0].plot(g["lead_min"], g["FAR"], "x--", color=c, ms=4, label=f"{m} FAR")
        axs[1, 1].plot(g["lead_min"], g["bias"], "o-", color=c, ms=3, label=m)
    th = grid[grid["method"] == "persistence"]
    axs[0, 1].plot(th["lead_min"], th["FSS_useful_threshold_20km"], ":", color="k", lw=0.8, label="useful: 0.5 + f0/2")
    axs[1, 1].axhline(1.0, color="k", lw=0.6)
    ax2 = axs[1, 1].twinx()
    ax2.bar(th["lead_min"], th["excluded_frac_mean"], width=12, color="0.85", zorder=0)
    ax2.set_ylabel("excluded (unscorable) frac", fontsize=7); ax2.set_ylim(0, 1); ax2.tick_params(labelsize=6)
    axs[1, 1].set_zorder(ax2.get_zorder() + 1); axs[1, 1].patch.set_visible(False)
    for ax, t in zip(axs.flat, ["CSI (BT < 235 K)", "FSS (BT < 235 K)", "POD / FAR", "Frequency bias (bars: excluded frac)"]):
        ax.set_title(t, fontsize=8, loc="left"); ax.tick_params(labelsize=6); ax.legend(fontsize=5.5); ax.grid(alpha=0.3)
    for ax in axs[1]:
        ax.set_xlabel("lead time (min)", fontsize=7)
    n = int(grid["n_issue_times"].max())
    fig.suptitle(f"Grid baselines, {label}: persistence vs pySTEPS advection — {n} issue times (01:00–23:00 UTC), "
                 "30-min leads, same scored pixels for both methods", fontsize=8, x=0.01, ha="left")
    fig.text(0.01, 0.005, "Single event, one day: no bootstrap-by-day CIs here (cross-event uncertainty: docs/MULTI_EVENT.md). "
             "Data: NOAA/NCEP/CPC merged IR.", fontsize=6)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_object(obj: pd.DataFrame, out: Path) -> Path:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4), dpi=150)
    for m, g in obj.groupby("method"):
        c = COL[m]; ls = "--" if m == "constant_velocity" else "-"
        a1.fill_between(g["lead_min"], g["centroid_err_km_p25"], g["centroid_err_km_p75"], color=c, alpha=0.12, lw=0)
        a1.plot(g["lead_min"], g["centroid_err_km_median"], "o" + ls, color=c, ms=3, label=m)
    g = obj[obj["method"] == "persistence"]
    a2.plot(g["lead_min"], g["survival_frac"], "o-", color="k", ms=3)
    for x, y, n in zip(g["lead_min"], g["survival_frac"], g["n_survived"]):
        a2.text(x, y + 0.02, str(n), fontsize=5, ha="center")
    a1.set_title("Centroid error of surviving cells (median, IQR band)", fontsize=8, loc="left")
    a1.set_ylabel("km", fontsize=7); a2.set_ylabel("fraction of cells still tracked", fontsize=7)
    a2.set_title("Survival (labels: n cells scored)", fontsize=8, loc="left")
    for ax in (a1, a2):
        ax.set_xlabel("lead time (min)", fontsize=7); ax.tick_params(labelsize=6); ax.grid(alpha=0.3)
    a1.legend(fontsize=6)
    fig.suptitle("Object baselines — DIAGNOSTIC ONLY: tracked positions are dominated by centroid jitter "
                 "(see docs/BASELINE_EVAL.md §5)", fontsize=8, x=0.01, ha="left", color="#B23A2E")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_example(ds: xr.Dataset, fc: xr.Dataset, issue_idx: int, leads: list[int], thr: float, out: Path) -> Path:
    cmap, norm = ir_cmap()
    ext = _km_extent(ds)
    t0 = pd.Timestamp(fc.issue_time.values[issue_idx])
    k = int(np.where(ds.time.values == fc.issue_time.values[issue_idx])[0][0])
    fig, axs = plt.subplots(len(leads), 3, figsize=(12, 3.4 * len(leads)), dpi=140)
    for r, L in enumerate(leads):
        li = int(np.where(fc.lead_min.values == L)[0][0])
        panels = [(ds.bt.values[k], f"persistence = observed at issue {t0:%H:%M} UTC"),
                  (fc.bt_forecast.values[issue_idx, li], f"pySTEPS advection, +{L} min"),
                  (ds.bt.values[k + L // 30], f"observed at {t0 + pd.Timedelta(minutes=L):%H:%M} UTC (+{L} min)")]
        obs = ds.bt.values[k + L // 30]
        for c, (fld, title) in enumerate(panels):
            ax = axs[r, c]
            ax.imshow(fld, origin="lower", extent=ext, cmap=cmap, norm=norm)
            ax.contour(ds.x / 1e3, ds.y / 1e3, np.where(np.isfinite(obs), obs, 999) < thr, levels=[0.5],
                       colors="k", linewidths=0.5)
            ax.contour(ds.x / 1e3, ds.y / 1e3, ds.in_domain.values.astype(float), levels=[0.5], colors="k",
                       linewidths=0.6, linestyles="--")
            _graticule(ax, ds.attrs["crs_proj4"])
            ax.set_title(title, fontsize=7, loc="left"); ax.tick_params(labelsize=5)
    fig.suptitle(f"Example forecasts issued {t0:%Y-%m-%d %H:%M} UTC ({t0 + IST:%H:%M} IST). Black contour = OBSERVED "
                 f"BT < {thr:.0f} K at the valid time (same in every panel of a row). Pink = missing/unknown "
                 "(incl. inflow from outside the grid).", fontsize=8, x=0.01, ha="left")
    fig.text(0.01, 0.003, "Issue time chosen by rule: largest in-domain area < 235 K among issue times with a +180 min "
             "observation. Data: NOAA/NCEP/CPC merged IR. Boundaries omitted.", fontsize=6)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    ev = ap.parse_args().event
    base = Path(f"data/processed/{ev}/baseline")
    figs = Path("data/figures")
    grid = pd.read_csv(base / "grid_metrics_by_lead.csv")
    per_issue = pd.read_csv(base / "grid_metrics_per_issue.csv")
    obj = pd.read_csv(base / "object_metrics_by_lead.csv")
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    fc = xr.open_dataset(base / "advection_forecasts.nc")
    thr = 235.0
    # Issue-time rule: largest in-domain area < 235 K among issue times with a +180 min observation.
    cold = ((ds.bt < thr) & ds.in_domain).sum(("y", "x")).to_series()
    ok = [i for i, t in enumerate(pd.to_datetime(fc.issue_time.values)) if t + pd.Timedelta(minutes=180) <= pd.Timestamp(ds.time.values[-1])]
    issue_idx = max(ok, key=lambda i: cold.loc[fc.issue_time.values[i]])
    label = f"{ev.split('_')[0]} {pd.Timestamp(ds.time.values[0]):%-d %b %Y}"
    print(fig_grid_skill(grid, per_issue, figs / f"{ev}_fig5_grid_skill_vs_lead.png", label))
    print(fig_object(obj, figs / f"{ev}_fig6_object_diagnostic.png"))
    print(fig_example(ds, fc, issue_idx, [60, 180], thr, figs / f"{ev}_fig7_example_forecast.png"))


if __name__ == "__main__":
    main()
