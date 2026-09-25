# PRD — Storm Lifecycle Intelligence (SIH26084)

**Version:** 0.1 (Phase 0) · **Owner:** Product/Architecture · **Source of truth:** [`../SIH26084_Research_Report.md`](../SIH26084_Research_Report.md) · **Scope:** [REVIEW_AND_SCOPE.md](REVIEW_AND_SCOPE.md) §6

**Tags:**
- **VERIFIED** — from the research report
- **PROPOSED** — a design decision
- **NEEDS VERIFICATION** — unsupported by the research files

---

## 1. Problem

Severe convective storms (thunderstorms, lightning, hail, downbursts, cloudbursts) kill people in India every pre-monsoon and monsoon season. They develop within minutes, at scales NWP grids miss. SIH26084 asks for:
- a 0–6 h, 1–3 km nowcasting system that fuses multiple sources;
- detection of convective initiation;
- hazard forecasts;
- a GIS dashboard with storm-arrival countdowns. (VERIFIED — Part 1)

**Constraint:** no open live Indian radar or lightning data exists (VERIFIED — Part 6). The system must therefore be **satellite-first**, and every claim must be verified on real Indian events.

## 2. Users

| User | Needs | Primary screens |
|---|---|---|
| **Duty forecaster** (IMD / NCMRWF / state met centre) — primary | Which cells matter, what happens next, how sure we are, why | Live Situation, Cell Tracker, Explainability, Confidence |
| **District / State DM officer** (DDMA/SDMA) | Which districts, when, how bad | Hazard Map, Alert Center, ETA countdowns |
| **Evaluator / scientist** (SIH jury, NCMRWF) | Proof: labels, baselines, skill, limitations | Model Performance, Replay, Data Health |
| Aviation / agriculture (named in PS) — secondary | Area risk + timing | Hazard Map, Forecast timeline |

## 3. Goals

- **G-1** Detect convective initiation from geostationary IR before cells reach deep convection (BT < 235 K). Measure the lead time gained.
- **G-2** Track storm cells with lifecycle phase and merge/split genealogy.
- **G-3** Forecast **lifecycle transitions** (mature within 30/60 min, decay within 60 min, remaining lifetime).
- **G-4** Give hazard outputs per cell and per grid, with wording that matches the evidence:
  - calibrated probabilities (lightning, heavy rain)
  - potentials/indicators (hail, cloudburst, downburst)
- **G-5** Give ETAs to districts/towns with **conformal intervals whose empirical coverage is reported**.
- **G-6** Replay historical Indian events showing what was known, predicted and observed.
- **G-7** Publish a reproducible verification report against persistence, pySTEPS and rules baselines.

## 4. Non-goals

- Official warnings. Every alert is labelled **"Research prototype — not an IMD warning"**.
- National or global coverage. Radar-centric nowcasting. Running NWP.
- Simulated or hypothetical weather scenarios. There is no "SIMULATED" mode.
- Mobile apps, SMS gateways, multilingual UI beyond an optional EN/HI toggle.
- Generative/diffusion models as dependencies (Architecture C).

## 5. SIH requirements traceability

| PS requirement (VERIFIED) | How we meet it | Honest gap |
|---|---|---|
| 0–6 h lead time | Cell nowcast 0–2 h + gridded probability to 6 h (A: extrapolation; B: advection-informed U-Net) | Skill decays after ~1–2 h; shown with a skill-vs-lead curve |
| 1–3 km resolution | 2 km product grid | Effective IR resolution ~3–5 km; 1 km only in TERLS radar and daytime VIS |
| Multi-source fusion | Geo IR/VIS/WV + NWP/reanalysis environment + satellite precipitation + (sparse) lightning + DEM; radar in the TERLS case | Live DWR and lightning unavailable → adapter interfaces |
| Early CI detection | Interest fields + LightGBM CI head | — |
| Lightning strike density | P(lightning ≤ 60 min) per cell/grid | Probability of occurrence, not density; ISS-LIS labels are sparse |
| Hail probability | Hail **potential** index | Ground-truth labels are sparse → "potential" |
| Downburst velocity | Downburst **indicator** (DCAPE + collapse signature) | No labels → not verified; no velocity claimed |
| Cloudburst thresholds | Cloudburst **indicator** (rain-rate threshold + stationarity + terrain) | 10 km rain products can't verify the 100 mm/h over ~20–30 km² definition |
| DWR / INSAT / lightning ingestion | SEVIRI + INSAT ingest live/replay; DWR & lightning adapters (PyScanCf, CSV strokes) | Restricted data |
| GIS dashboard + countdowns | MapLibre/deck.gl map + ETA countdown with interval | — |

## 6. Product architecture (summary; details in [ARCHITECTURE.md](ARCHITECTURE.md))

```
Data → QC → Common 2 km grid → Convective detection → Cell tracking → Lifecycle features
     → Baselines → ML heads → Hazard prediction → Calibration → ETA → Uncertainty → GIS/API/UI
```

**Modes:**
- **LIVE** — Meteosat hourly NRT + GFS + GSMaP_NOW
- **REPLAY** — historical, latency-faithful

Every output carries the **prediction envelope** (§6.1).

### 6.1 Prediction envelope (mandatory on every prediction) — PROPOSED

```json
{
  "issued_at": "2026-05-14T08:45:00Z",
  "valid_at": "2026-05-14T09:45:00Z",
  "lead_min": 60,
  "mode": "REPLAY",
  "model": {"name": "lgbm_lightning", "version": "0.3.1", "git_sha": "abc1234", "train_window": "2017-03..2021-09"},
  "inputs": [
    {"source": "SEVIRI_IODC", "obs_time": "2026-05-14T08:30:00Z", "latency_min": 15, "status": "OK"},
    {"source": "GFS_0p25", "cycle": "2026-05-14T00:00Z", "status": "OK"},
    {"source": "DWR", "status": "UNAVAILABLE"}
  ],
  "data_tier": "SAT+NWP",
  "calibrated": true,
  "evidence_level": "PROBABILITY | POTENTIAL | INDICATOR"
}
```

**Acceptance:** API responses without an envelope fail contract tests; the UI shows model version + data tier on every card.

---

## 7. Features (Purpose · Input · Output · Acceptance)

### F1 Data inputs & ingestion

| Item | Content |
|---|---|
| Purpose | Reproducibly acquire every dataset listed in [DATA_REALITY.md](DATA_REALITY.md) |
| Input | Credentials (EUMETSAT, Earthdata, CDS, MOSDAC, JAXA); config (domain, period, channels) |
| Output | Raw files under `data/raw/<source>/` + manifest (source, file, obs time, download time, checksum, licence) |
| Acceptance | Re-running ingest for a day is idempotent. The manifest lists 100 % of files. Missing slots are recorded, not silently skipped. Credentials never enter git. |

### F2 QC + common grid

| Item | Content |
|---|---|
| Purpose | One consistent 2 km equal-area grid with brightness temperatures and QC flags |
| Input | SEVIRI L1.5 / INSAT L1B, DEM |
| Output | Daily Zarr cube: BT per channel, VIS reflectance (day), QC mask, solar zenith, platform id |
| Acceptance | Checks pass: BT range 170–330 K, missing-line detection, time monotonic. Regridding error vs native pixel < 1 K RMS on a flat test field. Parallax on/off flag recorded. |

### F3 Convective detection & CI

| Item | Content |
|---|---|
| Purpose | Flag young clouds likely to become deep convection within 60 min |
| Input | Interest fields (10.8 µm BT, ΔBT 15/30 min, WV−IR BTD, tri-spectral 8.7−10.8−12.0, VIS texture by day), environment (CAPE, CIN, shear, PWAT, freezing level) |
| Output | Per young-cloud object: P(CI ≤ 60 min) + envelope |
| Acceptance | On the test split, CSI above the Mecikalski-rules baseline, with a bootstrap 95 % CI excluding zero — **reported either way**. Lead time gained (median minutes before first BT < 235 K) is reported. |

### F4 Storm-cell tracking & genealogy

| Item | Content |
|---|---|
| Purpose | Persistent cell IDs, polygons, motion, merge/split history |
| Input | −BT field; tobac thresholds [273, 253, 235, 221, 208 K]; watershed at 245 K |
| Output | `cells` (id, track_id, time, polygon, centroid, attributes); `genealogy_edges` (parent, child, type, time) |
| Acceptance | On 5 hand-checked days, ≥ 90 % of mature cells tracked ≥ 3 consecutive frames without ID swap (manual audit sheet). Merge/split events are rendered in the tree. Runtime < 2 min per 15-min frame on a laptop. |

### F5 Storm lifecycle (phase + transitions)

| Item | Content |
|---|---|
| Purpose | Objective current phase + forecast of the next phase and remaining lifetime |
| Input | Cell time series (min BT, area, cooling rate, OT flag, rain trend), environment, genealogy features |
| Output | `phase_now` ∈ {Initiation, Developing, Mature, Decaying, Dissipated}; P(→Mature ≤ 30/60 min); P(decay ≤ 60 min); remaining-life median + IQR |
| Acceptance | The phase rule table is published in config and versioned. Transition Brier skill score vs the "stay in phase" and climatological-matrix baselines is reported per horizon. Reliability diagram is shown. The C-index for time-to-decay is reported. |

**Phase rules (PROPOSED defaults from the report §9.2; mentor sign-off = D7):**

| Phase | Rule |
|---|---|
| Initiation | First detection at BT < 273 K with cooling ≤ −4 K/15 min |
| Developing | Area ↑ and min BT ↓ over 30 min |
| Mature | Min BT < 221 K, area change within ±10 %/30 min, or OT present |
| Decaying | Min BT ↑ ≥ 4 K/30 min and cold-core (< 221 K) area ↓ |
| Dissipated | Track ends |

### F6 Hazard prediction

| Head | Label source | Evidence level | Output | Acceptance |
|---|---|---|---|---|
| Lightning ≤ 60 min | ISS-LIS flashes (overpass-restricted) | PROBABILITY | P per cell + grid | AUPRC, BSS vs BT-rule baseline; reliability; test 2023 |
| Heavy rain ≥ 10/20 mm/h ≤ 60 min | IMERG | PROBABILITY | P per cell + grid | CSI/FSS vs persistence & extrapolated IMERG; test 2025–26 |
| Hail potential | GPM DPR ice/graupel-hail flags (train); IMD NW-India report 2026 (eval) | POTENTIAL (Low/Med/High) | Class per cell | POD at IMD report locations; ROC on DPR subset; FAR stated as not fully measurable |
| Cloudburst indicator | Rules (rain-rate threshold + motion < 10 km/h + slope) | INDICATOR | Flag + reasons | Case studies E5–E7 only; labelled "not verified" |
| Downburst indicator | Rules (DCAPE + rapid cloud-top warming/collapse) | INDICATOR | Flag + reasons | Case studies E3–E4 only; no velocity output |

**Common acceptance:** calibrated where labelled; the UI wording matches the evidence level; no hazard output without an envelope.

### F7 ETA + uncertainty

| Item | Content |
|---|---|
| Purpose | Countdown to arrival at districts/towns, with honest intervals |
| Input | Kalman-smoothed cell motion, predicted polygons, place polygons/buffers, validation residuals |
| Output | `eta_min`, `lo_80/hi_80`, `lo_90/hi_90`, `p_arrival` (probability the cell reaches the place before dissipating) |
| Definition | **Arrival** = first time the cell's cold core (BT < 235 K, parallax-corrected when enabled) intersects the place polygon/10 km buffer. It is not rain or gust arrival (stated in the UI). |
| Acceptance | ETA MAE by lead bin reported vs the constant-velocity baseline. Empirical coverage of 80/90 % intervals on the test split is within ±5 pp of nominal, **or the shortfall is shown**. |

### F8 Explainability

| Item | Content |
|---|---|
| Purpose | Show why a cell got its outputs, in physical units |
| Input | Trained LightGBM models + feature values + climatology (per month, per domain) |
| Output | Top-4 SHAP contributors, each with raw value and percentile; feature-group importance (satellite / environment / genealogy / time) |
| Acceptance | SHAP values sum to the model margin (TreeExplainer check). Percentiles are computed from training years only. The explanation panel loads in < 500 ms. |

### F9 Historical replay (spec: [REPLAY_SPEC.md](REPLAY_SPEC.md))

| Item | Content |
|---|---|
| Purpose | Show judges what the system knew / predicted / what happened |
| Input | Event list E1–E9, latency table, frozen model version |
| Output | Bundles `replay/{event}/{t}.json` + tiles; scorecard |
| Acceptance | Leakage test passes: no input with `obs_time + latency > t`. Replay events are excluded from training/calibration. The baseline toggle works on every frame. |

### F10 Validation (spec: [VALIDATION_PLAN.md](VALIDATION_PLAN.md))

| Item | Content |
|---|---|
| Purpose | Single source of every reported number |
| Input | Frozen predictions for model + baselines on test splits |
| Output | `evaluation/report.html` + JSON of all metrics + commit hash |
| Acceptance | Every PPT/UI metric links to a report entry. Bootstrap CIs are included. Nothing is computed on training or synthetic data. |

### F11 GIS dashboard (spec: [UI_UX_SPEC.md](UI_UX_SPEC.md))

| Item | Content |
|---|---|
| Purpose | Map-first decision support |
| Input | APIs below |
| Output | 10 screens |
| Acceptance | Map ≥ 55 % of viewport at 1440 px width. Mode badge (LIVE/REPLAY) is always visible. Every card shows valid time (UTC + IST), model version and data tier. Pan/zoom holds 60 fps with ≤ 500 cells. |

### F12 Alerts

| Item | Content |
|---|---|
| Purpose | Turn calibrated outputs into reviewable, district-level alerts |
| Input | Hazard P/indicators, ETA intervals, thresholds per hazard (config) |
| Output | Draft alerts → forecaster approve/reject → CAP 1.2 XML (status `Exercise`), auto-expiry on cell decay, audit log |
| Acceptance | No alert is issued without human approval in UI. The CAP validates against the schema. Every alert shows its lead time and the source prediction IDs. Label: "Research prototype — not an official IMD warning". |

---

## 8. ML pipeline (summary)

1. Features: per cell, 0/15/30/60-min stats + environment + genealogy + DEM + local solar time.
2. Models: LightGBM per head; logistic regression sanity baseline.
3. Calibration: isotonic regression on the validation split.
4. Uncertainty: conformal ETA intervals; bootstrap CIs for metrics. Deep ensembles only in stretch B.
5. Explainability: SHAP TreeExplainer.
6. Versioning: model artifact + model card + training manifest hash.

## 9. APIs (details in [ARCHITECTURE.md](ARCHITECTURE.md) §5)

`/health` · `/sources/status` · `/frames?from&to` · `/cells?t=` · `/cells/{id}` · `/cells/{id}/history` · `/cells/{id}/genealogy` · `/cells/{id}/explain` · `/forecast/grid?hazard&lead&t` · `/eta?place_id&t` · `/alerts` (GET/POST approve) · `/alerts/{id}/cap` · `/replay/events` · `/replay/{event}/{t}` · `/metrics?task&split` · `/models`

## 10. Database (details in [ARCHITECTURE.md](ARCHITECTURE.md) §6)

PostgreSQL + PostGIS tables:
- `sources`, `ingest_files`
- `frames`, `cells`, `tracks`, `genealogy_edges`
- `predictions`, `eta_predictions`
- `places`, `alerts`, `alert_audit`
- `replay_events`, `metrics`, `models`

Rasters stay on disk as Zarr/COG, not in the DB.

## 11. Security

- Credentials in `.env` / OS keychain; `.env` is git-ignored; secrets are never logged.
- Public read-only API for the demo. Alert approval and admin endpoints require a token.
- Respect data terms:
  - Don't republish raw MOSDAC L1B or EUMETSAT files. Serve only derived products. (Redistribution terms — NEEDS VERIFICATION per source.)
  - Attribute every source on Data Health.
- No impersonation: no IMD/NDMA logos. Alerts carry CAP `status=Exercise` and a disclaimer.
- Dependency licence audit (`pip-licenses`, `license-checker`) in CI. GPL components are isolated (D5).

## 12. Performance targets (PROPOSED)

| Step | Budget |
|---|---|
| Ingest one 15-min slot (cropped) | < 3 min |
| Regrid + QC | < 1 min |
| Tracking | < 2 min |
| Features + inference (all heads) | < 1 min CPU |
| Tile rendering | < 1 min |
| **Cycle total** | **< 8 min of every 15** |
| API p95 | < 300 ms |
| Replay frame switch | < 300 ms (preloaded) |

## 13. Limitations (state these in UI and PPT)

- Effective resolution ~3–5 km IR; not 1 km.
- Live mode is hourly (Meteosat NRT), not 15 min. INSAT L1B for general users arrives ≥ 3 days late → replay only.
- Lightning labels are ISS-LIS overpass samples up to Nov 2023 only.
- Hail and cloudburst ground truth is sparse; downburst is unverified.
- ETA is cold-cloud arrival, not rain or gust arrival.
- Skill beyond ~2 h is limited in Architecture A.

## 14. Future scope

- IMD DWR adapter (PyScanCf) → radar features + TRT-style severity; NRSC LDSN / IITM ILLN lightning labels.
- NCUM-R 1.5 km blending for 2–6 h.
- Advection-informed U-Net and LightningCast transfer (B).
- Generative ensembles with per-member tracking (C).
- INSAT-3DS NRT, once privileged access is arranged.
