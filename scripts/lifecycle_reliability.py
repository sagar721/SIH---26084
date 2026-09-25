"""Phase-5 task 2 gate: are the existing lifecycle features reliable enough to drive a decay-aware pySTEPS extension?

  python -m scripts.lifecycle_reliability

Candidate model (the simplest deterministic extension): at issue time, extrapolate each tracked cell's recent
Lagrangian tendency (min-BT or log-area change per 30 min) with AR(1) damping, apply it to the cell's pixels and
advect with the unchanged pySTEPS motion. Its only parameter is the lag-1 AR coefficient phi of the tendency.

Decision rule (set before the E8 numbers were computed; E8 is the development event, E10/E11 are held out):
  build the model only if, on E8 Phase-3 v2 tracks, some tendency has phi > 0 with a 95 % cell-bootstrap interval
  that excludes 0. Otherwise stop (Phase-5 instruction: "stop and document why instead of forcing the model").
E10/E11 values are computed for transparency only and do not enter the decision.

Features are existing Phase-3 lifecycle columns (cells_per_frame.csv): d_min_bt_30, area_km2, cold_core_km2, phase.
All are causal at frame k (they use frames k-1 and k only).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DEV_EVENT = "E8_20260514"
EVENTS = ["E8_20260514", "E10_20260504", "E11_20260516"]
OUT = Path("data/processed/multi_event/phase5")
N_BOOT, SEED = 1000, 20260925
TENDENCIES = {"d_min_bt_30": "min-BT change (K / 30 min)",
              "dlogA": "log segment-area change (< 245 K) per 30 min",
              "dlogCC": "log(1 + cold-core area < 221 K) change per 30 min"}


def load(ev: str) -> pd.DataFrame:
    p = Path(f"data/processed/{ev}/tracking_v2_none")
    pf = pd.read_csv(p / "cells_per_frame.csv").sort_values(["cell", "frame"])
    ge = pd.read_csv(p / "genealogy_events.csv")
    gen = set(zip(ge["frame"], ge["from_cell"])) | set(zip(ge["frame"], ge["into_cell"]))
    pf["genealogy_step"] = [(f, c) in gen for f, c in zip(pf["frame"], pf["cell"])]
    pf["dlogA"] = pf.groupby("cell")["area_km2"].transform(lambda a: np.log(a).diff())
    pf["dlogCC"] = pf.groupby("cell")["cold_core_km2"].transform(lambda a: np.log1p(a).diff())
    pf["ends_next"] = pf.groupby("cell")["frame"].transform("max") == pf["frame"]
    return pf


def ar1(s: pd.DataFrame, col: str) -> float:
    den = float((s[col] ** 2).sum())
    return float((s[col] * s["nxt"]).sum() / den) if den > 0 else float("nan")


def ar1_with_ci(pf: pd.DataFrame, col: str, clean_only: bool) -> dict:
    pf = pf.copy()
    pf["nxt"] = pf.groupby("cell")[col].shift(-1)
    pf["nxt_gen"] = pf.groupby("cell")["genealogy_step"].shift(-1)
    s = pf.dropna(subset=[col, "nxt"])
    if clean_only:
        s = s[~s["genealogy_step"] & (s["nxt_gen"] == False)]  # noqa: E712 (NaN-safe)
    groups = {c: g for c, g in s.groupby("cell")}
    cells = list(groups)
    rng = np.random.default_rng(SEED)
    boot = [ar1(pd.concat([groups[c] for c in rng.choice(cells, len(cells))]), col) for _ in range(N_BOOT)]
    boot = np.array(boot)
    boot = boot[np.isfinite(boot)]  # resamples whose tendency is all zero (e.g. no cold core) are undefined
    lo, hi = np.quantile(boot, [0.025, 0.975]) if len(boot) >= 0.9 * N_BOOT else (np.nan, np.nan)
    phi = ar1(s, col)
    return {"n_pairs": len(s), "n_cells": len(cells), "phi": phi, "phi_lo95": float(lo), "phi_hi95": float(hi),
            "cumulative_gain_phi_over_1_minus_phi": phi / (1 - phi) if 0 < phi < 1 else 0.0}


def coverage(ev: str, pf: pd.DataFrame) -> dict:
    """Share of observed BT < 235 K pixels at issue frames that lie in cells with a usable tendency."""
    import xarray as xr
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    mask = xr.open_dataset(f"data/processed/{ev}/mask.nc")["segment_label"].values
    bt, dom = ds["bt"].values, ds["in_domain"].values
    has = pf.dropna(subset=["d_min_bt_30"])
    clean = has[~has["genealogy_step"]]
    tot = cov = cov_c = 0
    for k in range(2, bt.shape[0] - 1):
        cold = (bt[k] < 235.0) & dom
        tot += int(cold.sum())
        cov += int((cold & np.isin(mask[k], has.loc[has["frame"] == k, "feature"])).sum())
        cov_c += int((cold & np.isin(mask[k], clean.loc[clean["frame"] == k, "feature"])).sum())
    return {"cold_px_with_tendency_frac": cov / tot, "cold_px_with_clean_tendency_frac": cov_c / tot}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, phase_rows = [], []
    for ev in EVENTS:
        pf = load(ev)
        cov = coverage(ev, pf)
        for col in TENDENCIES:
            for clean in (False, True):
                rows.append({"event": ev, "role": "development" if ev == DEV_EVENT else "held-out (not used in decision)",
                             "tendency": col, "steps": "no merge/split at either step" if clean else "all steps",
                             **ar1_with_ci(pf, col, clean), **cov})
        pf["next_dlogA"] = pf.groupby("cell")["dlogA"].shift(-1)
        pf["next_dminbt"] = pf.groupby("cell")["d_min_bt_30"].shift(-1)
        for ph, g in pf.groupby("phase"):
            phase_rows.append({"event": ev, "phase": ph, "n": len(g), "next_dlogA_mean": g["next_dlogA"].mean(),
                               "next_dlogA_sd": g["next_dlogA"].std(), "next_dminBT_mean": g["next_dminbt"].mean(),
                               "frac_cell_ends_next_step": g["ends_next"].mean()})
    rel = pd.DataFrame(rows)
    rel.to_csv(OUT / "lifecycle_reliability.csv", index=False)
    pd.DataFrame(phase_rows).to_csv(OUT / "lifecycle_phase_outcomes.csv", index=False)

    dev = rel[rel["event"] == DEV_EVENT]
    passing = dev[(dev["phi"] > 0) & (dev["phi_lo95"] > 0)]
    decision = {
        "rule": "build only if a tendency on the development event E8 has phi > 0 with 95 % cell-bootstrap CI excluding 0",
        "development_event": DEV_EVENT, "passing_tendencies": passing[["tendency", "steps"]].to_dict("records"),
        "decision": "BUILD" if len(passing) else "STOP",
    }
    h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    prov = {"run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **decision,
            "bootstrap": {"n": N_BOOT, "seed": SEED, "unit": "cell"},
            "inputs": {f"{ev}/tracking_v2_none/{n}": h(f"data/processed/{ev}/tracking_v2_none/{n}")
                       for ev in EVENTS for n in ("cells_per_frame.csv", "genealogy_events.csv")},
            "outputs": {n: h(OUT / n) for n in ("lifecycle_reliability.csv", "lifecycle_phase_outcomes.csv")}}
    (OUT / "lifecycle_decision.json").write_text(json.dumps(prov, indent=2))
    pd.set_option("display.width", 250)
    print(rel.drop(columns=["role"]).to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(pd.DataFrame(phase_rows).to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
