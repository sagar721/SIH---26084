# Final Claims — SIH26084 Satellite Nowcasting Prototype (evidence frozen at ml-v0)

**Status:** Phase 7 freeze.
- Every number below is copied from a frozen output file named next to it.
- Each file's SHA-256 is in [`docs/FREEZE_ml-v0.json`](FREEZE_ml-v0.json), and `tests/test_phase7_freeze.py` fails if any of them changes.
- No model, dataset, threshold or result was changed in Phase 7.

**Scope of all claims:**
- NOAA/NCEP/CPC merged IR (single ~11 µm channel, 4 km, 30 min).
- NW-India domain 26–34° N, 72–84° E.
- Event = cloud-top BT < 235 K (deep convection).
- **Three held-out event days:** E8 14 May, E10 4 May, E11 16 May 2026.

Abbreviations: P = persistence; pySTEPS = Lucas–Kanade + semi-Lagrangian extrapolation; NP31 = no-fit neighbourhood probability of pySTEPS (31×31 px); ML = ml-v0 calibrated gradient-boosting probability.

---

## A. Supported claims

| # | Claim | Evidence (frozen file → value) |
|---|---|---|
| A1 | **A real-data pipeline runs end-to-end and reproducibly:** download → QC → 2 km grid → cells → baselines → ML → verification. | Raw files with SHA-256 in `data/raw/cpc_merged_ir/manifest.json`; reruns byte-identical (Phases 2–6 provenance); full test suite passes (count recorded in `FREEZE_ml-v0.json`). |
| A2 | **pySTEPS beats persistence at every lead from 30 to 360 min, on all 3 events** (CSI and FSS 40 km). | `multi_event/cross_event_by_lead.csv`: pooled CSI P → pySTEPS 0.511 → 0.586 (30 min), 0.342 → 0.429 (60), 0.176 → 0.258 (120), 0.092 → 0.172 (180); pySTEPS better on 3 of 3 events at every lead for CSI and FSS 40 km. |
| A3 | **Extrapolation skill is useful only to about 2 h**, and neither baseline is useful at 6 h. | `multi_event/decay_by_event.csv`: FSS 40 km ≥ 0.5 + f0/2 up to 90 min (P) and 120 min (pySTEPS) on each event. |
| A4 | **pySTEPS's growing frequency bias is mostly a scoring-region (inflow-edge) effect, not missing storm decay.** | `multi_event/phase5/decomposition_by_lead.csv`, E8 at 360 min: bias 2.61 = edge 3.76 × advected area 0.73 × intensity 0.96 (exact factorisation); 76 % of observed cold pixels lie in the unscored edge. |
| A5 | **ml-v0 gives better probabilistic deep-convection forecasts than every baseline, to about 4 h.** | `ml_eval/ml-v0/metrics_pooled_lead.csv` (mask V), BSS vs training climatology, ML vs NP31: 0.67 vs 0.63 (30 min), 0.51 vs 0.41 (60), 0.27 vs 0.02 (120), 0.13 vs −0.23 (180). pySTEPS: 0.44, 0.10, −0.38, −0.67. |
| A6 | **ml-v0 beats the no-fit neighbourhood reference within E8 and E10.** On E11 the difference is not significant. | `ml_eval/ml-v0/bootstrap_ml_vs_pysteps.csv`, BSS(ML) − BSS(NP31), 95 % block bootstrap. E8: +0.04 [0.03, 0.11] at 30 min, +0.27 [0.04, 0.92] at 120 min. E10: +0.03 [0.01, 0.11], +0.26 [0.08, 0.95]. E11: 0.00 [−0.03, 0.09], +0.16 [−0.12, 0.86]. |
| A7 | **ml-v0 probabilities are well calibrated** on the held-out days. | `ml_eval/ml-v0/reliability.csv` (10 bins): ECE = Σ\|Σp − Σo\| / n = 0.0022 / 0.0034 / 0.0042 / 0.0026 (lead bins 30 / 60 / 90–120 / 150–360 min) for ML, vs up to 0.030 for NP31 (fig. 19). |
| A8 | **Train / validation / test are separated by calendar day.** Event days ±1 day are never used for fitting; test events were scored once with the frozen model. | `config/ml_dataset.yaml`, `data/processed/ml_dataset/dataset_manifest.json` (forbidden days listed), `data/models/ml-v0/model_card.json`; tests in `tests/test_phase6.py`. |
| A9 | **The Phase-1 tobac tracks are unusable as per-cell truth**, and overlap-based v2 tracking fixes the linking errors. Object metrics are diagnostic only. | `E8_20260514/audit/audit_v1.json` vs `audit_v2_none.json`: ID-switch candidates 0.206 → 0.004, zero-overlap links 0.057 → 0, direction reversals 0.47 → 0.35. |
| A10 | **Diagnostic only:** at 30 min, advection places cold cells closer than persistence on all 3 events. | `multi_event/object_diagnostics_by_event.csv` (v2 tracks): 0.59 / 0.62 / 0.57 of paired cases (43 / 66 / 18 cells). |
| A11 | **A decay-aware pySTEPS extension is not justified** by the available lifecycle features. | `multi_event/phase5/lifecycle_decision.json` = STOP (no tendency persistence on the development event); oracle area correction gains ≤ +0.04 CSI on E8/E10 (`decomposition_by_lead.csv`). |
| A12 | **In the inflow edge**, where pySTEPS has no forecast, ml-v0 keeps skill. | `ml_eval/ml-v0/metrics_edge_only.csv`: BSS 0.43 (30 min), 0.22 (120) vs NP31 0.37, 0.11. |

## B. Results that must be stated alongside the claims (negative or neutral)

| # | Result | Evidence |
|---|---|---|
| B1 | **As a yes/no forecast at the pre-declared p ≥ 0.5, ml-v0 does not beat pySTEPS beyond 60 min.** It forecasts no event from 150 min (calibrated p < 0.5). | `metrics_pooled_lead.csv`, CSI ML vs pySTEPS: 0.583 vs 0.586 (30 min), 0.452 vs 0.429 (60), 0.243 vs 0.258 (120), 0.000 vs 0.172 (180). |
| B2 | **ml-v0 is mostly a calibrated neighbourhood smoothing of pySTEPS.** Storm-initiation skill is not demonstrated. | `data/models/ml-v0/permutation_importance_validation.csv`: largest = pySTEPS 31-px event fraction (0.019 log-loss); tendency and diurnal terms ≤ 0.003. |
| B3 | **The 1 May 2026 hail day was excluded** by a rule fixed beforehand: too little cloud colder than 235 K. | `multi_event/event_qc.csv`: deep-convection frames 21 % < 50 %. |
| B4 | **Object-level claims go no further than 30 min.** The 60-min advantage fails on E11. | `object_diagnostics_by_event.csv`: E11 at 60 min = 0.42 (15 cells). |

## C. Claims that must NOT be made

1. **Not "ML beats pySTEPS" as a deterministic / yes-no forecast** (B1). Only the probabilistic (BSS) claim is supported.
2. **No skill at 6 h**, and no "0–6 h nowcasting skill". Useful skill ends by about 2 h (extrapolation) and about 4 h (ML probability, BSS > 0).
3. **No generalisation** beyond three pre-monsoon days of May 2026 in NW India: not to the monsoon, other regions, other years or other satellites.
4. **No statistical significance across events.** Three events cannot give p < 0.05 (the best sign test is p = 0.125). The intervals quoted are within-event.
5. **No hail, lightning, heavy-rain or cloudburst forecasting skill.** The only truth used is satellite BT < 235 K; IMD hail reports were used only to choose event days.
6. **Not "AI predicts storm initiation or development"** (B2), and no lifecycle-phase or decay prediction (Phase 5 STOP).
7. **No cell-tracking accuracy figure** (PRD's ≥ 90 % criterion is not assessed). There is no independent radar, lightning or manual truth.
8. **No forward-in-time validation.** The model was trained on days after the test days.
9. **Not operational, real-time or live.** No MOSDAC/INSAT or EUMETSAT/Meteosat data were used; there is no latency test and no alert service.
10. **No 15-minute forecasts.** The source cadence is 30 min.
11. **No deep learning.** None was used.
12. **No comparison with IMD/NCMRWF operational systems**, and no guarantee of SIH selection.

## D. Limitations (must accompany any result)

| Limitation | Effect |
|---|---|
| **Only 3 held-out event days** (E8, E10, E11), one month, one region | No cross-event significance; E11 is weak (base rate 0.4 %) |
| **Backward-in-time test** | Training (18–31 May) follows the test days; ±1-day buffers limit, but do not rule out, weather-regime overlap |
| **Thin training data** | 14 training days, of which 7 are convective (exactly the gate minimum); 7 validation days |
| **30-min satellite cadence** | No 15-min leads; motion estimated from 60 min of history |
| **Single IR channel** (CPC merged IR, 4 km) | No water-vapour / tri-spectral / visible cues for initiation; the NOAA source substitutes for Meteosat/INSAT |
| **No independent radar or lightning validation** | Truth is the same satellite field; tracking and object metrics are unvalidated |
| **Scoring edge** | Long-lead baseline scores cover a shrinking eastern region (unscorable fraction 9 → 35 % on E8) |
| **Other open items** | Parallax not corrected; satellite-ID code meaning unverified; pySTEPS built locally without OpenMP; LightGBM replaced by sklearn HistGradientBoosting; hail-report place/state mapping from PDF text order |

## E. Where each phase's full evidence lives

| Phase | Document | Frozen outputs |
|---|---|---|
| 1 | `docs/FIRST_EVENT.md` | `data/processed/E8_20260514/` (cells, mask, run_summary) |
| 2 | `docs/BASELINE_EVAL.md` | `data/processed/<event>/baseline/` |
| 3 | `docs/TRACKING_AUDIT.md` | `data/processed/<event>/audit/`, `tracking_v2_*` |
| 4 | `docs/MULTI_EVENT.md` | `data/processed/multi_event/` |
| 5 | `docs/DECAY_AWARE.md` | `data/processed/multi_event/phase5/` |
| 6 | `docs/ML_PROTOTYPE.md` | `data/models/ml-v0/`, `data/processed/ml_dataset/`, `data/processed/ml_eval/ml-v0/` |
