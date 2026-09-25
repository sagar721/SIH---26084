"""Phase-3 audit figures from saved audit/tracking outputs.

  python -m scripts.make_audit_figures --event E8_20260514
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from scripts.make_figures import ir_cmap

COL = {"persistence": "#6B6457", "constant_velocity": "#C9822B", "field_advection": "#1F6FB2"}


def fig_audit(P: Path, out: Path) -> Path:
    A = {v: json.loads((P / f"audit/audit_{v}.json").read_text()) for v in ["v1", "v2_none", "v2_flow"]}
    rows = [("v1 all (tobac)", A["v1"]["all_cells"]), ("v1 cold rows", A["v1"]["segmented_rows_only"]),
            ("v2 overlap", A["v2_none"]["all_cells"]), ("v2 flow-overlap*", A["v2_flow"]["all_cells"])]
    metrics = [("zigzag_frac", "direction reversals\n(frac of step pairs; random = 0.5)"),
               ("seg_links_better_other_none_frac", "ID-switch candidates\n(frac of cold links)"),
               ("seg_links_zero_overlap_both_frac", "zero-overlap links\n(frac; v2 = 0 by construction)"),
               ("seg_links_area_jump_frac", "area jumps > 2x\n(frac of cold links)"),
               ("flow_corr_x", "corr(step dx, flow dx)")]
    fig, axs = plt.subplots(1, len(metrics), figsize=(14, 3.4), dpi=150)
    cols = ["#9A9A9A", "#6B6457", "#2A9D8F", "#1F6FB2"]
    for ax, (k, t) in zip(axs, metrics):
        vals = [r[1].get(k, np.nan) for r in rows]
        ax.bar(range(len(rows)), vals, color=cols)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=6)
        ax.set_xticks(range(len(rows))); ax.set_xticklabels([r[0] for r in rows], rotation=35, ha="right", fontsize=6)
        ax.set_title(t, fontsize=7); ax.tick_params(labelsize=6)
        ax.set_ylim(0, max(np.nanmax(vals), 0.01) * 1.25)
    fig.suptitle("Tracking audit E8 14 May 2026 — before (v1 tobac nearest-feature) vs after (v2 overlap linking of cold "
                 "segments, coldness-weighted centroid). *flow-overlap uses the pySTEPS flow for linking, so its "
                 "flow-correlation is partly circular.", fontsize=7, x=0.01, ha="left", y=1.08)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_worst_track(P: Path, ds: xr.Dataset, out: Path) -> Path:
    sus = pd.read_csv(P / "audit/suspicious_tracks_v1.csv")
    cell = int(sus.iloc[0]["cell"])
    f = pd.read_parquet(P / "features.parquet")
    g = f[f["cell"] == cell].sort_values("frame")
    mask = xr.open_dataset(P / "mask.nc")["segment_label"].values
    v2 = pd.read_csv(P / "tracking_v2_none/cells_per_frame.csv")
    v2g = v2[v2["feature"].isin(g["feature"])]
    fig, ax = plt.subplots(figsize=(8, 6.5), dpi=150)
    k = int(g["frame"].iloc[len(g) // 2])
    cmap, norm = ir_cmap()
    ax.imshow(ds["bt"].values[k], origin="lower", cmap=cmap, norm=norm, alpha=0.5)
    for fr in g["frame"]:
        ax.contour((mask[int(fr)] > 0).astype(float), levels=[0.5], colors="0.6", linewidths=0.3)
    ax.plot(g["hdim_2"], g["hdim_1"], "-o", color="#B23A2E", ms=3, lw=1, label=f"v1 tobac cell #{cell} ({len(g)} frames)")
    for i, r in enumerate(g.itertuples()):
        ax.text(r.hdim_2 + 2, r.hdim_1 + 2, str(int(r.frame)), fontsize=5, color="#B23A2E")
    for c2, h in v2g.groupby("cell"):
        h = h.sort_values("frame")
        ax.plot(h["cx_idx"], h["cy_idx"], "-s", ms=3, lw=1, label=f"v2 cell #{c2} (features shared with v1 #{cell})")
    pad = 40
    ax.set_xlim(g["hdim_2"].min() - pad, g["hdim_2"].max() + pad); ax.set_ylim(g["hdim_1"].min() - pad, g["hdim_1"].max() + pad)
    ax.set_xlabel("grid x (2 km px)", fontsize=7); ax.set_ylabel("grid y (2 km px)", fontsize=7); ax.tick_params(labelsize=6)
    ax.legend(fontsize=6, loc="upper left")
    ax.set_title(f"Most suspicious v1 track (#{cell}: {int(sus.iloc[0]['reversals'])} reversals, "
                 f"{int(sus.iloc[0]['id_switch_candidates'])} ID-switch candidates, {int(sus.iloc[0]['zero_overlap_links'])} "
                 "zero-overlap links). Numbers = frame index; grey = all < 245 K segments over its lifetime.", fontsize=7, loc="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def fig_objects_v2(P: Path, out: Path) -> Path:
    fig, axs = plt.subplots(2, 2, figsize=(11, 7), dpi=150, sharex=True)
    for j, mode in enumerate(["none", "flow"]):
        om = pd.read_csv(P / f"tracking_v2_{mode}/object_metrics_by_lead.csv")
        pc = pd.read_csv(P / f"tracking_v2_{mode}/object_paired_comparison.csv")
        ax = axs[0, j]
        for m, g in om.groupby("method"):
            ax.fill_between(g["lead_min"], g["centroid_err_km_p25"], g["centroid_err_km_p75"], color=COL[m], alpha=0.12, lw=0)
            ax.plot(g["lead_min"], g["centroid_err_km_median"], "o-", ms=3, color=COL[m], label=m)
        ax.set_title(f"v2 {'Eulerian overlap' if mode == 'none' else 'flow-shifted overlap (partly circular for field_advection)'}"
                     ": median centroid error (IQR)", fontsize=7, loc="left")
        ax.set_ylabel("km", fontsize=7); ax.legend(fontsize=6); ax.grid(alpha=0.3); ax.tick_params(labelsize=6)
        ax2 = axs[1, j]
        ax2.plot(pc["lead_min"], pc["frac_field_better_than_persistence"], "o-", color=COL["field_advection"], ms=3,
                 label="field_advection better than persistence")
        ax2.plot(pc["lead_min"], pc["frac_cv_better_than_persistence"], "s--", color=COL["constant_velocity"], ms=3,
                 label="constant_velocity better than persistence")
        ax2.axhline(0.5, color="k", lw=0.6)
        for x, y, n in zip(pc["lead_min"], pc["frac_field_better_than_persistence"], pc["n_distinct_cells"]):
            ax2.text(x, y + 0.03, str(n), fontsize=5, ha="center")
        ax2.set_ylim(0, 1.05); ax2.set_title("paired: fraction of (cell, issue) cases better than persistence "
                                             "(labels: distinct cells)", fontsize=7, loc="left")
        ax2.set_xlabel("lead (min)", fontsize=7); ax2.legend(fontsize=6); ax2.grid(alpha=0.3); ax2.tick_params(labelsize=6)
    fig.suptitle("Object diagnostics after the tracking fixes (cold segments only) — one event; pairs from the same cell "
                 "are not independent; no CIs.", fontsize=8, x=0.01, ha="left")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event", default="E8_20260514")
    ev = ap.parse_args().event
    P = Path(f"data/processed/{ev}")
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    figs = Path("data/figures")
    print(fig_audit(P, figs / f"{ev}_fig8_tracking_audit.png"))
    print(fig_worst_track(P, ds, figs / f"{ev}_fig9_worst_v1_track.png"))
    print(fig_objects_v2(P, figs / f"{ev}_fig10_object_diagnostics_v2.png"))


if __name__ == "__main__":
    main()
