"""Phase-5 task 1: separate pySTEPS error from spatial-edge exclusion vs unchanged storm intensity/area.

  python -m scripts.decompose_advection_error

Nothing is fitted. For every (event, issue k, lead L) and the BT < 235 K event, with
  V   = Phase-2 scoring mask (domain & obs valid & persistence valid & advection valid),
  D   = domain & obs valid (what could be scored if there were no inflow edge),
  A0  = observed event area at the issue time (domain, valid),
  Af  = advection event area anywhere in the domain,     AfV = inside V,
  AoD = observed event area in D at k+L,                  AoV = inside V,
the frequency bias factorises exactly (pooled over issue times by summing areas per lead):

  bias_V = AfV / AoV = [ (AfV/Af) / (AoV/AoD) ]  x  [ Af / A0 ]  x  [ A0 / AoD ]
                        edge term E                advection        unchanged-intensity
                                                   area change C    term G (real growth/decay)

E > 1: scoring excludes more observed events than forecast events (inflow edge hides new/entering storms).
C < 1: advected cold area leaves the domain (outflow) or is lost by interpolation.
G > 1: the observed cold area shrank between k and k+L (decay the extrapolation ignores); G < 1: growth.

CSI is also reported three ways (diagnostic only):
  CSI_V         the Phase-2/4 score;
  CSI_D_edge    inflow-edge pixels scored as "no forecast event" (the price of the edge);
  CSI_V_oracle  advection with its event threshold chosen per (issue, lead) so that its area on V equals the
                OBSERVED area on V — uses the future; an upper bound on what any perfect area/intensity
                (growth/decay) correction of the advected field could reach. Not a forecast.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ml.forecasting.baselines import advection_grid, persistence_grid
from ml.verification.scores import cat_scores, contingency

EVENTS = ["E8_20260514", "E10_20260504", "E11_20260516"]
OUT = Path("data/processed/multi_event/phase5")
THR = 235.0


def oracle_contingency(fc: np.ndarray, obs_ev: np.ndarray, valid: np.ndarray) -> dict:
    """Area-matched threshold: forecast event = the n coldest valid forecast pixels, n = observed event count."""
    n = int(obs_ev[valid].sum())
    f = fc[valid]
    ev = np.zeros(f.shape, bool)
    if n:
        ev[np.argsort(f, kind="stable")[:n]] = True
    o = obs_ev[valid]
    return {"H": int((ev & o).sum()), "M": int((~ev & o).sum()), "F": int((ev & ~o).sum()), "CN": int((~ev & ~o).sum())}


def decompose_event(ev: str, cfg: dict) -> pd.DataFrame:
    ds = xr.open_dataset(f"data/interim/grid2km/{ev}.nc")
    bt, dom = ds["bt"].values, ds["in_domain"].values
    times = pd.to_datetime(ds.time.values)
    n_t, n_lead = bt.shape[0], cfg["max_lead_steps"]
    rows = []
    for k in range(cfg["motion"]["n_past_frames"] - 1, n_t - 1):
        fp = persistence_grid(bt, k, n_lead)
        fa, _ = advection_grid(bt, k, n_lead, cfg)
        a0 = int((dom & np.isfinite(bt[k]) & (bt[k] < THR)).sum())
        for L in range(1, n_lead + 1):
            if k + L >= n_t:
                break
            obs = bt[k + L]
            D = dom & np.isfinite(obs)
            V = D & np.isfinite(fp[L - 1]) & np.isfinite(fa[L - 1])
            o_ev = np.isfinite(obs) & (obs < THR)
            f_ev = np.isfinite(fa[L - 1]) & (fa[L - 1] < THR)
            ct_v = contingency(f_ev, o_ev, V)
            ct_d = contingency(f_ev, o_ev, D)          # NaN forecast (inflow) counts as "no event"
            ct_o = oracle_contingency(np.where(np.isfinite(fa[L - 1]), fa[L - 1], np.inf), o_ev, V)
            rows.append({"event": ev, "issue_time_utc": str(times[k]), "issue_hour_utc": times[k].hour,
                         "lead_min": L * cfg["cadence_min"], "A0": a0,
                         "Af": int((dom & f_ev).sum()), "AfV": int((V & f_ev).sum()),
                         "AoD": int((D & o_ev).sum()), "AoV": int((V & o_ev).sum()),
                         "n_V": int(V.sum()), "n_D": int(D.sum()),
                         **{f"{c}_V": v for c, v in ct_v.items()}, **{f"{c}_Dedge": v for c, v in ct_d.items()},
                         **{f"{c}_oracle": v for c, v in ct_o.items()}})
    return pd.DataFrame(rows)


def summarise(per: pd.DataFrame, by: tuple[str, ...] = ("event", "lead_min")) -> pd.DataFrame:
    out = []
    for key, g in per.groupby(list(by)):
        key = dict(zip(by, key))
        s = g.sum(numeric_only=True)
        E = (s["AfV"] / s["Af"]) / (s["AoV"] / s["AoD"])
        C, G = s["Af"] / s["A0"], s["A0"] / s["AoD"]
        row = {**key, "n_issue_times": len(g), "bias_V": s["AfV"] / s["AoV"],
               "E_edge": E, "C_advected_area": C, "G_unchanged_intensity": G,
               "log_bias": np.log(s["AfV"] / s["AoV"]), "log_E": np.log(E), "log_C": np.log(C), "log_G": np.log(G),
               "frac_obs_events_in_edge": 1 - s["AoV"] / s["AoD"], "frac_fc_events_outside_V": 1 - s["AfV"] / s["Af"]}
        for tag in ("V", "Dedge", "oracle"):
            row[f"CSI_{tag}"] = cat_scores(*(int(s[f"{c}_{tag}"]) for c in ("H", "M", "F", "CN")))["CSI"]
        out.append(row)
    return pd.DataFrame(out)


def main() -> None:
    cfg = yaml.safe_load(Path("config/baseline.yaml").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    per = pd.concat([decompose_event(ev, cfg) for ev in EVENTS], ignore_index=True)
    per.to_csv(OUT / "decomposition_per_issue.csv", index=False)
    summ = summarise(per)
    summ.to_csv(OUT / "decomposition_by_lead.csv", index=False)
    per["issue_block_utc"] = (per["issue_hour_utc"] // 6 * 6).map(lambda h: f"{h:02d}-{h + 6:02d}")
    summarise(per, ("event", "issue_block_utc", "lead_min")).to_csv(OUT / "decomposition_by_issue_block.csv", index=False)
    h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    prov = {"run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "events": EVENTS,
            "config_baseline_sha256": h("config/baseline.yaml"),
            "inputs": {f"{ev}.nc": h(f"data/interim/grid2km/{ev}.nc") for ev in EVENTS},
            "outputs": {p: h(OUT / p) for p in ("decomposition_per_issue.csv", "decomposition_by_lead.csv", "decomposition_by_issue_block.csv")},
            "fitted_parameters": "none; the oracle row uses observed future areas and is NOT a forecast"}
    (OUT / "decomposition_provenance.json").write_text(json.dumps(prov, indent=2))
    pd.set_option("display.width", 250)
    print(summ[summ["lead_min"].isin([30, 60, 120, 180, 240, 360])].to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
