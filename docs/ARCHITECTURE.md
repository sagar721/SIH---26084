# Technical Architecture — Storm Lifecycle Intelligence

**Version:** 0.1 (Phase 0) · Implements [PRD.md](PRD.md) · **Architecture A = minimum system; B = stretch; C = not a dependency**

**Tags:**
- **VERIFIED** — from the research report
- **PROPOSED** — a design decision
- **NEEDS VERIFICATION** — unsupported by the research files

---

## 1. System context

```
            ┌───────────── External sources (see DATA_REALITY.md) ─────────────┐
            │ EUMETSAT Data Store (SEVIRI IODC) · MOSDAC (INSAT-3DR/3DS, TERLS) │
            │ Copernicus CDS (ERA5) · NCMRWF RDS (IMDAA) · NOMADS (GFS)         │
            │ NASA Earthdata (IMERG, ISS-LIS, GPM DPR) · JAXA (GSMaP)           │
            │ IMD hail report (PDF) · Boundaries/DEM                            │
            └───────────────┬──────────────────────────────────────────────────┘
                            │ pipelines/ingest (scheduled or backfill)
                            ▼
  data/raw ──► pipelines/preprocess ──► data/interim (Zarr, 2 km grid)
                                              │
                        ml/tracking (tobac) ──┤──► PostGIS: frames, cells, tracks, genealogy
                                              │
       ml/features ──► ml/forecasting (baselines + LightGBM heads + calibration + ETA/conformal)
                                              │──► PostGIS: predictions, eta_predictions
                                              │──► data/tiles (COG/PNG per frame, per hazard)
                                              ▼
                      services/api (FastAPI) ─┼──► apps/web (React/MapLibre/deck.gl)
                                              │
            ml/verification ──► evaluation report + metrics table (single source of numbers)
            pipelines/replay ──► data/replay/{event}/{t}.json bundles (latency-faithful)
```

## 2. Stack (PROPOSED; libraries VERIFIED in research Part 3)

| Layer | Choice | Licence |
|---|---|---|
| Frontend | React + TypeScript + Vite, Tailwind, MapLibre GL JS, deck.gl, Recharts (charts), D3-hierarchy (genealogy tree) | BSD-3 / MIT |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 + GeoAlchemy2, Uvicorn | MIT/BSD |
| DB | PostgreSQL 16 + PostGIS 3 | PostgreSQL / GPL-2 (server, not linked) |
| Weather/geo | xarray, dask, satpy, pyresample, rasterio, rioxarray, MetPy, pySTEPS, tobac, shapely, geopandas, zarr | Apache/BSD/MIT |
| ML | LightGBM, scikit-learn (isotonic, metrics), SHAP, scikit-survival or lifelines (survival), PyTorch (stretch B only) | MIT/BSD |
| Verification | xskillscore, scoringrules, pysteps.verification | Apache-2.0 / BSD-3 |
| Orchestration | Makefile + Typer CLI; cron/APScheduler for live mode (Prefect optional) | — |
| Packaging | Docker Compose (db, api, web, worker) | — |

**Licence rule:** only permissive dependencies in the core. GPL-3.0 code (LightningCast, ProbSevere scripts) lives in a separate optional service (`services/lightningcast/`), called over HTTP (decision D5).

## 3. Processing pipeline (every 15 min in replay/backfill; hourly in LIVE)

| # | Stage | Module | Input → Output | Key details |
|---|---|---|---|---|
| 1 | **Ingest** | `pipelines/ingest/*` | Remote → `data/raw` + `ingest_files` rows | `eumdac` (SEVIRI; Data Tailor crop — NEEDS VERIFICATION of crop options), `mdapi.py` (MOSDAC), `cdsapi`, `earthaccess` (NASA), GFS grib filter. Checksums; retries; idempotent. |
| 2 | **QC** | `pipelines/preprocess/qc.py` | Raw → QC mask | BT range, missing lines, duplicate slots, solar zenith. Slots failing QC → `frames.status='QC_FAIL'`. |
| 3 | **Common grid** | `pipelines/preprocess/regrid.py` | → Zarr (2 km LAEA, centre 30°N 78°E, domain 26–34°N 72–84°E ≈ 600×450 px) | satpy + pyresample (bilinear for BT, nearest for masks). Optional parallax correction (NEEDS VERIFICATION of satpy API). `platform` recorded (MSG1/MSG2/INSAT-3DR/3DS). |
| 4 | **Convective detection** | `ml/tracking/detect.py` | BT cube → features per frame | tobac `feature_detection_multithreshold` on −BT at [273, 253, 235, 221, 208 K]; minimum area 4 px (PROPOSED; tune). |
| 5 | **Cell tracking** | `ml/tracking/track.py` | Features → cells/tracks | tobac `segmentation_2D` (watershed at 245 K) → polygons; `linking_trackpy` (v_max tuned); `merge_split_MEST` → `genealogy_edges`. Fallback: pySTEPS T-DaTing. |
| 6 | **Lifecycle features** | `ml/features/cell_features.py` | Tracks + env → feature table (parquet) | min/mean BT, ΔBT 15/30/60, area & growth, OT flag, BTDs, VIS texture, motion (Kalman), age, n_merges/splits, CAPE/CIN/shear/PWAT/freezing level/DCAPE (MetPy on ERA5/GFS), DEM slope, local solar time. |
| 7 | **Phase labelling** | `ml/tracking/phases.py` | Feature series → `phase_now` | Rule table from `config/phases.yaml` (versioned). |
| 8 | **Baselines** | `ml/forecasting/baselines/` | Frames/tracks → baseline forecasts | Persistence; pySTEPS Lucas–Kanade + semi-Lagrangian on BT and IMERG; Mecikalski CI rules; constant-velocity ETA; "stay-in-phase" transitions; climatological transition matrix. |
| 9 | **ML heads** | `ml/models/` | Features → raw scores | LightGBM: `ci`, `transition_{30,60}`, `survival` (discrete-time hazard), `lightning_60`, `heavyrain_{10,20}`, `hail_potential`. Rule modules: `cloudburst_indicator`, `downburst_indicator`. |
| 10 | **Calibration** | `ml/forecasting/calibrate.py` | Raw → calibrated probabilities | Isotonic per head per lead bin, fitted on the validation split only. |
| 11 | **ETA** | `ml/forecasting/eta.py` | Cell motion + polygons + places → ETA | Advect polygon along smoothed motion (with pySTEPS field-motion prior for young cells); first intersection with place polygon/10 km buffer. |
| 12 | **Uncertainty** | `ml/forecasting/conformal.py` | Validation residuals → intervals | Split conformal per lead bin (0–30, 30–60, 60–120, 120+ min), 80/90 %. `p_arrival` from the survival head × geometric reach. |
| 13 | **GIS products** | `pipelines/tiles/render.py` | Grids → COG + PNG overlays; cells → GeoJSON | One PNG per (frame, layer) with bounds, for the MapLibre image source / deck.gl BitmapLayer. Vector cells via API. |
| 14 | **Persist + serve** | `services/api` | DB + tiles → JSON/GeoJSON/CAP | Every response wrapped in the prediction envelope (PRD §6.1). |

**Stretch B modules (not dependencies):**
- `ml/models/unet_advect.py` — Metzl-style advection-informed U-Net; re-implemented from the paper, not copied
- `services/lightningcast/` — GPL, isolated
- `pipelines/ingest/terls.py` + `ml/tracking/radar_tint.py` — TERLS radar case with Py-ART/TINT

## 4. Data contracts (PROPOSED)

### Zarr cube `data/interim/grid2km/{YYYY-MM-DD}.zarr`
- `time` (15-min steps)
- `y`, `x` (LAEA metres)
- `lat(y,x)`, `lon(y,x)`
- **Variables:**
  - `bt_039`, `bt_062|bt_068`, `bt_073`, `bt_087`, `bt_108`, `bt_120`, `bt_134` (K; channels absent for INSAT are NaN)
  - `refl_006`, `refl_016` (daytime)
  - `sza`, `qc`
  - `platform(time)`

### Cell feature table (parquet)
- One row per (cell_id, time).
- Keys: `track_id`, `cell_id`, `time`, `platform`
- Features: as in stage 6
- Labels: `y_ci_60`, `y_phase_30`, `y_phase_60`, `t_to_decay`, `event_decay`, `y_ltg_60`, `ltg_observed` (LIS overpass mask), `y_rain10_60`, `y_rain20_60`, `y_hail_dpr`
- `split` ∈ {train, val, test, event_holdout}

### Replay bundle
See [REPLAY_SPEC.md](REPLAY_SPEC.md) §4.

## 5. API (FastAPI, `/api/v1`) — PROPOSED

| Method & path | Query | Returns |
|---|---|---|
| GET `/health` | — | Service + DB status |
| GET `/sources/status` | `t` | Per source: last obs time, latency, status, licence note |
| GET `/frames` | `from,to,mode` | Available frame times + layer URLs |
| GET `/cells` | `t, bbox?, min_phase?` | GeoJSON FeatureCollection (polygon, phase, key probs, envelope) |
| GET `/cells/{id}` | `t` | Full cell card (§9.3 of the report) |
| GET `/cells/{id}/history` | — | Time series (min BT, area, probs, phase) |
| GET `/cells/{id}/genealogy` | — | Nodes + edges (merge/split) |
| GET `/cells/{id}/explain` | `t, head` | SHAP top-k with raw values + percentiles |
| GET `/forecast/grid` | `hazard, lead, t` | Tile URL + bounds + envelope + validated skill at that lead |
| GET `/eta` | `place_id \| lat,lon ; t` | List of cells → eta, intervals, p_arrival |
| GET `/places` | `q, bbox` | Districts/towns |
| GET/POST `/alerts` | `status` / body | Draft, approve, reject (POST requires token) |
| GET `/alerts/{id}/cap` | — | CAP 1.2 XML (`status=Exercise`) |
| GET `/replay/events` | — | E1–E9 metadata |
| GET `/replay/{event}/{t}` | `baseline?` | Bundle (knew / predicted / happened) |
| GET `/metrics` | `task, split, method` | Metric values + CIs + report commit hash |
| GET `/models` | — | Model cards, versions, train windows |

**Contract tests:** every prediction-bearing response validates against the `Envelope` Pydantic model.

## 6. Database schema (PostGIS) — PROPOSED

```sql
sources(id, name, licence, url, access_status)                       -- AVAILABLE/PARTIAL/RESTRICTED
ingest_files(id, source_id, obs_time, path, sha256, bytes, downloaded_at, status)
frames(id, obs_time, platform, mode, status, zarr_path)              -- mode: LIVE/REPLAY
tracks(id, first_time, last_time, n_frames)
cells(id, track_id, frame_id, obs_time, geom geometry(Polygon,4326), centroid geometry(Point,4326),
      min_bt, area_km2, cooling_15, phase, attrs jsonb)
genealogy_edges(parent_track, child_track, type, time)               -- type: MERGE/SPLIT
models(id, name, version, git_sha, train_window, card jsonb)
predictions(id, cell_id null, frame_id, head, lead_min, value, evidence_level,
            calibrated bool, model_id, envelope jsonb)
eta_predictions(id, cell_id, place_id, frame_id, eta_min, lo80, hi80, lo90, hi90, p_arrival, model_id)
places(id, name, kind, geom geometry(MultiPolygon,4326), state)      -- district/town buffer
alerts(id, place_id, hazard, severity, issued_at, expires_at, status, source_prediction_ids int[], cap_xml)
alert_audit(id, alert_id, action, actor, at, note)
replay_events(id, code, name, t0, window_start, window_end, notes)
metrics(id, task, split, method, metric, value, ci_lo, ci_hi, report_sha)
```

**Indexes:** GiST on `geom`/`centroid`; B-tree on `(obs_time)`, `(track_id, obs_time)`, `(head, frame_id)`.

## 7. Deployment

- `docker-compose.yml` services:
  - `db` (postgis)
  - `api`
  - `worker` (pipelines/ML CLI)
  - `web` (nginx serving the Vite build)
  - optional `lightningcast`
- Volumes: `data/`.
- **Offline demo:** replay bundles + tiles precomputed; no network needed.
- Config via `config/*.yaml` + `.env` (secrets).

## 8. Observability

- Structured logs (JSON), one `run_id` per cycle.
- Data Health reads `ingest_files` and `frames` — no separate metrics stack.

---

## 9. Repository structure (Task 9)

```
sih26084/
├── apps/
│   └── web/                 # React+TS+Vite+Tailwind+MapLibre+deck.gl — the 10 screens
│       ├── src/pages/       # live, cells, forecast, replay, hazards, explain, confidence, alerts, performance, health
│       ├── src/map/         # layer factories (BT, cells, hazards, ETA cones, places)
│       ├── src/components/  # shell, sidebar, context panel, timeline, cards, charts
│       └── src/api/         # typed client generated from OpenAPI
├── services/
│   ├── api/                 # FastAPI: routers/, schemas/ (Envelope etc.), db/ (models, migrations), cap/
│   └── lightningcast/       # OPTIONAL, GPL-isolated (stretch B)
├── ml/
│   ├── data/                # dataset builders: splits, event holdouts, label joins
│   ├── features/            # interest_fields.py, cell_features.py, env_features.py, climatology.py
│   ├── tracking/            # detect.py, track.py, genealogy.py, phases.py (tobac; T-DaTing fallback)
│   ├── models/              # lgbm heads, survival.py, rules (cloudburst/downburst), unet_advect.py (B)
│   ├── forecasting/         # baselines/, calibrate.py, eta.py, conformal.py, predict.py
│   └── verification/        # matching.py, scores.py, reliability.py, bootstrap.py, report.py
├── pipelines/
│   ├── ingest/              # eumetsat_seviri.py, mosdac_insat.py, era5.py, imdaa.py, gfs.py, imerg.py, isslis.py, gpm_dpr.py, gsmap.py, hail_report.py, terls.py
│   ├── preprocess/          # qc.py, regrid.py, parallax.py
│   ├── tiles/               # render.py
│   └── replay/              # build_bundle.py, latency.py, leakage_check.py
├── data/                    # git-ignored: raw/ interim/ processed/ tiles/ replay/ + PROVENANCE.md
├── notebooks/               # exploration only (never the source of reported numbers)
├── docs/                    # this folder
├── tests/                   # unit (metrics, labels, phases), leakage, contract (Envelope), golden replay
├── scripts/                 # bootstrap_accounts.md, download_event.sh, make_figures.py
└── config/                  # domain.yaml, grid.yaml, phases.yaml, thresholds.yaml, events.yaml, splits.yaml, latency.yaml
```
