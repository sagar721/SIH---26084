# Final SIH Submission PPT — SIH26084 (10 slides)

**Evidence rule:** every number below is a frozen, verified result.
- The source for each is given, and all are traceable to [`FINAL_CLAIMS.md`](FINAL_CLAIMS.md) / [`FINAL_RESULTS.md`](FINAL_RESULTS.md) (hashes in [`FREEZE_ml-v0.json`](FREEZE_ml-v0.json)).
- No number may be added or rounded differently without checking that source.

**Format:**
- Build the deck inside the official **SIH 2026 Idea PPT template** (`SIH2026-IDEA-Presentation-Format.pptx`; see [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md)).
- The 10 slides below map onto its sections.

**Visual rule:**
- One large real image per slide, with ≤ 5 short lines of text.
- Prototype screenshots come from the verified E8 browser run:
  - `apps/web/e2e-shots/verify/`: with basemap, 1440×900;
  - `apps/web/e2e-shots/`: basemap off.

**Placeholders to fill:** `[TEAM NAME]`, `[TEAM ID]`, `[COLLEGE]`, `[TEAM LEADER]`.

---

## Slide 1 — Title

**Title:** StormLife Nowcast: satellite-first nowcasting of deep convection for India

**Slide text:**
- PS **SIH26084** · MoES / NCMRWF · *Convective scale nowcasting for Thunderstorms, Hail & Cloudbursts (0–6 hr)*
- Team **[TEAM NAME]** · **[COLLEGE]** · Team ID **[TEAM ID]**
- *Real satellite data. Held-out storm days. Every number reproducible.*
- Footer: Research prototype — not an official IMD warning

**Visual:** `apps/web/e2e-shots/verify/1_situation_basemap.png` as the hero image. It shows the real 14 May 2026 IR frame with tracked cells.

**Speaker note:** "We forecast where deep convective clouds will be over the next hours, from satellite alone, and we show how far each forecast can be trusted."

---

## Slide 2 — Problem

**Title:** Storms grow in minutes, and India has no open radar or lightning feed to learn from

**Slide text:**
- Thunderstorms, hail and cloudbursts build and move within 0–6 hours.
- IMD's radar-based nowcasts cover radar cities. Raw radar data needs a licence, and the AWS/ARG portal was closed to the public in May 2025.
- Geostationary satellites see all of India every 30 min, but only cloud tops.
- **The question:** where will cloud tops be colder than 235 K (deep convection) 30 min–6 h ahead, and how much should a forecaster trust that forecast?

**Visual:** `data/figures/E8_20260514_fig1_satellite_frame.png` (real IR frame, 14 May 2026, NW-India multi-station hail day).

**Verified facts** (research report Part 6, VERIFIED):
- IMD DWR raw data needs a licence or research request.
- IMD AWS/ARG portal locked in May 2025.

**Speaker note:**
- The PS lists many hazards. We scoped to the one target we can verify on real data: deep convection (BT < 235 K).
- Hail, lightning and rain need independent truth that is not openly available, so we make no claims for them.

---

## Slide 3 — Solution

**Title:** One pipeline from raw satellite frames to a verified, replayable forecast

**Slide text:**
- **Input:** NOAA/NCEP/CPC merged IR (4 km, 30 min) → quality control → common 2 km grid.
- **Storm cells:** detected and tracked (tobac + audited overlap tracking), with phase, motion and history.
- **Forecasts, 30 min–6 h:** persistence, pySTEPS motion extrapolation, and a **calibrated ML probability** of deep convection.
- **Verification** on held-out storm days, on identical pixels for every method.
- **Web prototype:** situation map, cell cards, 0–6 h forecast, replay (*knew / predicted / happened*), evidence, data health, and exercise alerts.

**Visual:** `apps/web/e2e-shots/verify/4_forecast_ml_threshold05.png` (ML probability, T+2h, E8), or a 3-panel strip: 1_situation → 2_cell_by_map_click → 4_forecast_ml.

**Speaker note:** "Everything you will see in the demo is replayed from these saved, verified outputs. Nothing is simulated."

---

## Slide 4 — Innovation / differentiation

**Title:** What is new here: honesty you can check

**Slide text:**
- **Real Indian storm days only:** no simulated radar, lightning or synthetic metrics.
- **Baseline-first:** every model is scored against persistence and pySTEPS on the same pixels. Negative results are reported, not hidden.
- **Diagnosis, not just scores:** an exact split of forecast bias shows *why* skill is lost after ~2 h.
- **Audited tracking** before any cell-level use: ID switches cut from 21 % to 0.4 %.
- **Evidence freeze:** 386 files are hash-locked, and a test fails if any number changes.

**Visual:** two small panels:
- `data/figures/phase6_fig19_reliability.png` (calibration);
- `data/figures/E8_20260514_fig8_tracking_audit.png` (tracking audit).

**Verified metrics:**

| Result | Value | Source |
|---|---|---|
| Tracking audit: ID-switch candidates | 0.206 → 0.004 | `audit_v1.json` vs `audit_v2_none.json` |
| Tracking audit: zero-overlap links | 0.057 → 0 | same |
| Freeze | 386 files, test suite green | `FREEZE_ml-v0.json` |

**Speaker note:**
- Storm-lifecycle tracking already exists operationally (NWCSAF RDT, MeteoSwiss TRT, NOAA ProbSevere). We do not claim the concept is new.
- Our contribution for SIH26084 is a verified, reproducible, satellite-only version on Indian storm days, with its limits stated.

---

## Slide 5 — Architecture

**Title:** Architecture: built today vs planned

**Slide text** (draw as a left-to-right flow):
- **BUILT:**
  1. NOAA CPC merged IR ingest (SHA-256 manifest)
  2. QC + gap-fill + 2 km LAEA grid
  3. tobac detection + v2 overlap tracking
  4. pySTEPS Lucas–Kanade + semi-Lagrangian
  5. ML: gradient boosting + isotonic calibration
  6. Verification: CSI, FSS, BSS, reliability, block bootstrap
  7. Evidence freeze
  8. Replay-bundle builder
  9. Static React + MapLibre web app
- **PLANNED** (greyed): Meteosat-9 IODC / INSAT-3DS multi-channel 15-min input · live mode (FastAPI + PostGIS) · radar/lightning adapters when access exists.
- **Open-source, permissive stack:** pySTEPS (BSD-3), tobac (BSD-3), scikit-learn (BSD-3), MapLibre (BSD-3), React (MIT).

**Visual:** a flow diagram drawn in the PPT, built boxes solid and planned boxes dashed/grey. Skeleton:

```
NOAA CPC IR ──► QC + 2 km grid ──► cells (tobac + v2) ──► pySTEPS ──► ML (GBDT + isotonic)
                                                                      │
                     replay bundles ◄── evidence freeze ◄── verification (held-out days)
                          │
                     web prototype (9 screens)
[planned, dashed] Meteosat-9 / INSAT-3DS · FastAPI + PostGIS live · radar / lightning
```

**Speaker note:**
- The prototype runs from static, hash-checked files, with no server. That made the demo reliable.
- A live mode is designed but not built.

---

## Slide 6 — Data + methodology

**Title:** Data and method: real days, a rule fixed before scoring, strict time splits

**Slide text:**
- **Satellite:** NOAA/NCEP/CPC merged IR, single ~11 µm channel, 4 km, 30 min. **Domain:** NW India, 26–34° N, 72–84° E.
- **Held-out test days:** 14 May, 4 May, 16 May 2026 (IMD RMC New Delhi hail-report days, selected by a rule fixed before scoring). 1 May was excluded by a pre-declared rule; April 2026 is missing from the archive.
- **Target:** cloud top < 235 K per 2 km pixel, 30 min–6 h ahead.
- **Splits by calendar day:** train 18–31 May (14 days, 7 convective), validate 6–12 May, test the 3 event days, with a ±1-day buffer around every event.
- **Scores:** CSI, FSS (40 km), Brier skill score, reliability. Features use only data up to the issue time (tested).

**Visual:** `data/figures/E8_20260514_fig2_detected_cells.png`, plus a simple split timeline drawn in the PPT:

```
May 2026:  1 | 4 | 6 … 12 | 14 | 16 | 18 … 31
          ex |TEST| VALID | TEST|TEST|  TRAIN
```

**Verified:**
- Training rows: 1,467,318; validation rows: 856,830 (`model_card.json`).
- 7 of 14 training days convective (sufficiency gate minimum).

**Speaker note:** "The archive starts on 1 May, so training days come after the test days. It is a day-separated test, but backward in time. We say so on the limitations slide."

---

## Slide 7 — ML + baseline results

**Title:** Results on 3 held-out storm days: pySTEPS beats persistence; ML gives the best probabilities to ~4 h

**Slide text:**
- pySTEPS beats persistence at **every lead on 3 of 3 days**. Useful skill lasts **~90 min (persistence) and ~120 min (pySTEPS)**.
- ML has the best **probability skill** up to ~4 h, and its probabilities are **well calibrated** (calibration error 0.002–0.004).
- As a **yes/no** forecast (p ≥ 0.5), ML is no better than pySTEPS beyond 1 h.
- Why skill fades: on 14 May at 6 h, pySTEPS bias is 2.61 on the scored area but 0.70 over the whole domain. New storms enter from the unforecastable edge.

**Visual:** `data/figures/phase6_fig17_skill_vs_lead.png` (CSI, FSS, BSS and bias vs lead for all methods), or the table below built in the PPT.

**Verified table** (BSS vs training climatology; `metrics_pooled_lead.csv`, mask V):

| Lead | Persistence | pySTEPS | Neighbourhood pySTEPS | **ML** |
|---|---|---|---|---|
| 30 min | 0.32 | 0.44 | 0.63 | **0.67** |
| 1 h | −0.04 | 0.10 | 0.41 | **0.51** |
| 2 h | −0.47 | −0.38 | 0.02 | **0.27** |
| 3 h | −0.69 | −0.67 | −0.23 | **0.13** |
| 6 h | −0.84 | −1.11 | −0.59 | −0.03 |

**Also verified (safe to quote):**
- CSI, persistence → pySTEPS (pooled): 0.511 → 0.586 at 30 min; 0.176 → 0.258 at 2 h.
- CSI at p ≥ 0.5, ML vs pySTEPS: 0.583 vs 0.586 (30 min), 0.452 vs 0.429 (1 h), 0.243 vs 0.258 (2 h).
- Per event: ML's gain over neighbourhood pySTEPS has 95 % intervals above 0 on 14 May and 4 May; not significant on 16 May.

**Speaker note:**
- "0 means no better than climatology. At 6 h nobody has skill, including us."
- "The ML advantage is in probability skill, not in yes/no maps beyond an hour."
- **Do not say:** "ML beats pySTEPS", "6-hour skill", or "significant across events" (3 days cannot give that).

---

## Slide 8 — Working prototype + replay

**Title:** Working prototype: replay a real storm day as a forecaster would have seen it

**Slide text:**
- **14 May 2026, 14:00 UTC:** 9 active storm cells; cell #108 selected (developing, min cloud top 216.1 K), with track and ML probability by lead.
- **0–6 h forecast:** ML probability at T+2h shown with its **validated skill (BSS 0.27)** and the yes/no caveat.
- **Replay:** three synced maps. *What the system knew · What it predicted · What actually happened.*
- Evidence and data-health screens: model comparison, calibration, 6 QC-flagged frames, source status.
- Runs locally from hash-checked files. Tested end-to-end in a real browser.

**Visual:** a 3-screenshot collage:
- `apps/web/e2e-shots/verify/2_cell_by_map_click.png`
- `apps/web/e2e-shots/verify/5_replay.png`
- `apps/web/e2e-shots/verify/6_performance.png`

**Verified on screen** (browser run):
- 9 cells at 14:00 UTC.
- Cell #108: Developing, min BT 216.1 K.
- ML T+2h ribbon: CSI 0.243 · BSS 0.27 · FSS40 0.53.
- 6 QC-fail frames (10:00–12:30 UTC).
- CAP download `status=Exercise`.

**Speaker note:** "Everything is labelled: REPLAY, PROBABILITY, rules v0 PROPOSED. The alert panel only drafts exercise advisories; nothing is issued without a forecaster's approval."

---

## Slide 9 — Impact / use cases

**Title:** Who could use it, and how

**Slide text:**
- **IMD / NCMRWF forecasters:** a satellite-only probability map of deep convection for areas without radar, with its validated skill shown beside it.
- **District disaster officials:** place-level draft advisories to review and approve (CAP 1.2, exercise mode). Never auto-issued.
- **Researchers / evaluators:** a reusable, reproducible test bed. Any new model is scored against the same baselines, on the same pixels and the same held-out days.
- **Scales with the satellite:** geostationary imagery covers all of India every 30 min.

**Visual:** `apps/web/e2e-shots/9_alerts.png` (Alert Center: Shopian draft at 08:00 UTC, CAP preview, Exercise badge), next to `apps/web/e2e-shots/verify/1_situation_basemap.png`.

**Speaker note:**
- These are intended uses of a research prototype. Alert usefulness has **not** been verified, and no operational value is claimed.
- The advisory rule (ML P ≥ 0.5 within 10 km) is a display rule on frozen probabilities.

---

## Slide 10 — Limitations + future scope

**Title:** Limits we state up front, and the next steps

**Slide text:**
- **Limits:**
  - only 3 held-out storm days (May 2026, NW India);
  - trained on later days (backward-in-time test);
  - thin training data (7 convective days);
  - 30-min cadence;
  - one IR channel;
  - no radar or lightning validation;
  - replay only, no live feed.
- **Not claimed:** yes/no ML gain beyond 1 h · 6-h skill · hail, lightning or rain forecasts · storm-initiation prediction.
- **Next:**
  1. forward-in-time test on new storm days;
  2. INSAT-3DS / Meteosat-9 multi-channel 15-min input;
  3. radar and lightning truth where access allows;
  4. a storm-initiation score;
  5. live mode with a latency model.

**Visual:** `data/figures/phase5_fig14_bias_decomposition.png` (small), or no image, just a clean two-column layout (Limits | Next).

**Verified:** list taken from `FINAL_CLAIMS.md` §C–§D.

**Speaker note:** "We would rather show you a smaller result that is true than a bigger one we cannot defend."

---

## Numbers audit (for the team before submitting)

| Number on slides | Source file (frozen) |
|---|---|
| BSS 0.67 / 0.51 / 0.27 / 0.13 / −0.03 (ML) and baselines | `data/processed/ml_eval/ml-v0/metrics_pooled_lead.csv` |
| CSI 0.511 → 0.586, 0.176 → 0.258; 3 of 3 days | `data/processed/multi_event/cross_event_by_lead.csv` |
| Useful skill 90 / 120 min | `data/processed/multi_event/decay_by_event.csv` |
| Calibration error 0.0022 / 0.0034 / 0.0042 / 0.0026 | `data/processed/ml_eval/ml-v0/reliability.csv` (FINAL_CLAIMS A7) |
| Bias 2.61 vs 0.70 (E8, 6 h) | `data/processed/multi_event/phase5/decomposition_by_lead.csv` |
| ID switches 0.206 → 0.004 | `data/processed/E8_20260514/audit/audit_v*.json` |
| Per-event intervals (E8, E10 above 0; E11 not) | `data/processed/ml_eval/ml-v0/bootstrap_ml_vs_pysteps.csv` |
| 1,467,318 / 856,830 rows; 7 of 14 convective days | `data/models/ml-v0/model_card.json` |
| 386 frozen files | `docs/FREEZE_ml-v0.json` |
| 9 cells, #108 216.1 K, ribbon values, 6 QC-fail frames | E8 bundle (`apps/web/public/bundles/E8_20260514/`), verified in the browser run |
