"""Phase-6 figures from saved evaluation outputs (data/processed/ml_eval/<version>/).

  python -m scripts.make_ml_figures
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import yaml

CFG = yaml.safe_load(Path("config/ml_dataset.yaml").read_text())
EV = Path(f"data/processed/ml_eval/{CFG['version']}")
MD = Path(f"data/models/{CFG['version']}")
FIGS = Path("data/figures")
COL = {"persistence": "#6B6457", "pysteps_advection": "#1F6FB2", "pysteps_np31": "#8FB8DE", "ml_raw": "#E9A23B",
       "ml": "#B23A2E"}
LAB = {"persistence": "persistence", "pysteps_advection": "pySTEPS", "pysteps_np31": "pySTEPS 31-px neighbourhood (no fit)",
       "ml_raw": "ML raw", "ml": "ML calibrated"}
EVL = {"E8_20260514": "E8 14 May", "E10_20260504": "E10 4 May", "E11_20260516": "E11 16 May"}


def fig_skill(out: Path) -> Path:
    po = pd.read_csv(EV / "metrics_pooled_lead.csv")
    be = pd.read_csv(EV / "metrics_by_event_lead.csv")
    po, be = po[po["mask"] == "V"], be[be["mask"] == "V"]
    fss = be.groupby(["method", "lead_min"])["FSS_40km"].mean().reset_index()
    fig, axs = plt.subplots(1, 4, figsize=(17, 4), dpi=150)
    for m in COL:
        g = po[po["method"] == m].sort_values("lead_min")
        axs[0].plot(g["lead_min"], g["CSI"], "o-", ms=3, color=COL[m], label=LAB[m])
        f = fss[fss["method"] == m].sort_values("lead_min")
        axs[1].plot(f["lead_min"], f["FSS_40km"], "o-", ms=3, color=COL[m])
        axs[2].plot(g["lead_min"], g["BSS_vs_train_clim"], "o-", ms=3, color=COL[m])
        axs[3].plot(g["lead_min"], g["bias"], "o-", ms=3, color=COL[m])
    axs[2].axhline(0, color="k", lw=0.6); axs[3].axhline(1, color="k", lw=0.6)
    axs[2].set_ylim(-1.0, 1.0)
    for ax, t in zip(axs, ["CSI (event: BT < 235 K; ML at p >= 0.5)", "FSS 40 km (mean of 3 events)",
                           "BSS vs training climatology (0/1 for deterministic)", "Frequency bias"]):
        ax.set_title(t, fontsize=8, loc="left"); ax.set_xlabel("lead (min)", fontsize=7)
        ax.tick_params(labelsize=6); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=6)
    fig.suptitle("Phase 6: held-out test events E8/E10/E11 pooled, scored on the Phase-4 mask V (identical pixels "
                 "for all methods). Model trained on 18-31 May 2026, calibrated on 6-12 May 2026.",
                 fontsize=8, x=0.01, ha="left", y=1.03)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_diff(out: Path) -> Path:
    b = pd.read_csv(EV / "bootstrap_ml_vs_pysteps.csv")
    fig, axs = plt.subplots(1, 2, figsize=(12, 4), dpi=150)
    for j, (ev, g) in enumerate(b.groupby("event", sort=False)):
        g = g.sort_values("lead_min")
        x = g["lead_min"] + (j - 1) * 4
        axs[0].errorbar(x, g["CSI_diff_ml_minus_pysteps"], yerr=[g["CSI_diff_ml_minus_pysteps"] - g["CSI_diff_lo95"],
                        g["CSI_diff_hi95"] - g["CSI_diff_ml_minus_pysteps"]], fmt="os^"[j], ms=3, lw=0.8, capsize=1.5,
                        label=EVL[ev])
        axs[1].errorbar(x, g["BSS_diff_ml_minus_np31"], yerr=[g["BSS_diff_ml_minus_np31"] - g["BSS_diff_np31_lo95"],
                        g["BSS_diff_np31_hi95"] - g["BSS_diff_ml_minus_np31"]], fmt="os^"[j], ms=3, lw=0.8,
                        capsize=1.5, label=EVL[ev])
    axs[1].set_ylim(-1.0, 2.0)
    for ax, t in zip(axs, ["CSI(ML, p >= 0.5) - CSI(pySTEPS)",
                           "BSS(ML) - BSS(pySTEPS 31-px neighbourhood, no fit); upper bars clipped at 2"]):
        ax.axhline(0, color="k", lw=0.6); ax.set_title(t, fontsize=8, loc="left"); ax.set_xlabel("lead (min)", fontsize=7)
        ax.tick_params(labelsize=6); ax.grid(alpha=0.3); ax.legend(fontsize=6)
    fig.suptitle("Per held-out event; bars = 95 % circular block bootstrap over issue times (6 h blocks, 1000 resamples). "
                 "Within-event variability only; 3 events cannot establish generalisation.", fontsize=8, x=0.01, ha="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_reliability(out: Path) -> Path:
    r = pd.read_csv(EV / "reliability.csv")
    groups = [(30, 30), (60, 60), (90, 120), (150, 360)]
    fig, axs = plt.subplots(2, 4, figsize=(15, 6), dpi=150, gridspec_kw={"height_ratios": [3, 1]})
    for j, (lo, hi) in enumerate(groups):
        g = r[(r["lead_min"] >= lo) & (r["lead_min"] <= hi)].groupby(["method", "bin"])[["n", "sum_p", "sum_o"]].sum().reset_index()
        for m in ("pysteps_np31", "ml_raw", "ml"):
            s = g[(g["method"] == m) & (g["n"] > 0)]
            axs[0, j].plot(s["sum_p"] / s["n"], s["sum_o"] / s["n"], "o-", ms=3, color=COL[m], label=LAB[m])
            axs[1, j].bar(s["bin"] / 10 + 0.05 + {"pysteps_np31": -0.03, "ml_raw": 0.0, "ml": 0.03}[m], s["n"],
                          width=0.03, color=COL[m])
        axs[0, j].plot([0, 1], [0, 1], "k:", lw=0.8)
        axs[0, j].set_title(f"lead {lo}-{hi} min", fontsize=8, loc="left")
        axs[0, j].set_xlabel("forecast probability", fontsize=7); axs[0, j].set_ylabel("observed frequency", fontsize=7)
        axs[1, j].set_yscale("log"); axs[1, j].set_xlabel("probability bin", fontsize=7); axs[1, j].set_ylabel("n px", fontsize=7)
        for ax in axs[:, j]:
            ax.tick_params(labelsize=6); ax.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=6)
    fig.suptitle("Reliability on the held-out test events (pooled, mask V, 10 bins). Isotonic calibration was fitted on "
                 "the validation days only.", fontsize=8, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_example(out: Path, lead: int = 120) -> Path:
    fig, axs = plt.subplots(2, 3, figsize=(15, 8), dpi=150)
    for j, ev in enumerate(CFG["splits"]["test"]):
        ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
        pr = xr.open_dataset(EV / f"ml_probabilities_{ev}.nc")
        fc = xr.open_dataset(f"data/processed/{ev}/baseline/advection_forecasts.nc")
        cold = ((ds["bt"] < 235.0) & ds["in_domain"]).sum(("y", "x")).to_series()
        it = pd.to_datetime(fc.issue_time.values)
        ok = [i for i, t in enumerate(it) if t + pd.Timedelta(minutes=lead) <= pd.Timestamp(ds.time.values[-1])]
        i = max(ok, key=lambda i: cold.loc[fc.issue_time.values[i]])        # fig-7 issue-time rule
        k = int(np.where(ds.time.values == fc.issue_time.values[i])[0][0])
        obs = ds["bt"].values[k + lead // 30]
        o_ev = (obs < 235.0).astype(float)
        dom = ds["in_domain"].values
        f = fc["bt_forecast"].values[i, lead // 30 - 1]
        ax = axs[0, j]
        ax.imshow(np.where(dom, np.where(np.isfinite(f), (f < 235.0).astype(float), 0.3), np.nan), origin="lower",
                  cmap="Blues", vmin=0, vmax=1.3, interpolation="nearest")
        ax.contour(o_ev * dom, levels=[0.5], colors="k", linewidths=0.5)
        ax.set_title(f"{EVL[ev]}: pySTEPS < 235 K\nissued {it[i]:%H:%M} UTC, +{lead} min (grey = no forecast)",
                     fontsize=7, loc="left")
        ax2 = axs[1, j]
        p = pr["p_ml"].values[i, lead // 30 - 1].astype(float)
        p = p * 1e-4 if p.max() > 1.5 else p
        im = ax2.imshow(np.where(dom, p, np.nan), origin="lower", cmap="magma_r", vmin=0, vmax=1, interpolation="nearest")
        ax2.contour(o_ev * dom, levels=[0.5], colors="c", linewidths=0.5)
        ax2.contour(np.where(dom, p, 0), levels=[0.5], colors="k", linewidths=0.6, linestyles="--")
        ax2.set_title("ML calibrated P(BT < 235 K)\ndashed = p 0.5; cyan = observed", fontsize=7, loc="left")
        for a in (ax, ax2):
            a.set_xticks([]); a.set_yticks([])
    fig.colorbar(im, ax=axs[1, :], shrink=0.6, label="probability")
    fig.suptitle("Example held-out forecasts (black/cyan contour = OBSERVED BT < 235 K). Issue time chosen by the fig-7 rule.",
                 fontsize=8, x=0.01, ha="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_training(out: Path) -> Path:
    card = json.loads((MD / "model_card.json").read_text())
    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=150)
    c = card["validation_logloss_curve"]
    ax.plot(np.arange(1, len(c) + 1), c, "k-", lw=1)
    ax.axvline(card["n_iter_selected"], color="#B23A2E", lw=0.8, label=f"selected n_iter = {card['n_iter_selected']}")
    ax.set_xlabel("boosting iteration", fontsize=7); ax.set_ylabel("weighted log-loss (validation days)", fontsize=7)
    ax.tick_params(labelsize=6); ax.grid(alpha=0.3); ax.legend(fontsize=6)
    ax.set_title("n_iter chosen on validation days 6-12 May (never on test)", fontsize=8, loc="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def main() -> None:
    print(fig_skill(FIGS / "phase6_fig17_skill_vs_lead.png"))
    print(fig_diff(FIGS / "phase6_fig18_ml_minus_pysteps_ci.png"))
    print(fig_reliability(FIGS / "phase6_fig19_reliability.png"))
    print(fig_example(FIGS / "phase6_fig20_example_probabilities.png"))
    print(fig_training(FIGS / "phase6_fig21_validation_curve.png"))


if __name__ == "__main__":
    main()
