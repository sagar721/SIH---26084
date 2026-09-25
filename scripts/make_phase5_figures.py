"""Phase-5 figures from saved outputs (decomposition, lifecycle reliability, Phase-2/4 forecasts).

  python -m scripts.make_phase5_figures
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

from scripts.lifecycle_reliability import load as load_lifecycle

P5 = Path("data/processed/multi_event/phase5")
FIGS = Path("data/figures")
EVENTS = ["E8_20260514", "E10_20260504", "E11_20260516"]
LAB = {"E8_20260514": "E8 14 May", "E10_20260504": "E10 4 May", "E11_20260516": "E11 16 May"}
THR = 235.0


def fig_decomposition(out: Path) -> Path:
    dec = pd.read_csv(P5 / "decomposition_by_lead.csv")
    em = pd.read_csv("data/processed/multi_event/event_metrics_by_lead.csv")
    fig, axs = plt.subplots(2, 3, figsize=(14, 7), dpi=150, sharex=True)
    for j, ev in enumerate(EVENTS):
        d = dec[dec["event"] == ev].sort_values("lead_min")
        ax = axs[0, j]
        ax.plot(d["lead_min"], d["log_bias"], "k-o", ms=3, label="log bias (scored region V)")
        ax.plot(d["lead_min"], d["log_E"], "-s", color="#B23A2E", ms=3, label="log E: edge exclusion")
        ax.plot(d["lead_min"], d["log_C"], "-^", color="#6B6457", ms=3, label="log C: advected-area change")
        ax.plot(d["lead_min"], d["log_G"], "-D", color="#1F6FB2", ms=3, label="log G: unchanged intensity (domain)")
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title(f"{LAB[ev]}: bias = E x C x G (exact)", fontsize=8, loc="left")
        ax2 = axs[1, j]
        p = em[(em["event"] == ev) & (em["method"] == "persistence")].sort_values("lead_min")
        ax2.plot(p["lead_min"], p["CSI"], "-o", color="#6B6457", ms=3, label="persistence")
        ax2.plot(d["lead_min"], d["CSI_V"], "-o", color="#1F6FB2", ms=3, label="pySTEPS (Phase-4 score)")
        ax2.plot(d["lead_min"], d["CSI_Dedge"], "--", color="#1F6FB2", lw=1, label="pySTEPS, edge scored as no-event")
        ax2.plot(d["lead_min"], d["CSI_oracle"], ":", color="#2A9D8F", lw=1.5,
                 label="ORACLE area-matched pySTEPS (uses future; bound)")
        ax2.set_title("CSI (BT < 235 K)", fontsize=8, loc="left"); ax2.set_xlabel("lead (min)", fontsize=7)
        for a in (ax, ax2):
            a.tick_params(labelsize=6); a.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=5.5); axs[1, 0].legend(fontsize=5.5)
    fig.suptitle("Phase 5 task 1 — where the pySTEPS frequency-bias growth comes from. E > 1: observed events sit "
                 "disproportionately in the unscorable inflow edge; G: observed domain cold-area change ignored by "
                 "extrapolation. Pooled over issue times.", fontsize=8, x=0.01, ha="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_evolution(out: Path) -> Path:
    per = pd.read_csv(P5 / "decomposition_per_issue.csv")
    fig = plt.figure(figsize=(14, 7.5), dpi=150)
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1])
    for j, ev in enumerate(EVENTS):
        ax = fig.add_subplot(gs[0, j])
        ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
        cold = ((ds["bt"] < THR) & ds["in_domain"]).sum(("y", "x")).values * 4.0 / 1e3
        t = pd.to_datetime(ds.time.values)
        ax.plot(t.hour + t.minute / 60, cold, "k-", lw=1.2, label="observed area < 235 K (domain)")
        g = per[(per["event"] == ev) & (per["lead_min"] == 120)]
        vt = pd.to_datetime(g["issue_time_utc"]) + pd.Timedelta(minutes=120)
        x = vt.dt.hour + vt.dt.minute / 60
        ax.plot(x, g["AfV"] * 4 / 1e3, "-", color="#1F6FB2", lw=1, label="pySTEPS +120 min, inside V")
        ax.plot(x, g["AoV"] * 4 / 1e3, "--", color="k", lw=0.8, label="observed, inside V")
        ax.plot(x, g["Af"] * 4 / 1e3, ":", color="#1F6FB2", lw=1, label="pySTEPS +120 min, whole domain")
        ax.set_xlim(0, 24); ax.set_xlabel("valid hour (UTC)", fontsize=7); ax.set_ylabel("10^3 km^2", fontsize=7)
        ax.set_title(f"{LAB[ev]}: cold-area evolution", fontsize=8, loc="left")
        ax.tick_params(labelsize=6); ax.grid(alpha=0.3)
        if j == 0:
            ax.legend(fontsize=5.5)
    pf = load_lifecycle("E8_20260514")
    for j, (col, lab) in enumerate([("dlogA", "log-area change / 30 min"), ("d_min_bt_30", "min-BT change (K / 30 min)"),
                                    ("dlogCC", "log(1+cold-core area) change / 30 min")]):
        ax = fig.add_subplot(gs[1, j])
        pf["nxt"] = pf.groupby("cell")[col].shift(-1)
        s = pf.dropna(subset=[col, "nxt"])
        c = np.where(s["genealogy_step"], "#C9822B", "#1F6FB2")
        ax.scatter(s[col], s["nxt"], s=6, c=c, alpha=0.7)
        phi = float((s[col] * s["nxt"]).sum() / (s[col] ** 2).sum())
        lim = np.nanquantile(np.abs(np.r_[s[col], s["nxt"]]), 0.98)
        xx = np.linspace(-lim, lim, 2)
        ax.plot(xx, phi * xx, "k-", lw=0.8, label=f"AR(1) phi = {phi:.2f} (n = {len(s)})")
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.axhline(0, color="k", lw=0.4); ax.axvline(0, color="k", lw=0.4)
        ax.set_xlabel(f"{lab} at t", fontsize=7); ax.set_ylabel("same, at t + 30 min", fontsize=7)
        ax.set_title(f"E8 (development) cell tendency persistence: {lab}", fontsize=7, loc="left")
        ax.tick_params(labelsize=6); ax.legend(fontsize=6); ax.grid(alpha=0.3)
    fig.text(0.01, 0.005, "Bottom: v2 cells (Phase 3). Orange = step with a merge/split, blue = clean step. A usable "
             "trend needs phi clearly > 0; none has a 95 % CI excluding 0 on E8 (lifecycle_reliability.csv).", fontsize=6)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_differences(out: Path, lead: int = 120) -> Path:
    cmap = mcolors.ListedColormap(["#FFFFFF", "#2A9D8F", "#B23A2E", "#1F6FB2", "#8C8C8C", "#EDEDED"])
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.5), dpi=150)
    for j, ev in enumerate(EVENTS):
        ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
        fc = xr.open_dataset(f"data/processed/{ev}/baseline/advection_forecasts.nc")
        bt, dom = ds["bt"].values, ds["in_domain"].values
        # Issue-time rule (as fig 7): largest in-domain area < 235 K among issues with a +lead observation.
        cold = ((ds["bt"] < THR) & ds["in_domain"]).sum(("y", "x")).to_series()
        it = pd.to_datetime(fc.issue_time.values)
        ok = [i for i, t in enumerate(it) if t + pd.Timedelta(minutes=lead) <= pd.Timestamp(ds.time.values[-1])]
        i = max(ok, key=lambda i: cold.loc[fc.issue_time.values[i]])
        k = int(np.where(ds.time.values == fc.issue_time.values[i])[0][0])
        L = lead // 30
        f = fc["bt_forecast"].values[i, L - 1]
        obs, per = bt[k + L], bt[k]
        V = dom & np.isfinite(obs) & np.isfinite(per) & np.isfinite(f)
        o_ev, f_ev = np.isfinite(obs) & (obs < THR), np.isfinite(f) & (f < THR)
        cat = np.zeros(bt.shape[1:], int)
        cat[V & f_ev & o_ev], cat[V & ~f_ev & o_ev], cat[V & f_ev & ~o_ev] = 1, 2, 3
        cat[dom & ~V] = 5                                 # unscorable in-domain pixel (inflow edge / missing data)
        cat[dom & ~V & o_ev] = 4                          # observed event in the unscorable region
        cat[~dom] = 0
        ax = axs[0, j]
        ax.imshow(cat, origin="lower", cmap=cmap, vmin=-0.5, vmax=5.5, interpolation="nearest")
        ax.set_title(f"{LAB[ev]}: pySTEPS issued {it[i]:%H:%M} UTC, +{lead} min", fontsize=8, loc="left")
        # Oracle (area-matched) forecast: which pixels would a perfect uniform area correction flip?
        n = int(o_ev[V].sum())
        ff = np.where(V, f, np.inf)
        orc = np.zeros_like(V)
        if n:
            idx = np.argsort(ff, axis=None, kind="stable")[:n]
            orc.flat[idx] = True
        diff = np.zeros(bt.shape[1:], int)
        diff[V & f_ev & ~orc & ~o_ev] = 1                # removed, correctly (decay)
        diff[V & f_ev & ~orc & o_ev] = 2                 # removed, wrongly
        diff[V & ~f_ev & orc & o_ev] = 3                 # added, correctly (growth)
        diff[V & ~f_ev & orc & ~o_ev] = 4                # added, wrongly
        ax2 = axs[1, j]
        cm2 = mcolors.ListedColormap(["#FFFFFF", "#2A9D8F", "#B23A2E", "#1F6FB2", "#C9822B"])
        ax2.imshow(diff, origin="lower", cmap=cm2, vmin=-0.5, vmax=4.5, interpolation="nearest")
        ax2.contour(o_ev.astype(float) * V, levels=[0.5], colors="k", linewidths=0.4)
        vals = {c: int((diff == c).sum()) for c in range(1, 5)}
        ax2.set_title(f"ORACLE area match (bias {f_ev[V].sum() / max(n, 1):.2f} -> 1)\nremoved ok {vals[1]} / wrong {vals[2]}"
                      f"; added ok {vals[3]} / wrong {vals[4]} px", fontsize=7, loc="left")
        for a in (ax, ax2):
            a.set_xticks([]); a.set_yticks([])
    h = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ["#2A9D8F", "#B23A2E", "#1F6FB2", "#8C8C8C", "#EDEDED"]]
    axs[0, 0].legend(h, ["hit", "miss", "false alarm", "observed event, unscored", "unscored (edge / missing)"],
                     fontsize=6, loc="lower left")
    h2 = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ["#2A9D8F", "#B23A2E", "#1F6FB2", "#C9822B"]]
    axs[1, 0].legend(h2, ["removed, correct", "removed, wrong", "added, correct", "added, wrong"], fontsize=6, loc="lower left")
    fig.suptitle("Forecast differences. Top: pySTEPS contingency inside the scored region V. Bottom: pixels a "
                 "perfect uniform area/intensity correction (ORACLE, uses the observation) would change; black = observed "
                 "< 235 K. Issue time chosen by the fig-7 rule.", fontsize=8, x=0.01, ha="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def main() -> None:
    print(fig_decomposition(FIGS / "phase5_fig14_bias_decomposition.png"))
    print(fig_evolution(FIGS / "phase5_fig15_area_evolution_and_lifecycle_persistence.png"))
    print(fig_differences(FIGS / "phase5_fig16_forecast_differences.png"))


if __name__ == "__main__":
    main()
