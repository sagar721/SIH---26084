# Phase 2 — Baseline Forecast Evaluation (E8, 14 May 2026)

**Status:** Phase 2 complete · **Inputs:** Phase-1 outputs only ([FIRST_EVENT.md](FIRST_EVENT.md)); NOAA/CPC merged IR as the approved Phase-1 fallback. No new data sources were acquired.

**Scope:**
- **Models:** baselines only — M0 persistence and M1 pySTEPS extrapolation (VALIDATION_PLAN §1). **Nothing is trained, fitted or tuned.**
- **Outputs:** no probabilities are produced (both baselines are deterministic), so no Brier/BSS/AUPRC/reliability. Those metrics need probabilistic forecasts (Phase 5).

---

## 1. Setup (fixed in `config/baseline.yaml` before evaluation)

| Item | Value |
|---|---|
| Issue times | 45: every frame 01:00–23:00 UTC. The first two frames are used only as motion history. |
| Leads | 30, 60 … 360 min (native 30-min cadence). **15-min leads are not produced**: the source has no 15-min frames, and interpolated truth would not be real observation. |
| M0 persistence | BT(t+L) = BT(t) |
| M1 pySTEPS advection | Lucas–Kanade dense motion from frames t−60, t−30, t, on tracer max(0, 273 K − BT); semi-Lagrangian advection of BT(t); inflow from outside the grid = NaN |
| Grid event | BT < 235 K (deep convection; VALIDATION_PLAN §2) |
| Scoring mask | Inside the lat/lon domain **and** valid in observation, persistence **and** advection. Both methods are scored on identical pixels. |
| Object baselines | Per tracked cell with ≥ 1 frame of history at issue: persistence (last position), constant velocity (displacement over t−60→t, else t−30→t), field advection (the M1 motion field sampled at the cell). Truth = the same cell's observed position at t+L. |
| Time ordering | Every forecast issued at frame k reads only frames ≤ k. This is **tested** by destroying future frames and checking the forecast is unchanged. With no fitted parameters there is no train/test split to leak across. The event lies in the VALIDATION_PLAN test period (2025–26). |

## 2. Reproduce

```bash
.venv/bin/python -m scripts.run_baseline --event E8_20260514          # ~75 s
.venv/bin/python -m scripts.make_baseline_figures --event E8_20260514
.venv/bin/python -m pytest -q                                          # 17 tests
```

A rerun gives byte-identical CSVs (hashes in [`data/PROVENANCE.md`](../data/PROVENANCE.md) §Phase 2).

## 3. Grid metrics (pooled over issue times; `grid_metrics_by_lead.csv`)

| Lead | n issues | Excluded frac | Persistence CSI | Advection CSI | Persistence POD / FAR | Advection POD / FAR | Persistence bias | Advection bias | FSS 20 km P / A | FSS 40 km P / A |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 | 45 | 0.087 | 0.509 | **0.593** | 0.688 / 0.338 | 0.802 / 0.306 | 1.04 | 1.16 | 0.792 / **0.853** | 0.851 / 0.898 |
| 60 | 44 | 0.112 | 0.352 | **0.428** | 0.534 / 0.493 | 0.684 / 0.467 | 1.05 | 1.28 | 0.635 / **0.713** | 0.700 / 0.771 |
| 120 | 42 | 0.162 | 0.191 | **0.245** | 0.327 / 0.684 | 0.481 / 0.666 | 1.03 | 1.44 | 0.400 / **0.480** | 0.448 / 0.534 |
| 180 | 40 | 0.211 | 0.106 | **0.156** | 0.192 / 0.809 | 0.351 / 0.780 | 1.01 | 1.60 | 0.237 / 0.333 | 0.266 / 0.371 |
| 240 | 38 | 0.258 | 0.077 | 0.109 | 0.139 / 0.852 | 0.267 / 0.844 | 0.94 | 1.71 | 0.169 / 0.244 | 0.187 / 0.271 |
| 360 | 34 | 0.348 | 0.038 | 0.043 | 0.066 / 0.919 | 0.148 / 0.943 | 0.82 | 2.61 | 0.084 / 0.099 | 0.097 / 0.110 |

All 12 leads are in the CSV. The "useful" FSS threshold (0.5 + f0/2) is ≈ 0.51.
- **At 20 km:** advection stays above it to ~90 min (0.590); persistence only to ~60–90 min (0.635 at 60, 0.509 at 90).
- **At 40 km:** advection to ~120 min (0.534); persistence to ~90 min (0.567).

**Reading:**
- Advection beats persistence on CSI and FSS at every lead on this event.
- Both methods lose most skill by 2–3 h. By 6 h neither has useful skill. This matches the report's expectation that extrapolation cannot deliver 2–6 h, which needs the Phase-5+ ML/NWP components.
- Advection's **frequency bias grows to 2.6 at 6 h**. It moves cold shields intact while the real ones warm and decay (fig. 7 shows this). The west-side inflow exclusion may also contribute; that split is not decomposed yet (NEEDS VERIFICATION).
- The unscorable fraction grows from 9 % to 35 % with lead, so long-lead scores cover a shrinking, eastern part of the domain.

**Uncertainty:**
- Only one event day exists, so the VALIDATION_PLAN's bootstrap-by-event-day CIs **cannot be computed** and are not reported.
- Per-issue-time dispersion (IQR bands in fig. 5, table `grid_metrics_per_issue.csv`) is descriptive only. Issue times within one day are strongly autocorrelated.

## 4. Object metrics — DIAGNOSTIC ONLY (`object_metrics_by_lead.csv`)

| Lead | n scored (survivors) | Survival frac | Median centroid error (km): persistence | Constant velocity | Field advection | Median IoU (segmented cells) P / CV / FA |
|---|---|---|---|---|---|---|
| 30 | 1,248 | 0.68 | **20.3** | 24.3 | 21.0 | 0.27 / 0.25 / **0.33** (n=190) |
| 60 | 868 | 0.47 | **28.5** | 40.8 | 31.9 | 0.14 / 0.12 / 0.14 (n=116) |
| 120 | 431 | 0.23 | **37.0** | 63.2 | 48.8 | 0.00 / 0.00 / 0.02 (n=45) |
| 180 | 224 | 0.12 | **43.2** | 84.0 | 69.8 | — (n=21) |

## 5. Why the object metrics are not skill evidence (finding)

Persistence has the *lowest* centroid error, even though both the flow field (mean ~34 km/h eastward) and the tracked cells' net motion (Phase 1: median 31 km/h, ESE) show real motion.

**Diagnostic** (60-min lead, segmented cells): the correlation between the field-predicted displacement and the tracked cell's observed displacement is only **0.13 (x) / 0.11 (y)**. The tracked feature positions move largely by **jitter**:
- positions switch between sub-features and threshold levels;
- the `random` linker re-links to the nearest feature within 54 km.

They do not move with the cloud field. The grid scores do not depend on tracking and show that advection adds skill.

**Implications:**
- Object-level truth needs the Phase-3 tracking audit before object metrics can be claimed. Candidates: cold-core positions, smoothed tracks, a manual audit sheet.
- Scores are conditional on survival. Only 12 % of cells survive to 3 h, so long-lead object numbers rest on small samples.
- IoU is computed only for cells segmented (< 245 K) at both times.

## 6. Figures (from saved outputs)

| # | File | Content |
|---|---|---|
| 5 | [`data/figures/E8_20260514_fig5_grid_skill_vs_lead.png`](../data/figures/E8_20260514_fig5_grid_skill_vs_lead.png) | CSI (pooled + per-issue IQR), FSS 20/40 km with useful threshold, POD/FAR, bias + excluded fraction vs lead |
| 6 | [`data/figures/E8_20260514_fig6_object_diagnostic.png`](../data/figures/E8_20260514_fig6_object_diagnostic.png) | Object centroid error (3 methods) and survival — labelled diagnostic |
| 7 | [`data/figures/E8_20260514_fig7_example_forecast.png`](../data/figures/E8_20260514_fig7_example_forecast.png) | Issued 14:00 UTC: persistence / advection / observed at +60 and +180 min, with observed < 235 K contours. Issue time chosen by rule (largest cold area with a +180 min observation). |

## 7. Saved outputs (`data/processed/E8_20260514/baseline/`)

| File | Content |
|---|---|
| `advection_forecasts.nc` | M1 forecasts (45 issues × 12 leads, int16 at 0.01 K) + motion fields. Persistence is not duplicated: it equals the cube frame at the issue time (stated in file attrs). |
| `grid_metrics_by_lead.csv` | Pooled contingency counts, POD/FAR/CSI/bias/base rate, FSS 10/20/40 km, useful threshold, excluded fraction, n |
| `grid_metrics_per_issue.csv` | Same per issue time (+ FSS 20 km) |
| `object_predictions.csv` | Every (cell, issue, lead, method) prediction with truth, error, IoU |
| `object_metrics_by_lead.csv` | Summary by method and lead |
| `baseline_provenance.json` | Input/output SHA-256, issue times, versions, pySTEPS build note |

## 8. Tests (17 total; 7 new in `tests/test_phase2.py`)

**Unit** (tiny fixtures, arithmetic only):
- contingency/scores
- shifted IoU
- FSS perfect/disjoint

**Real data:**
- Our FSS equals **pySTEPS `spatialscores.fss`** on a real NaN-free window.
- **Leakage:** forecasts are unchanged when future frames are destroyed; persistence equals the issue frame.
- Saved outputs match their provenance hashes; "no fitted parameters" is recorded.
- One stored score is recomputed from scratch and matches exactly; the stored int16 forecast is within 0.006 K of the recomputed field.

## 9. NEEDS VERIFICATION / limitations

1. **pySTEPS local build.** No macOS arm64 wheel exists and Apple clang has no OpenMP, so pySTEPS was built from the PyPI sdist with `-fopenmp` removed. This affects only multithreading of the Proesmans/VET extensions, which are unused. LK and semi-Lagrangian code is unmodified. OpenCV 5.0 compatibility has not been independently verified beyond these runs.
2. **Single event, one day.** No CIs by event day. Results can't be generalised until more events are processed.
3. **Bias decomposition.** How much of advection's bias growth is no-decay vs west-inflow exclusion is not decomposed.
4. **Object truth quality.** See §5; Phase-3 tracking audit required.
5. **Parallax / satellite ID.** Carried from Phase 1 (unverified).
6. **Not evaluated:** 15-min leads; probabilistic metrics.
