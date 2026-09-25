# StormLife Nowcast — SIH 2026, PS SIH26084

**Convective-scale nowcasting for thunderstorms, hail and cloudbursts (0–6 h).** Team **THE FEVICONS** (Team ID 167858).

StormLife Nowcast is a **satellite-first, replay-only research prototype**. It turns real satellite infrared imagery into detected and tracked storm cells, 0–6 h forecasts (persistence, pySTEPS advection, and a calibrated ML probability of deep convection), an honest validation scorecard, and a web dashboard that replays past events.

> **Not an operational or live system and not an official IMD warning.** It forecasts deep-convective cloud (cloud-top brightness temperature < 235 K), **not** hail, lightning or rainfall, and makes no 6-h ML skill claim. See [Limitations](#limitations).

## Main capabilities
- Ingest and quality-control NOAA/NCEP/CPC merged IR, regrid to a common 2 km grid (NW India, 26–34° N, 72–84° E).
- Detect, track and characterise storm cells (tobac + a v2 overlap tracker with an audit).
- Forecast 30–360 min ahead: persistence, pySTEPS, and HistGradientBoosting + isotonic calibration (model `ml-v0`).
- Verify on held-out event days (CSI, POD, FAR, bias, FSS, BSS, reliability, bootstrap).
- Replay events in a 9-screen React + MapLibre dashboard (situation, cells, forecast, replay, performance, confidence, data health, exercise alerts).

## Pipeline
```
NOAA CPC merged IR (4 km, 30 min) -> ingest + SHA-256 manifest -> QC / decode -> 2 km cube
  -> cell detection & tracking -> forecasts (persistence | pySTEPS | ML) -> validation
  -> evidence freeze (ml-v0, 386 hashed files) -> replay bundle -> web dashboard
```
Diagrams: [docs/DIAGRAMS.md](docs/DIAGRAMS.md). Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Data source
NOAA/NCEP/CPC *Globally Merged IR* (4 km, 30-min) for May 2026; event selection from an archived IMD hail-report PDF (`data/raw/hail_reports/`). No radar or lightning data; no MOSDAC/EUMETSAT accounts were used. Details: [data/PROVENANCE.md](data/PROVENANCE.md), [docs/DATA_REALITY.md](docs/DATA_REALITY.md).

## Install
Python 3.11 and Node.js are required. Exact versions are pinned in [requirements.txt](requirements.txt) (see the note there on the locally built pySTEPS).
```bash
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd apps/web && npm ci
```

## Run the web demo (replay)
Replay bundles are in `apps/web/public/bundles/`. If missing, rebuild them from the frozen outputs (needs the local data, see below):
```bash
.venv/bin/python -m pipelines.replay.build_bundle --event E8_20260514 E10_20260504 E11_20260516
cd apps/web && npm run build && npm run preview     # http://localhost:4173/
```
E8 (14 May 2026) is the main demo; E10 and E11 also open; other events are greyed with a reason. Walkthrough: [docs/PRODUCT_DEMO.md](docs/PRODUCT_DEMO.md).

## Run the tests
```bash
.venv/bin/python -m pytest -q                       # includes the evidence-freeze guard
cd apps/web && npm test                             # unit tests
cd apps/web && npx playwright install chromium && npm run e2e
```
Last verified: 76 passed / 1 skipped (Python), 6/6 unit, 2/2 e2e, type-check and build pass.

## Reproduce the research
Per-event pipeline (after the raw download): `bash scripts/run_event_pipeline.sh <EVENT>`; ML: `scripts/build_ml_dataset.py`, `train_ml.py`, `evaluate_ml.py`. Download example: `.venv/bin/python -m pipelines.ingest.cpc_merged_ir --start 2026-05-14T00:00 --end 2026-05-14T23:00`. Configuration is in `config/`. Results and claims: [docs/FINAL_RESULTS.md](docs/FINAL_RESULTS.md), [docs/FINAL_CLAIMS.md](docs/FINAL_CLAIMS.md); phase reports: FIRST_EVENT, BASELINE_EVAL, TRACKING_AUDIT, MULTI_EVENT, DECAY_AWARE, ML_PROTOTYPE in `docs/`; full report: [docs/FINAL_TECHNICAL_REPORT.md](docs/FINAL_TECHNICAL_REPORT.md).

## Data and evidence
- `docs/FREEZE_ml-v0.json` records SHA-256 hashes of the 386 frozen files; `tests/test_phase7_freeze.py` fails if any changes.
- Large data is **not stored in git**: `data/raw/` (~16 GB; re-downloadable, URLs + SHA-256 in `data/raw/cpc_merged_ir/manifest.json`), `data/interim/` (~0.6 GB), `data/processed/` (~1 GB). The freeze test and bundle rebuild need these locally; publish them via Git LFS or a release/external archive (maintainer decision pending).
- `data/models/ml-v0/` and `data/figures/` are small and committed.

## Limitations
3 held-out days only; May 2026, NW India only; test is backward in time (no forward-in-time test); 30-min cadence and a single IR channel; no radar/lightning truth; parallax not corrected; ML shows no yes/no gain over pySTEPS beyond 1 h; no hail/lightning/rain skill; replay only (latency not modelled). Full list: [docs/FINAL_CLAIMS.md](docs/FINAL_CLAIMS.md).

## Project structure
```
apps/web/     React + TypeScript + Vite + MapLibre dashboard, unit and e2e tests, replay bundles
ml/           features, forecasting baselines, tracking, verification
pipelines/    ingest, preprocess, replay bundle builder
scripts/      experiment, figure and freeze scripts
config/       YAML configuration
tests/        Python tests (phases 1–8, freeze guard)
docs/         specs, phase reports, final results/claims, technical report, ppt/ (final PPT + PDF, build script)
data/         provenance, figures, model (large data git-ignored)
```
Final submission deck: [docs/ppt/FINAL_SIH26084_PRESENTATION.pptx](docs/ppt/FINAL_SIH26084_PRESENTATION.pptx) / [.pdf](docs/ppt/FINAL_SIH26084_PRESENTATION.pdf).
# SIH---26084
