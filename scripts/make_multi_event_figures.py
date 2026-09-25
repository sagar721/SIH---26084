"""Phase-4 cross-event figures from data/processed/multi_event/ (saved outputs only).

  python -m scripts.make_multi_event_figures
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

M = Path("data/processed/multi_event")
FIGS = Path("data/figures")
COL = {"persistence": "#6B6457", "pysteps_advection": "#1F6FB2"}
EV_STYLE = ["o-", "s--", "^-.", "D:"]


def _label(ev: str) -> str:
    code, d = ev.split("_")
    return f"{code} {d[6:8]}/{d[4:6]}"


def fig_skill(bl: pd.DataFrame, events: list[str], out: Path) -> Path:
    fig, axs = plt.subplots(1, 3, figsize=(14, 4), dpi=150)
    for j, ev in enumerate(events):
        for m in COL:
            g = bl[(bl["event"] == ev) & (bl["method"] == m)].sort_values("lead_min")
            kw = dict(color=COL[m], ms=3, lw=1, label=f"{_label(ev)} {m}")
            axs[0].plot(g["lead_min"], g["CSI"], EV_STYLE[j], **kw)
            axs[1].plot(g["lead_min"], g["FSS_40km"], EV_STYLE[j], **kw)
            axs[2].plot(g["lead_min"], g["bias"], EV_STYLE[j], **kw)
        th = bl[(bl["event"] == ev) & (bl["method"] == "persistence")].sort_values("lead_min")
        axs[1].plot(th["lead_min"], th["FSS_useful_threshold_40km"], ":", color="k", lw=0.6)
    axs[2].axhline(1.0, color="k", lw=0.6)
    for ax, t in zip(axs, ["CSI (BT < 235 K), pooled per event", "FSS 40 km (dotted: useful 0.5 + f0/2)",
                           "Frequency bias"]):
        ax.set_title(t, fontsize=8, loc="left"); ax.set_xlabel("lead (min)", fontsize=7)
        ax.tick_params(labelsize=6); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=5, ncol=2)
    fig.suptitle("Phase 4: persistence (grey) vs pySTEPS advection (blue) on each event — identical protocol "
                 "(config/baseline.yaml unchanged), 30-min leads, same scored pixels for both methods. "
                 "Data: NOAA/NCEP/CPC merged IR.", fontsize=8, x=0.01, ha="left", y=1.02)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_diff(ci: pd.DataFrame, cross: pd.DataFrame, events: list[str], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    w = 4.0
    for j, ev in enumerate(events):
        g = ci[ci["event"] == ev].sort_values("lead_min")
        x = g["lead_min"] + (j - (len(events) - 1) / 2) * w
        ax.errorbar(x, g["CSI_diff"], yerr=[g["CSI_diff"] - g["CSI_diff_lo95"], g["CSI_diff_hi95"] - g["CSI_diff"]],
                    fmt=EV_STYLE[j][0], ms=3, lw=0.8, capsize=1.5, label=_label(ev))
    ax.plot(cross["lead_min"], cross["CSI_diff_pooled"], "k-", lw=1.2, label="pooled over events")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xlabel("lead (min)", fontsize=7); ax.set_ylabel("CSI(advection) − CSI(persistence)", fontsize=7)
    ax.tick_params(labelsize=6); ax.grid(alpha=0.3); ax.legend(fontsize=6)
    ax.set_title("Advection minus persistence CSI per event; bars = 95 % circular block bootstrap over issue times "
                 "(6 h blocks, 1000 resamples).\nWithin-event intervals only: issue times inside one day are not "
                 "independent events.", fontsize=7, loc="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_qc(bl: pd.DataFrame, qc: pd.DataFrame, events: list[str], out: Path) -> Path:
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.6), dpi=150)
    for j, ev in enumerate(events):
        g = bl[(bl["event"] == ev) & (bl["method"] == "persistence")].sort_values("lead_min")
        axs[0].plot(g["lead_min"], g["excluded_frac_mean"], EV_STYLE[j], ms=3, lw=1, label=_label(ev))
        axs[1].plot(g["lead_min"], g["base_rate"], EV_STYLE[j], ms=3, lw=1, label=_label(ev))
    axs[0].set_title("Unscorable fraction (outside-inflow NaN + missing data)", fontsize=8, loc="left")
    axs[1].set_title("Observed base rate of BT < 235 K on scored pixels", fontsize=8, loc="left")
    for ax in axs:
        ax.set_xlabel("lead (min)", fontsize=7); ax.tick_params(labelsize=6); ax.grid(alpha=0.3); ax.legend(fontsize=6)
    txt = "   ".join(f"{_label(r.event)}: QC-fail frames {r.qc_fail_frames}/48, max raw missing {r.raw_missing_frac_max:.3f}"
                   for r in qc.itertuples() if r.event in events)
    fig.text(0.01, -0.03, txt, fontsize=6)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def main() -> None:
    bl = pd.read_csv(M / "event_metrics_by_lead.csv")
    ci = pd.read_csv(M / "event_block_bootstrap.csv")
    cross = pd.read_csv(M / "cross_event_by_lead.csv")
    qc = pd.read_csv(M / "event_qc.csv")
    events = list(dict.fromkeys(bl["event"]))
    print(fig_skill(bl, events, FIGS / "multi_event_fig11_skill_by_event.png"))
    print(fig_diff(ci, cross, events, FIGS / "multi_event_fig12_csi_difference_ci.png"))
    print(fig_qc(bl, qc, events, FIGS / "multi_event_fig13_scorability_base_rate.png"))


if __name__ == "__main__":
    main()
