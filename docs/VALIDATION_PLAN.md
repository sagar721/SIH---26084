# Validation Plan

**Principle:** every number shown in the UI or PPT comes from `ml/verification` running on **held-out, time-blocked, observed data**. We never report synthetic metrics, training-set metrics or plain accuracy on rare events. Results are reported **whether or not our model beats the baselines**.

---

## 1. Methods compared (same inputs, same scoring code)

| ID | Method | Applies to |
|---|---|---|
| M0 | **Persistence** — no change; for motion, last observed position | All tasks |
| M1 | **Optical flow / pySTEPS** — Lucas–Kanade motion + semi-Lagrangian extrapolation of BT (and of IMERG for rain); constant-velocity cell extrapolation for ETA | Grid, cell position, ETA, rain |
| M2 | **Rules** — Mecikalski CI interest-field rules (≥ 4 of 6); BT < 235 K lightning rule; CAPE-only / OT-only hail rule; stay-in-phase and climatological transition matrix | CI, lightning, hail, lifecycle |
| M3 | **Our model (Architecture A)** — calibrated LightGBM heads, survival model, Kalman ETA + conformal | All |
| M4 | [B-stretch] Advection-informed U-Net; LightningCast zero-shot / fine-tuned | Grid, lightning |

## 2. Tasks, truth, metrics

| Task | Truth | Unit of evaluation | Primary metrics | Secondary |
|---|---|---|---|---|
| CI ≤ 60 min | Track reaches BT < 235 K within 60 min | Young-cloud object | **CSI, POD, FAR** (performance diagram), **AUPRC** | Lead time gained (median min), BSS |
| Gridded deep-convection 0–6 h | BT < 235 K mask | 2 km grid, per lead | **FSS** at 10/20/40 km, CSI @ p ≥ 0.5 | BSS, reliability per lead |
| Cell position | Observed matched centroid | Matched cell, per lead | **Centroid error (km)** | **IoU** of polygons |
| Lifecycle transition | Rule phase at t+30/60 | Cell-time | **Brier/BSS** vs stay-in-phase and climatology matrix | Reliability; macro-F1 (next phase) |
| Remaining lifetime | Track end / decay time | Track | **C-index** | Integrated Brier score |
| Lightning ≤ 60 min | ISS-LIS flash within cell polygon, ±5 min, overpass-observed cells only | Cell-time under LIS view | **AUPRC, BSS**, CSI at best threshold | Reliability, POD/FAR |
| Heavy rain ≥ 10/20 mm/h ≤ 60 min | IMERG max in polygon | Cell-time; grid | **CSI**, **FSS** | BSS; RMSE/MAE of rain-rate magnitude only |
| Hail potential | GPM DPR flag (overpass subset); IMD 2026 report stations | Cell-day | **POD** at report locations; ROC-AUC on DPR subset | FAR **stated as not fully measurable** (incomplete reports) |
| ETA | First observed cold-core intersection with place polygon/10 km buffer | Cell–place pair | **ETA MAE (min)** by lead bin | Bias; hit rate of `p_arrival` (BSS) |
| ETA uncertainty | Same | Cell–place pair | **Empirical coverage** of 80/90 % intervals vs nominal | Mean interval width |
| Cloudburst / downburst indicators | Case studies (E3–E7) | Event | Qualitative timeline + hit/miss | — (**not verified**; no skill claimed) |

**Metric definitions** (from a contingency table of hits H, misses M, false alarms F):
- POD = H/(H+M)
- FAR = F/(H+F)
- CSI = H/(H+M+F)
- Bias = (H+F)/(H+M)
- BSS = 1 − BS/BS_ref, where the reference is the sample climatology of the training split
- FSS per Roberts & Lean (2008)
- Unit tests in `tests/verification/` check each metric on toy grids with known answers.

## 3. Time-blocked splits (per head)

A single split cannot serve every head, because label periods differ (risk K4).

| Head | Train | Validation (calibration + conformal) | Test | Notes |
|---|---|---|---|---|
| CI, tracking, lifecycle, ETA, gridded | 2019–2023 (Mar–Sep) | 2024 | **2025–2026** | Meteosat-8 (≤ May 2022) and -9 both present → `platform` feature; report test by platform |
| Heavy rain | 2019–2023 | 2024 | **2025–2026** | IMERG Final where available, else Late (flagged) |
| Lightning | 2017–2021 | 2022 | **2023** (to 16 Nov) | ISS-LIS period; test straddles only Meteosat-9 |
| Hail potential | DPR overpasses 2019–2024 | 2025 | **2026**: DPR subset + IMD NW-India report | Report and DPR evaluated separately |

**Event-day holdouts:**
- E1–E9 event days ±1 day are removed from **all** training *and* validation (calibration/conformal) sets (risk K5).
- They appear only in test metrics (if their year is a test year) and in replay.
- Events in train years (E1 2018, E2 2020) are therefore excluded entirely from fitting.

**Leakage checklist** (automated in `tests/leakage/` + signed off in Phase 11):
1. No random pixel or random cell-time splits; split by **calendar day**.
2. Climatology percentiles (Explainability) and feature normalisation are computed on train years only.
3. Calibration and conformal are fitted on validation only; never on test.
4. Features use only data with `obs_time + latency ≤ issue_time` (the same latency table as replay).
5. Tracking uses no future frames. Online linking only for predictions; offline full-track linking is allowed **only for label creation**.
6. Labels come from strictly future windows relative to issue time.
7. No hyper-parameter tuning on test; test metrics are computed once per frozen model version.

## 4. Object matching (cell-based scores)

- **Detection/position:** Hungarian assignment between forecast and observed cells at each valid time. Cost = centroid distance; match allowed if distance ≤ 25 km **or** IoU ≥ 0.1 (PROPOSED; sensitivity reported for 15/25/40 km).
  - Unmatched forecasts = false alarms.
  - Unmatched observed = misses.
- **CI objects:** a CI forecast is a hit if the same track (or a child via split) reaches 235 K within the window.
- **ETA pairs:** a (cell, place) pair enters evaluation when the forecast predicts arrival within 6 h **or** the observed cell arrives within 6 h. Missed arrivals and false arrivals are counted separately from the MAE.

## 5. Statistical reporting

- **Bootstrap:** 1,000 resamples **by event day**, giving 95 % CIs for every metric and for every difference (model − baseline).
- **Skill-vs-lead curves** (0–360 min) for all methods, on one plot per task.
- Sample sizes (n objects, n days) shown next to every metric.
- Stratification: platform, month (pre-monsoon vs monsoon), day/night (VIS available or not), terrain (plains vs Himalaya).

## 6. Calibration & uncertainty

- Reliability diagrams (10 bins, with counts) per head per lead bin; expected calibration error (ECE) as a secondary number.
- Isotonic calibration; compare pre- and post-calibration BSS on test.
- **Conformal ETA:** split conformal on absolute ETA residuals, fitted per lead bin (0–30, 30–60, 60–120, 120–360 min) on validation. Report empirical coverage and mean width on test. **Acceptance:** coverage within ±5 pp of nominal, or the shortfall is shown and explained (e.g., distribution shift by platform/month).

## 7. Ablations (research questions)

| # | Question | Comparison |
|---|---|---|
| A1 | Does genealogy help? | Transition/intensification models with vs without merge/split features |
| A2 | What does NWP environment add? | Satellite-only vs satellite + ERA5/GFS |
| A3 | Do WV / tri-spectral channels cut false alarms? | CI FAR with vs without BTD features (cf. CIUnet 2024) |
| A4 | Does parallax correction improve ETA? | ETA MAE with vs without correction |
| A5 | [B] What does radar add? | TERLS case: satellite-only vs radar-added |
| A6 | [B] Zero-shot vs fine-tuned LightningCast | AUPRC/BSS on the ISS-LIS test |

## 8. Outputs

- `evaluation/metrics.json` — every metric: task, method, split, lead, value, CI, n, model version, commit.
- `evaluation/report.html` — tables + figures (performance diagram, FSS vs scale, reliability, coverage, skill vs lead, ablations, stratifications).
- `metrics` DB table loaded from the JSON. UI "Model Performance" reads only this.
- **Freeze:** the report commit hash is shown in the UI and printed on the PPT results slide.

## 9. Pass/fail gates (for moving phases, not for "success" claims)

| Gate | Condition |
|---|---|
| Phase 4 | All baselines scored on all applicable test splits |
| Phase 5 | Every head has test metrics + CIs + reliability; leakage tests green |
| Phase 7 | Coverage table exists for 80/90 % |
| Phase 11 | Report regenerates bit-identically from a clean checkout; two-person sign-off |
