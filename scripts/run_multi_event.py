"""Phase-4 cross-event evaluation of the Phase-2 grid baselines (docs/MULTI_EVENT.md).

  python -m scripts.run_multi_event

Reads only saved per-event outputs of the unchanged Phase-1/2/3 pipeline (cube, baseline/, tracking_v2_*/) and writes
data/processed/multi_event/. No forecast is re-run, no threshold is changed and nothing is fitted.

Uncertainty (VALIDATION_PLAN §5):
- within an event: circular block bootstrap over issue times, block = 12 issue times (6 h, the longest lead, so that
  the overlapping forecast windows of neighbouring issue times stay together), 1000 resamples, fixed seed;
- across events: bootstrap by event day (1000 resamples of whole events). With only a handful of events this has
  very few distinct resamples and is reported as indicative only; the sign count across events is reported beside it.
Both resample pooled contingency counts (H, M, F), so CSI and bias are recomputed exactly per resample.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ml.verification.scores import cat_scores

EVENTS = ["E8_20260514", "E8a_20260501", "E10_20260504", "E11_20260516"]
METHODS = ("persistence", "pysteps_advection")
OUT = Path("data/processed/multi_event")
N_BOOT = 1000
BLOCK = 12
SEED = 20260925
REPORT_LEADS = [30, 60, 120, 180, 240, 360]
# Suitability (fixed before scoring): all frames of the 24 h window decoded, and deep convection (BT < 235 K) present
# in the domain in at least half of the frames, so that CSI is defined for most issue times.
MIN_DEEP_FRAME_FRAC = 0.5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csi_bias(ct: np.ndarray) -> tuple[float, float]:
    """ct = (..., 3) array of H, M, F -> CSI, bias (NaN where undefined)."""
    H, M, F = ct[..., 0], ct[..., 1], ct[..., 2]
    with np.errstate(invalid="ignore", divide="ignore"):
        return H / (H + M + F), (H + F) / (H + M)


def circular_block_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, n, size=int(np.ceil(n / block)))
    return (starts[:, None] + np.arange(block)[None]).ravel()[:n] % n


def block_bootstrap(counts: dict[str, np.ndarray], n_boot: int, block: int, seed: int) -> dict[str, np.ndarray]:
    """counts[method] = (n_issue, 3) H/M/F for one lead, rows in issue-time order (same rows for both methods).
    Returns bootstrap samples of pooled CSI per method, the CSI difference and bias per method."""
    rng = np.random.default_rng(seed)
    n = next(iter(counts.values())).shape[0]
    idx = np.stack([circular_block_indices(n, min(block, n), rng) for _ in range(n_boot)])
    out = {}
    for m, c in counts.items():
        pooled = c[idx].sum(axis=1)
        out[f"CSI_{m}"], out[f"bias_{m}"] = csi_bias(pooled)
    out["CSI_diff"] = out["CSI_pysteps_advection"] - out["CSI_persistence"]
    return out


def event_qc(ev: str) -> dict:
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    dom = ds["in_domain"].values
    deep = ((ds["bt"] < 235.0) & ds["in_domain"]).sum(("y", "x")).values
    run = json.loads(Path(f"data/processed/{ev}/run_summary.json").read_text())
    return {
        "event": ev, "n_frames": int(ds.sizes["time"]), "n_raw_files": len(json.loads(ds.attrs["raw_sha256"])),
        "qc_fail_frames": int((ds["qc_status"].values != "OK").sum()),
        "raw_missing_frac_max": float(ds["raw_missing_frac"].max()),
        "residual_missing_frac_max": float(ds["qc_missing_frac"].max()),
        "gapfilled_px_frac_mean": float(ds["gapfilled"].values[:, dom].mean()),
        "deep_frames_frac": float((deep > 0).mean()),
        "deep_area_frac_mean": float(deep.mean() / dom.sum()),
        "deep_area_frac_max": float(deep.max() / dom.sum()),
        "n_cells_v1": run["n_cells"], "n_cells_v1_ge_2h": run["n_cells_ge_2h"],
        "suitable": bool(ds.sizes["time"] == 48 and (deep > 0).mean() >= MIN_DEEP_FRAME_FRAC),
    }


def decay_row(g: pd.DataFrame) -> dict:
    g = g.sort_values("lead_min")
    row = {}
    for s in ("20km", "40km"):
        ok = (g[f"FSS_{s}"] >= g[f"FSS_useful_threshold_{s}"]).values
        n_ok = int(np.argmin(ok)) if not ok.all() else len(ok)   # leads useful without interruption from 30 min
        row[f"useful_FSS_{s}_up_to_min"] = int(g["lead_min"].iloc[n_ok - 1]) if n_ok else 0
    c30 = g["CSI"].iloc[0]
    below = g[g["CSI"] <= 0.5 * c30]
    row["CSI_half_lead_min"] = int(below["lead_min"].iloc[0]) if len(below) else np.nan
    fit = g[(g["lead_min"] <= 180) & (g["CSI"] > 0)]
    slope = np.polyfit(fit["lead_min"], np.log(fit["CSI"]), 1)[0]
    row["CSI_efold_min_30_180"] = float(-1.0 / slope) if slope < 0 else np.nan
    return row


def run(events: list[str]) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg_hash = sha256(Path("config/baseline.yaml"))
    qc = pd.DataFrame([event_qc(ev) for ev in events])
    qc.to_csv(OUT / "event_qc.csv", index=False)
    used = [ev for ev, ok in zip(qc["event"], qc["suitable"]) if ok]

    by_lead, per_issue, prov_in = [], {}, {}
    for ev in used:
        b = Path(f"data/processed/{ev}/baseline")
        prov = json.loads((b / "baseline_provenance.json").read_text())
        if prov["inputs"]["config/baseline.yaml"] != cfg_hash:
            raise ValueError(f"{ev} was not run with the current config/baseline.yaml")
        for name, digest in prov["outputs"].items():
            if sha256(b / name) != digest:
                raise ValueError(f"{ev}/{name} does not match its provenance hash")
            prov_in[f"{ev}/baseline/{name}"] = digest
        by_lead.append(pd.read_csv(b / "grid_metrics_by_lead.csv").assign(event=ev))
        per_issue[ev] = pd.read_csv(b / "grid_metrics_per_issue.csv")
    by_lead = pd.concat(by_lead, ignore_index=True)
    keep = ["event", "method", "lead_min", "n_issue_times", "n_scored_pixels", "excluded_frac_mean", "base_rate",
            "H", "M", "F", "CN", "POD", "FAR", "CSI", "bias", "FSS_10km", "FSS_20km", "FSS_40km",
            "FSS_useful_threshold_20km", "FSS_useful_threshold_40km"]
    by_lead[keep].to_csv(OUT / "event_metrics_by_lead.csv", index=False)

    # ---- within-event block bootstrap ----
    ci_rows = []
    for ev in used:
        pi = per_issue[ev]
        for L in sorted(pi["lead_min"].unique()):
            g = pi[pi["lead_min"] == L]
            counts = {m: g[g["method"] == m].sort_values("issue_time_utc")[["H", "M", "F"]].to_numpy(float) for m in METHODS}
            bs = block_bootstrap(counts, N_BOOT, BLOCK, SEED)
            pt = {m: csi_bias(counts[m].sum(0)) for m in METHODS}
            row = {"event": ev, "lead_min": int(L), "n_issue_times": counts[METHODS[0]].shape[0],
                   "CSI_persistence": pt["persistence"][0], "CSI_pysteps_advection": pt["pysteps_advection"][0],
                   "CSI_diff": pt["pysteps_advection"][0] - pt["persistence"][0],
                   "bias_persistence": pt["persistence"][1], "bias_pysteps_advection": pt["pysteps_advection"][1]}
            for k, v in bs.items():
                row[f"{k}_lo95"], row[f"{k}_hi95"] = np.nanquantile(v, [0.025, 0.975])
            row["frac_boot_diff_gt0"] = float(np.nanmean(bs["CSI_diff"] > 0))
            ci_rows.append(row)
    ci = pd.DataFrame(ci_rows)
    ci.to_csv(OUT / "event_block_bootstrap.csv", index=False)

    # ---- cross-event ----
    cross = []
    for L in sorted(by_lead["lead_min"].unique()):
        g = by_lead[by_lead["lead_min"] == L]
        ct = {m: g[g["method"] == m].set_index("event").loc[used, ["H", "M", "F"]].to_numpy(float) for m in METHODS}
        csi_ev = {m: csi_bias(ct[m])[0] for m in METHODS}
        diff_ev = csi_ev["pysteps_advection"] - csi_ev["persistence"]
        rng = np.random.default_rng(SEED)
        idx = rng.integers(0, len(used), size=(N_BOOT, len(used)))
        bdiff = csi_bias(ct["pysteps_advection"][idx].sum(1))[0] - csi_bias(ct["persistence"][idx].sum(1))[0]
        row = {"lead_min": int(L), "n_events": len(used)}
        for m in METHODS:
            s = cat_scores(*[int(v) for v in g[g["method"] == m][["H", "M", "F", "CN"]].sum().values])
            gm = g[g["method"] == m]
            row.update({f"CSI_pooled_{m}": s["CSI"], f"bias_pooled_{m}": s["bias"],
                        f"CSI_event_min_{m}": float(np.min(csi_ev[m])), f"CSI_event_max_{m}": float(np.max(csi_ev[m])),
                        f"bias_event_min_{m}": float(gm["bias"].min()), f"bias_event_max_{m}": float(gm["bias"].max()),
                        f"FSS_40km_event_mean_{m}": float(gm["FSS_40km"].mean()),
                        f"FSS_40km_event_min_{m}": float(gm["FSS_40km"].min()),
                        f"FSS_40km_event_max_{m}": float(gm["FSS_40km"].max())})
        row["CSI_diff_pooled"] = row["CSI_pooled_pysteps_advection"] - row["CSI_pooled_persistence"]
        row["n_events_advection_better_CSI"] = int((diff_ev > 0).sum())
        row["CSI_diff_eventday_boot_lo95"], row["CSI_diff_eventday_boot_hi95"] = np.quantile(bdiff, [0.025, 0.975])
        fss_d = (by_lead[(by_lead["lead_min"] == L) & (by_lead["method"] == "pysteps_advection")].set_index("event").loc[used, "FSS_40km"]
                 - by_lead[(by_lead["lead_min"] == L) & (by_lead["method"] == "persistence")].set_index("event").loc[used, "FSS_40km"])
        row["n_events_advection_better_FSS40"] = int((fss_d > 0).sum())
        cross.append(row)
    cross = pd.DataFrame(cross)
    cross.to_csv(OUT / "cross_event_by_lead.csv", index=False)

    decay = pd.DataFrame([{"event": ev, "method": m, **decay_row(g)}
                          for (ev, m), g in by_lead.groupby(["event", "method"])])
    decay.to_csv(OUT / "decay_by_event.csv", index=False)

    # ---- object diagnostics (Phase-3 v2 tracks; DIAGNOSTIC ONLY, never primary) ----
    obj = []
    for ev in used:
        for mode in ("none", "flow"):
            p = Path(f"data/processed/{ev}/tracking_v2_{mode}/object_paired_comparison.csv")
            if p.exists():
                obj.append(pd.read_csv(p).assign(event=ev, truth=f"v2_{mode}"))
                prov_in[f"{ev}/tracking_v2_{mode}/object_paired_comparison.csv"] = sha256(p)
    obj = pd.concat(obj, ignore_index=True) if obj else pd.DataFrame()
    obj.to_csv(OUT / "object_diagnostics_by_event.csv", index=False)

    outputs = {p.name: sha256(p) for p in sorted(OUT.glob("*.csv"))}
    prov = {"run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "events_considered": events, "events_used": used,
            "config_baseline_sha256": cfg_hash, "config_tracking_sha256": sha256(Path("config/tracking.yaml")),
            "config_tracking_v2_sha256": sha256(Path("config/tracking_v2.yaml")),
            "bootstrap": {"n": N_BOOT, "block_issue_times": BLOCK, "seed": SEED,
                          "within_event": "circular block bootstrap over issue times, pooled H/M/F per resample",
                          "cross_event": "bootstrap by event day, pooled H/M/F per resample"},
            "suitability_rule": f"48 frames and BT<235 K present in >= {MIN_DEEP_FRAME_FRAC:.0%} of frames",
            "inputs": prov_in, "outputs": outputs, "fitted_parameters": "none"}
    (OUT / "multi_event_provenance.json").write_text(json.dumps(prov, indent=2))
    return {"qc": qc, "cross": cross, "ci": ci, "decay": decay, "obj": obj}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", nargs="+", default=EVENTS)
    r = run(ap.parse_args().events)
    pd.set_option("display.width", 250)
    print(r["qc"].to_string(index=False))
    c = r["cross"]
    print(c[c["lead_min"].isin(REPORT_LEADS)].T.to_string(float_format=lambda v: f"{v:.3f}"))
    ci = r["ci"]
    print(ci[ci["lead_min"].isin(REPORT_LEADS)][["event", "lead_min", "CSI_persistence", "CSI_pysteps_advection", "CSI_diff",
          "CSI_diff_lo95", "CSI_diff_hi95", "bias_pysteps_advection"]].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(r["decay"].to_string(index=False))


if __name__ == "__main__":
    main()
