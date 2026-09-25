"""Phase-8 replay-bundle tests: the web prototype shows only frozen evidence, unchanged.

The bundle (apps/web/public/bundles/<event>/) is built by pipelines/replay/build_bundle.py from frozen files; these tests
check its provenance against docs/FREEZE_ml-v0.json, that displayed numbers equal the frozen tables, that tiles reproduce
the frozen fields, and that replay shows no future information."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

WEB = Path("apps/web/public/bundles")
EV = "E8_20260514"
B = WEB / EV
needs = pytest.mark.skipif(not (B / "manifest.json").exists(), reason="bundle not built")
h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(name: str):
    return json.loads((B / name).read_text())


@needs
def test_bundle_inputs_are_the_frozen_files():
    man, freeze = _j("manifest.json"), json.loads(Path("docs/FREEZE_ml-v0.json").read_text())
    assert man["freeze_manifest_sha256"] == h("docs/FREEZE_ml-v0.json")
    assert man["inputs"], "bundle recorded no inputs"
    for p, d in man["inputs"].items():
        assert freeze["files"][p] == d == h(p)
    assert man["envelope"]["model"]["artifacts"] == freeze["model"]["artifacts"]


@needs
def test_bundle_outputs_match_their_hashes():
    man = _j("manifest.json")
    files = {str(p.relative_to(B)) for p in B.rglob("*") if p.is_file() and p.name != "manifest.json"}
    assert files == set(man["outputs"])
    for rel, d in man["outputs"].items():
        assert h(B / rel) == d
    n_i, n_l = len(man["issues"]), len(man["leads_min"])
    assert len(list((B / "fc").glob("ml_*.png"))) == n_i * n_l == len(list((B / "fc").glob("pysteps_*.png")))
    assert len(list((B / "obs").glob("*.png"))) == len(man["frames"]) == 48


@needs
def test_displayed_skill_equals_frozen_tables():
    sk = _j("skill.json")
    po = pd.read_csv("data/processed/ml_eval/ml-v0/metrics_pooled_lead.csv")
    po = po[po["mask"] == "V"].set_index(["method", "lead_min"])
    for m, rows in sk["pooled"].items():
        for r in rows:
            f = po.loc[(m, r["lead_min"])]
            assert r["BSS"] == pytest.approx(f["BSS_vs_train_clim"], abs=0, rel=0)
            if r["CSI"] is not None:
                assert r["CSI"] == pytest.approx(f["CSI"], abs=0, rel=0)
    ml = {r["lead_min"]: r for r in sk["pooled"]["ml"]}
    assert round(ml[30]["BSS"], 2) == 0.67 and round(ml[120]["BSS"], 2) == 0.27      # docs/FINAL_RESULTS.md
    assert "does not beat pySTEPS beyond 60 min" in sk["claim_guard"]


@needs
def test_issue_scores_equal_frozen_per_issue_table():
    sc = _j("scores.json")
    per = pd.read_csv("data/processed/ml_eval/ml-v0/per_issue.csv")
    per = per[(per["event"] == EV) & (per["mask"] == "V")]
    n = 0
    for t, by_lead in sc.items():
        for L, by_m in by_lead.items():
            for m, s in by_m.items():
                r = per[(per["issue_time_utc"] == t) & (per["lead_min"] == int(L)) & (per["method"] == m)].iloc[0]
                assert (s["H"], s["M"], s["F"], s["CN"]) == (r.H, r.M, r.F, r.CN)
                n += 1
    assert n > 900


@needs
def test_alerts_are_unique_exercise_drafts_at_the_frozen_threshold():
    al = _j("alerts.json")
    assert "EXERCISE" in al["rule"] and ">= 0.5" in al["rule"]
    for t, lst in al["by_issue"].items():
        ids = [a["alert_id"] for a in lst]
        assert len(ids) == len(set(ids)), f"duplicate alert ids at {t}"
        for a in lst:
            assert a["p_max"] >= 0.5 and a["lead_min"] in (30, 60)
            assert a["alert_id"] == f"{a['prediction_id']}#{a['place']}"
            assert al["place_max_p_60min"][t][a["place"]] >= a["p_max"]


@needs
def test_cells_show_no_future_information():
    tracks = _j("tracks.json")
    for f in sorted((B / "cells").glob("f*.geojson")):
        k = int(f.stem[1:])
        for feat in json.loads(f.read_text())["features"]:
            p = feat["properties"]
            first = min(pt["frame"] for pt in tracks[str(p["cell"])])
            assert first <= k and p["age_min"] == (k - first) * 30          # age = history up to now, not lifetime


@needs
def test_ml_tile_reproduces_frozen_probability():
    import xarray as xr
    from PIL import Image
    from pipelines.replay.build_bundle import display_grid
    ds = xr.open_dataset(f"data/interim/grid2km/{EV}.nc")
    g = display_grid(ds)
    pm = xr.open_dataset(f"data/processed/ml_eval/ml-v0/ml_probabilities_{EV}.nc")
    i, L = 26, 60
    p = pm["p_ml"].isel(issue_time=i, lead_min=list(pm.lead_min.values).index(L)).values
    code = np.array(Image.open(B / f"fc/ml_i{i:02d}_l{L:03d}.png"))
    ok = g["ok"] & (code < 255)
    assert ok.mean() > 0.8
    assert np.abs(code[ok] / 250.0 - p[g["row"], g["col"]][ok]).max() <= 0.5 / 250 + 1e-9


@needs
def test_event_index_marks_only_bundled_events_playable():
    idx = json.loads((WEB / "index.json").read_text())
    assert idx["default"] == EV
    playable = {c["event"] for c in idx["events"] if c["status"] == "BUNDLED"}
    assert EV in playable and all((WEB / e / "manifest.json").exists() for e in playable)
    assert any(c["code"] == "E9" and c["status"] == "NOT AVAILABLE" for c in idx["events"])
