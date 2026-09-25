# Phase 6 — ML Forecast Prototype (ml-v0)

**Status:** Phase 6 complete. One frozen model was scored once on the held-out events E8 (14 May), E10 (4 May) and E11 (16 May 2026).

**Headline:**
- **Probabilistic skill:** clearly better than persistence, pySTEPS and a no-fit neighbourhood-probability pySTEPS, out to ~4 h.
- **Deterministic forecast at the pre-declared p ≥ 0.5:** no better than pySTEPS beyond 60 min, and CSI = 0 from 150 min.
- **Scope:** three events from one month and one region. No generalisation is claimed.

**Constraints followed:**
- Phase 5 STOP respected; no decay-aware model.
- No deep learning; no synthetic data.
- No UI.

---

## 1. Target, data, splits (`config/ml_dataset.yaml`, fixed before training)

**Target and data:**
- **Target:** observed BT(t+L) < 235 K per 2 km pixel, L = 30…360 min. This is the Phase-2/4 grid event; no new labels.
- **Source:** the approved NOAA/NCEP/CPC merged-IR archive, with Phase-1 preprocessing unchanged (`build_window` is a behaviour-preserving split of `build`; tested equal on E11).

**Splits** (calendar-day blocks; no pixel or random splits):

| Block | Days | Convective days (Phase-4 rule) | Use |
|---|---|---|---|
| Train | 18–31 May 2026 (14) | 7 (18, 20, 21, 28–31) | Fitting |
| Validation | 6–12 May 2026 (7) | 5 | n_iter selection, isotonic calibration |
| Test | E8 14 May, E10 4 May, E11 16 May | 3 | Scored once, frozen model |
| Excluded | All events.yaml days (1, 4, 14, 16 May) ± 1 day | — | Never read |

**Sufficiency gate** (fixed before building the dataset): at least 7 convective training days and at least 3 convective validation days.
- **Result:** train 7 (exactly the minimum), validation 5 → PROCEED.

**Limitation of the split:** the archive starts 1 May, so the training block lies **after** the test events. It is a day-disjoint, buffered, backward-in-time test, not a forward one (VALIDATION_PLAN wants train 2019–23 / test 2025–26).

**Dataset:**
- Per (day, issue, lead), pixels are stratified into:
  - event: 150;
  - non-event near cold cloud: 150;
  - far non-event: 60.
- Each row carries an inverse-probability weight. Weighted totals reproduce the full population exactly (tested).
- Rows: 1,467,318 train and 856,830 validation.

**Features (17):** all from frames ≤ t plus the unchanged pySTEPS forecast issued at t (causality tested by destroying future frames):
- pySTEPS BT at t+L, and its 11/31-px event fractions, min, and valid fraction;
- BT(t), its 31-px event fraction and 11-px min;
- 30-min tendency, raw and advected, plus the neighbourhood mean of the advected tendency;
- motion speed;
- domain cold fraction and its 60-min change;
- valid hour (sin/cos);
- lead.

No lat/lon or terrain (declared: 14 days cannot support a location climatology).

## 2. Model

- **Algorithm:** `sklearn.ensemble.HistGradientBoostingClassifier`, the histogram GBDT family ARCHITECTURE plans as LightGBM, which is not installed.
  - Settings: learning rate 0.05, 31 leaves, min leaf 500, L2 1.0, `random_state` 0.
  - No internal early stopping, because that would be a random pixel split.
- **n_iter = 216:** the minimum of weighted log-loss on the validation days over 400 staged iterations, then refit (fig. 21).
- **Isotonic calibration:** per lead bin (30 / 60 / 90–120 / 150–360 min), validation days only. Validation weighted log-loss: 0.0552 raw → 0.0529 calibrated.
- **Artifacts:** `data/models/ml-v0/`, holding `model.joblib`, `calibrators.joblib` and `model_card.json` (hashes, days, curve, training climatology, versions). Training takes ~100 s; a retrain on the same data gives identical predictions (tested).
- **Permutation importance** (validation subsample; `permutation_importance_validation.csv`). By weighted log-loss increase:

| Feature | Log-loss increase |
|---|---|
| Neighbourhood fraction of pySTEPS events (31 px) | 0.019 |
| Lead | 0.008 |
| BT(t) neighbourhood fraction | 0.005 |
| Motion speed | 0.003 |
| pySTEPS min | 0.003 |
| Advected-tendency mean | 0.003 |
| Diurnal terms | ~0.001–0.002 |

The domain-scale and raw BT features add nothing (≤ 0). **The model is mainly a calibrated, lead-aware neighbourhood version of pySTEPS**, with modest tendency and time-of-day information.

## 3. Held-out results (`data/processed/ml_eval/ml-v0/`)

Scored on the Phase-4 mask V, identical pixels for every method (tested). Pooled over E8/E10/E11.

**Methods compared:**
- persistence and pySTEPS: unchanged; re-scored contingency equals Phase 4 exactly;
- NP31: the no-fit reference, the fraction of pySTEPS events in 31×31 px;
- ML.

**Scoring:**
- Deterministic scores use p ≥ 0.5 (VALIDATION_PLAN §2, pre-declared).
- BSS uses the per-lead training-split climatology.

| Lead (min) | CSI P / pySTEPS / NP31 / ML | FSS 40 km (event mean) pySTEPS / ML | Bias pySTEPS / ML | BSS P / pySTEPS / NP31 / **ML** |
|---|---|---|---|---|
| 30 | 0.511 / 0.586 / 0.596 / 0.583 | 0.901 / 0.886 | 1.13 / 0.76 | 0.32 / 0.44 / 0.63 / **0.67** |
| 60 | 0.342 / 0.429 / 0.444 / **0.452** | 0.773 / 0.778 | 1.22 / 0.66 | −0.04 / 0.10 / 0.41 / **0.51** |
| 120 | 0.176 / 0.258 / 0.264 / 0.243 | 0.543 / 0.525 | 1.30 / 0.54 | −0.47 / −0.38 / 0.02 / **0.27** |
| 180 | 0.092 / 0.172 / 0.172 / **0.000** | 0.402 / 0.000 | 1.32 / 0.00 | −0.69 / −0.67 / −0.23 / **0.13** |
| 240 | 0.052 / 0.122 / 0.116 / 0.000 | 0.276 / 0.000 | 1.28 / 0.00 | −0.78 / −0.82 / −0.37 / **0.06** |
| 360 | 0.022 / 0.049 / 0.045 / 0.000 | 0.086 / 0.000 | 1.29 / 0.00 | −0.84 / −1.11 / −0.59 / −0.03 |

**Per-event uncertainty** (`bootstrap_ml_vs_pysteps.csv`). Circular block bootstrap over issue times, 6-h blocks, 1000 resamples, as in Phase 4.

BSS(ML) − BSS(NP31):

| Event | 30 min | 60 min | 120 min | 180 min |
|---|---|---|---|---|
| E8 | +0.04 [0.03, 0.11] | +0.12 [0.04, 0.36] | +0.27 [0.04, 0.92] | +0.49 [0.10, 1.63] |
| E10 | +0.03 [0.01, 0.11] | +0.11 [0.03, 0.50] | +0.26 [0.08, 0.95] | +0.31 [0.05, 1.37] |
| E11 | 0.00 [−0.03, 0.09] | +0.01 [−0.07, 0.19] | +0.16 [−0.12, 0.86] | +0.26 [−0.17, 1.46] |

- **CSI(ML) − CSI(pySTEPS):** intervals include 0 at 30–120 min on all events. From 150 min the interval upper bound is at or below 0 on every event, because calibrated p < 0.5 there.
- Upper interval bounds are wide because BSS is a ratio.

**Calibration** (`reliability.csv`, fig. 19):
- ML ECE is 0.002–0.004 in every lead bin, against 0.002–0.030 for NP31, which is over-confident from 60 min on.
- Isotonic calibration (validation-fitted) caps the 150–360 min probabilities below 0.5: high raw probabilities verified only ~27 % there. That cap is why the p ≥ 0.5 CSI/FSS are 0 from 150 min. It is honest calibration, not a bug.

**Inflow edge** (`metrics_edge_only.csv`; the pixels pySTEPS cannot forecast, outside V):

| Lead | ML BSS | NP31 BSS | ML POD (p ≥ 0.5) | pySTEPS POD |
|---|---|---|---|---|
| 30 min | 0.43 | 0.37 | 0.38 | 0.21 |
| 120 min | 0.22 | 0.11 | — | — |

This is the one place the model adds placement information for entering storms, from its persistence-neighbourhood features.

## 4. Findings

1. **Probabilistic skill.**
   - A lightweight GBDT on pySTEPS-derived and recent-IR features gives calibrated probabilities with positive BSS to ~4 h. Every baseline is negative beyond ~1–2 h.
   - Against the fair no-fit reference NP31, the gain is significant within E8 and E10 at every lead, but **not on E11** (the weak event).
2. **No deterministic gain beyond 1 h.**
   - At the pre-declared p ≥ 0.5, CSI/FSS beat pySTEPS only at 60 min (CSI 0.452 vs 0.429) and are 0 from 150 min.
   - A validation-chosen threshold would be a new model version (ml-v1). It must be judged on events that have not been seen. It was **not** tuned on these test events.
3. **Mechanism.**
   - Most of the gain is calibrated neighbourhood smoothing of pySTEPS plus lead dependence.
   - Development (initiation) is not demonstrably learned: tendency and diurnal features have small importance, and there is no initiation-specific score.
   - The residual placement/development error identified in Phase 5 remains largely unsolved.

## 5. Figures

| # | File | Content |
|---|---|---|
| 17 | `data/figures/phase6_fig17_skill_vs_lead.png` | CSI, FSS 40 km, BSS, bias vs lead, all 5 methods |
| 18 | `data/figures/phase6_fig18_ml_minus_pysteps_ci.png` | Per-event CSI(ML) − CSI(pySTEPS) and BSS(ML) − BSS(NP31) with block-bootstrap CIs |
| 19 | `data/figures/phase6_fig19_reliability.png` | Reliability diagrams + counts per lead bin (NP31, ML raw, ML calibrated) |
| 20 | `data/figures/phase6_fig20_example_probabilities.png` | pySTEPS event vs ML probability at +120 min, one issue per event (fig-7 rule) |
| 21 | `data/figures/phase6_fig21_validation_curve.png` | Validation log-loss vs boosting iteration |

## 6. Reproduce

```bash
.venv/bin/python -m pipelines.ingest.cpc_merged_ir --start 2026-05-18T00:00 --end 2026-05-31T23:00   # + 06..12 May
.venv/bin/python -m scripts.build_ml_dataset    # cubes + sampled rows, ~75 s/day (cached per day)
.venv/bin/python -m scripts.train_ml            # gate -> fit -> n_iter -> isotonic, ~100 s
.venv/bin/python -m scripts.evaluate_ml         # held-out scoring, ~30 min (--resummarise re-derives tables only)
.venv/bin/python -m scripts.ml_importance       # validation-only diagnostic
.venv/bin/python -m scripts.make_ml_figures
.venv/bin/python -m pytest -q                   # 67 tests (66 pass, 1 skipped: excluded event E8a)
```

**Pipeline fixes made in this phase:**
- **Download resume:** the NOAA server dropped long transfers, so the downloader now resumes `.part` files with HTTP Range and checks the total size. Manifest writes are file-locked and atomic, so parallel download processes cannot lose entries.
- **Calibration bug:** `calibrate` skipped empty lead bins after an evaluation crash. The crash came before any score existed, and the frozen model and calibrators were unchanged.

## 7. NEEDS VERIFICATION

1. **Backward-in-time test on 3 events from one month.**
   - Training (late May) follows the test days.
   - The ±1-day buffers limit, but cannot exclude, regime overlap.
   - A forward test needs pre-2026 data (e.g. GPM_MERGIR via Earthdata; not available here) or held-out events after 31 May.
2. **Thin training data.** Only 7 convective training days, exactly the gate minimum. Probabilities at long leads rest on few storm systems.
3. **Deterministic threshold.** p ≥ 0.5 follows VALIDATION_PLAN but is a poor operating point for calibrated long-lead probabilities. A validation-chosen threshold is untested.
4. **Development skill unmeasured.** There is no initiation-specific verification (e.g. CI objects, VALIDATION_PLAN §2). Terrain and NWP environment features (ARCHITECTURE stage 6) are absent.
5. **The BSS reference** is the per-lead training climatology, which differs from the test-day base rates. It is standard, but it flatters any forecast on high-base-rate days.
6. **Carried over:** single IR channel, 30-min cadence, parallax, pySTEPS local build, LightGBM → sklearn HGB substitution.
