"""Phase-5 tests: exactness of the edge/decay decomposition, agreement with the Phase-4 scores, the oracle bound,
the lifecycle-reliability gate (and its STOP decision), causality of the lifecycle features, provenance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.decompose_advection_error import oracle_contingency
from scripts.lifecycle_reliability import DEV_EVENT, ar1_with_ci, load

P5 = Path("data/processed/multi_event/phase5")
needs_dec = pytest.mark.skipif(not (P5 / "decomposition_provenance.json").exists(), reason="decomposition not run")
needs_rel = pytest.mark.skipif(not (P5 / "lifecycle_decision.json").exists(), reason="reliability not run")
h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------- unit ----------------

def test_oracle_matches_observed_area():
    fc = np.array([[200.0, 240.0, 250.0], [230.0, 260.0, 210.0]])
    obs = np.array([[1, 1, 0], [0, 0, 0]], bool)
    valid = np.ones_like(obs)
    ct = oracle_contingency(fc, obs, valid)
    assert ct["H"] + ct["F"] == ct["H"] + ct["M"] == 2          # forecast area = observed area
    assert ct == {"H": 1, "M": 1, "F": 1, "CN": 3}              # the 2 coldest pixels are (0,0) and (1,2)


# ---------------- decomposition ----------------

@needs_dec
def test_bias_factorisation_is_exact():
    for name in ("decomposition_by_lead.csv", "decomposition_by_issue_block.csv"):
        d = pd.read_csv(P5 / name).dropna(subset=["bias_V", "E_edge", "C_advected_area", "G_unchanged_intensity"])
        d = d[np.isfinite(d[["bias_V", "E_edge", "C_advected_area", "G_unchanged_intensity"]]).all(axis=1)]
        assert np.allclose(d["E_edge"] * d["C_advected_area"] * d["G_unchanged_intensity"], d["bias_V"], rtol=1e-12)


@needs_dec
def test_decomposition_rescoring_equals_phase4_scores():
    per = pd.read_csv(P5 / "decomposition_per_issue.csv")
    for ev, g in per.groupby("event"):
        pi = pd.read_csv(f"data/processed/{ev}/baseline/grid_metrics_per_issue.csv")
        pi = pi[pi["method"] == "pysteps_advection"].set_index(["issue_time_utc", "lead_min"])[["H", "M", "F", "CN"]]
        mine = g.set_index(["issue_time_utc", "lead_min"])[["H_V", "M_V", "F_V", "CN_V"]]
        mine.columns = ["H", "M", "F", "CN"]
        assert (mine.loc[pi.index] == pi).all().all()
    by = pd.read_csv(P5 / "decomposition_by_lead.csv")
    em = pd.read_csv("data/processed/multi_event/event_metrics_by_lead.csv")
    em = em[em["method"] == "pysteps_advection"].set_index(["event", "lead_min"])["CSI"]
    assert np.allclose(by.set_index(["event", "lead_min"])["CSI_V"].loc[em.index], em, rtol=0, atol=1e-15)


@needs_dec
def test_edge_and_oracle_rows_are_consistent():
    per = pd.read_csv(P5 / "decomposition_per_issue.csv")
    assert (per["n_D"] >= per["n_V"]).all() and (per["M_Dedge"] >= per["M_V"]).all()
    assert (per["AoD"] >= per["AoV"]).all() and (per["Af"] >= per["AfV"]).all()
    # the oracle forecast has exactly the observed event count on V
    assert (per["H_oracle"] + per["F_oracle"] == per["H_V"] + per["M_V"]).all()


# ---------------- lifecycle gate ----------------

@needs_rel
def test_lifecycle_gate_recomputes_and_stops():
    rel = pd.read_csv(P5 / "lifecycle_reliability.csv")
    pf = load(DEV_EVENT)
    for col in ("d_min_bt_30", "dlogA"):
        r = ar1_with_ci(pf, col, clean_only=False)
        row = rel[(rel["event"] == DEV_EVENT) & (rel["tendency"] == col) & (rel["steps"] == "all steps")].iloc[0]
        assert r["phi"] == pytest.approx(row["phi"]) and r["phi_lo95"] == pytest.approx(row["phi_lo95"])
    dev = rel[rel["event"] == DEV_EVENT]
    passing = dev[(dev["phi"] > 0) & (dev["phi_lo95"] > 0)]
    dec = json.loads((P5 / "lifecycle_decision.json").read_text())
    assert dec["decision"] == ("BUILD" if len(passing) else "STOP") == "STOP"


@needs_rel
def test_lifecycle_tendencies_are_causal():
    # Tendencies at frame k must be unchanged when every row after frame k is deleted (no future information).
    pf = load(DEV_EVENT)
    k = int(pf["frame"].median())
    raw = pd.read_csv(f"data/processed/{DEV_EVENT}/tracking_v2_none/cells_per_frame.csv")
    cut = raw[raw["frame"] <= k].sort_values(["cell", "frame"])
    cut["dlogA"] = cut.groupby("cell")["area_km2"].transform(lambda a: np.log(a).diff())
    a = pf[pf["frame"] <= k].set_index(["cell", "frame"])["dlogA"]
    b = cut.set_index(["cell", "frame"])["dlogA"]
    assert np.allclose(a.loc[b.index].fillna(-99), b.fillna(-99))


# ---------------- provenance / earlier phases untouched ----------------

@needs_dec
@needs_rel
def test_phase5_outputs_match_provenance():
    for name in ("decomposition_provenance.json", "lifecycle_decision.json"):
        prov = json.loads((P5 / name).read_text())
        for out, digest in prov["outputs"].items():
            assert h(P5 / out) == digest
    prov = json.loads((P5 / "decomposition_provenance.json").read_text())
    assert prov["config_baseline_sha256"] == h("config/baseline.yaml")


def test_phase4_outputs_unchanged():
    prov = json.loads(Path("data/processed/multi_event/multi_event_provenance.json").read_text())
    for name, digest in prov["outputs"].items():
        assert h(Path("data/processed/multi_event") / name) == digest
