# Phase 8 — Product Prototype (Replay Demo)

**What it is:** a static web prototype ("StormLife Nowcast") that replays the **frozen** Phase 1–7 evidence for real held-out event days. The main demo is **E8 · 14 May 2026**.

**What it is not:**
- Not live: it is REPLAY only, product latency is not modelled, and there is no MOSDAC/EUMETSAT feed.
- Not an official warning: alerts are CAP `status=Exercise` with a disclaimer.
- Not a new model or experiment: every number and field comes from files hashed in [`FREEZE_ml-v0.json`](FREEZE_ml-v0.json).

## Run

```bash
# 1. build the replay bundles from frozen outputs (each input is hash-checked against the freeze manifest)
.venv/bin/python -m pipelines.replay.build_bundle --event E8_20260514 E10_20260504 E11_20260516

# 2. web app (Node >= 18)
cd apps/web
npm install
npm run build            # type-check + production build -> apps/web/dist
npm run preview          # http://localhost:4173   (or: npm run dev)

# tests
npm test                 # unit tests (colour scales, decoding, CAP, formatting)
npx playwright install chromium && npm run e2e   # end-to-end demo flow on the production build
cd ../.. && .venv/bin/python -m pytest -q        # Python suite incl. bundle tests and the Phase-7 freeze guard
```

**Offline use:**
- The basemap uses online Esri World Light Gray Canvas tiles (no API key; CARTO tiles now require a key and were replaced). Switch it off in the sidebar for an offline demo; all data layers are local.
- Fonts fall back to system fonts when offline.

## Architecture (no backend)

`pipelines/replay/build_bundle.py` reads frozen outputs and writes `apps/web/public/bundles/<event>/` (REPLAY_SPEC §4):

| File(s) | Content |
|---|---|
| `obs/`, `fc/` | 8-bit data tiles on a Web-Mercator display grid: observed BT, pySTEPS BT, ML probability; colourised in the browser |
| `cells/`, `contours/` | GeoJSON: v2 cell polygons, observed < 235 K outlines |
| `tracks.json`, `cellfc/` | Tracks, and the frozen pySTEPS-advected cell positions |
| `scores.json`, `skill.json` | Frozen per-issue and pooled held-out metrics |
| `health.json` | QC per frame, sources, model card, limitations |
| `alerts.json` | Draft advisories |
| `manifest.json` | Input hashes (checked against the freeze) and output hashes |

The React + TypeScript + Vite + MapLibre app (`apps/web/`) loads these static files. It does not compute any metric; charts and tables display frozen numbers only.

## Screens

| # | Screen | What it shows |
|---|---|---|
| 1 | **Event selection** | Preset cards E1–E11 with honest availability (BUNDLED / EXCLUDED / NOT AVAILABLE + reason) |
| 2 | **Situation** | IR map, phase-styled cells, pySTEPS motion arrows, IMD-report places coloured by max ML P in the next 60 min; KPIs; top-5 cells by ML risk; source status |
| 3 | **Storm Cells** | Selected cell: past track (history to now), pySTEPS-advected track to +6 h. Cell card: phase (rules v0, PROPOSED), min BT, ΔBT, area, cold core, age, merges/splits, motion, sparklines. **ML probability near the forecast cell position** by lead. Sortable cell table. |
| 4 | **0–6 h Forecast** | Persistence / pySTEPS / ML probability at T+30 m…T+6 h. Probability threshold, optional observed outcome (replay), skill ribbon from the frozen pooled metrics, envelope, and this issue's frozen scores |
| 5 | **Alert Center** | System status; draft advisories (rule: ML P ≥ 0.5 within 10 km at +30/+60 min); approve/reject; CAP 1.2 preview/download (`status=Exercise`); audit log |
| 6 | **Historical Replay** | Three synced panes: WHAT THE SYSTEM KNEW · WHAT IT PREDICTED · WHAT ACTUALLY HAPPENED. Baseline toggle (B), lead selector, data-availability row, per-issue scorecard, would-have-issued drafts |
| 7 | **Confidence** | Reliability diagrams + ECE per lead bin (ML vs neighbourhood pySTEPS); per-event bootstrap intervals |
| 8 | **Model Performance** | Persistence vs pySTEPS vs neighbourhood pySTEPS vs ML: BSS and CSI vs lead (pooled or per event), final comparison table, Phase-4 baseline consistency, Phase-5 bias decomposition, claim guard |
| 9 | **Data Health** | Source status, per-frame QC strip + raw-file SHA-256, unscorable fraction by lead, model card and hashes, limitations, bundle input hashes |

App-wide:
- **Top bar:** REPLAY badge, valid time UTC/IST, data tier, model version, frame QC.
- **Timeline:** 48 frames with QC-fail marks, play 1×/2×/5×, lead selector.
- **Keyboard:** ←/→, Space, 1–9, B.
- **Footer:** disclaimer.

## Demo script (≈ 5 min)

1. **Event selection** → click **E8 · 14 May 2026** (held-out; never used in training).
2. **Situation** at 14:00 UTC. Nine cold cells, and Amritsar flagged by the ML probability. Point out the REPLAY badge and the source statuses: radar and lightning unavailable.
3. Click cell **#108** (top of the risk list) → **Storm Cells**. Show the phase card, history sparklines, the dashed pySTEPS track and the ML probability by lead. Note that cell position skill is only a diagnostic at 30 min.
4. **0–6 h Forecast**: switch pySTEPS → ML probability at **T+2h**. The skill ribbon shows BSS 0.27 (held-out pooled). Tick "show what happened".
5. **Historical Replay**: the three panes. Press **B** to flip the predicted pane between ML, pySTEPS and persistence, and play the timeline.
6. **Model Performance**: ML is best in probability skill (BSS) to about 4 h. The red banner says ML does not beat pySTEPS as a yes/no forecast beyond 1 h.
7. **Confidence / Data Health**: the reliability diagram, the six QC-fail frames at 10:00–12:30 UTC, and the limitations list.
8. **Alert Center** at 08:00 UTC: approve the Shopian draft and preview the CAP (`status=Exercise`).

## Honest-labelling rules implemented

- Probability layers carry a PROBABILITY badge and the text "calibrated probability, not a guaranteed outcome".
- The skill ribbon de-emphasises leads beyond validated skill:
  - baselines: useful FSS 40 km on every event;
  - ML: pooled BSS > 0, with a "small" warning when BSS < 0.1.
- The yes/no caveat (FINAL_CLAIMS B1) appears on the ribbon, the Model Performance banner and the cell ML chart.
- Phase labels show "rules v0 · PROPOSED". The object track shows "verified only as a diagnostic at 30 min".
- Cell age, history and merges are shown only up to the current frame. The one offline exception (single-frame stubs dropped using the next frame) is stated on screen.
- ML probability tiles cover domain pixels with a valid verifying observation (the frozen evaluation mask); gaps show as no data.

## Known limitations of the prototype

- **Replay only:** NOAA CPC product latency is not modelled.
- **Basemap provider terms** (Esri) for a public deployment, and whether its boundary depiction is acceptable for an Indian government review: NEEDS VERIFICATION (decision D6). The basemap can be switched off.
- **No district choropleth, hazard map or explainability (SHAP) screens:** out of the Phase-8 scope.
- **Draft-advisory rule** (p ≥ 0.5 within 10 km) is a display rule on frozen probabilities. **Alert skill is not verified.**
- **Bundle size:** 82 MB for 3 events; the production build copies it (dist ≈ 91 MB).
