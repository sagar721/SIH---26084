# Phase 4 — Multi-Event Validation of the Grid Baselines

**Status:** Phase 4 complete.

**Question:** do the Phase-2 findings on 14 May (E8) hold on other real days? The Phase-2 findings were: pySTEPS advection beats persistence on CSI/FSS, useful skill lasts only ~1.5–2 h, and advection's frequency bias grows with lead.

**Protocol:** the Phase 1–3 pipeline runs unchanged on each event.
- `config/baseline.yaml` is unchanged; its SHA-256 is identical in every event's provenance.
- No per-event tuning; nothing fitted.
- Grid metrics are primary; object metrics are diagnostic.

---

## 1. Events

**Selection rule** (fixed before any scoring; recorded in `config/events.yaml`):
- the date is printed in the archived IMD RMC New Delhi hail report (sha `face5916…`);
- all 24 hourly NOAA CPC merged-IR files exist on the approved archive;
- at least 2 reported places geocode inside the frozen domain;
- the date is not within ±1 day of another selected event (VALIDATION_PLAN §3).

Candidates were ranked by the number of reported places.

**Suitability rule** (also fixed before scoring, in `scripts/run_multi_event.py`):
- all 48 frames are present;
- BT < 235 K occurs in the domain in ≥ 50 % of frames, so CSI is defined for most issue times.

| Event | Date | Reported places (in domain) | Outcome |
|---|---|---|---|
| E8 | 14 May 2026 | 16 (15) | Phase-1 reference |
| E8a | 1 May 2026 | 20 (17) | **Excluded by the suitability rule.** BT < 235 K in only 21 % of frames; mean deep area 0.014 % of the domain; no deep cell within 50 km of any station. Reported hail was largely in hills (HP/UK) and western UP. On this source the storms stayed warmer than 235 K. Its outputs are kept but not used. |
| E10 | 4 May 2026 | 10 (10) | **Used** |
| E11 | 16 May 2026 | 5 (3) | **Used** (weak event: base rate 0.4 %) |
| E9 | 5 Apr & 9 Apr 2026 | — | **Unavailable.** The archive has no April 2026 files (HTTP 404; the listing has 30–31 Mar, then 1 May onward). |
| E9 | 21 Mar 2026 | — | Unavailable (before 30 Mar) |

**No further candidate qualifies:**
- 13 May, 15 May, 2 May, 3 May and 5 May are each within ±1 day of a selected event.
- 6 May has 1 in-domain place (Moth/Jhansi is south of 26° N).
- 7 May has 1 place.
- The PDF ends on 16 May.

## 2. Reproduce

```bash
.venv/bin/python -m pipelines.ingest.cpc_merged_ir --start 2026-05-04T00:00 --end 2026-05-04T23:00   # per event
bash scripts/run_event_pipeline.sh E10_20260504        # unchanged Phase 1-3 pipeline (cube, tracks, baselines, v2, audit)
.venv/bin/python -m scripts.run_multi_event             # cross-event tables -> data/processed/multi_event/
.venv/bin/python -m scripts.make_multi_event_figures    # figs 11-13
.venv/bin/python -m pytest -q                           # 46 tests (45 pass, 1 skipped: E8a unused)
```

**Determinism:** a rerun of `run_multi_event` and of the 16-May baseline gave byte-identical CSVs.

## 3. Pipeline changes needed to run the new events (neither changes E8)

1. **trackpy solver cap** (`config/tracking.yaml: subnetwork_size_max: 50`, passed to tobac `subnetwork_size`).
   - On 1 May a linking subnetwork had 34 candidate points, above trackpy's default of 30, and linking aborted.
   - This is a computational limit of trackpy's exact solver, not a meteorological threshold. It applies to all events.
   - Re-running E8 tracking with it gave byte-identical `features.parquet`, `mask.nc` and `merge_split.json`.
2. **`shifted_iou` off-grid shift** (`ml/forecasting/baselines.py`).
   - On 4 May a long-lead constant-velocity forecast shifted a cell by more than the grid size, and the slice assignment crashed.
   - The function now returns IoU 0, or NaN if both masks are empty.
   - Any such shift previously raised, so no earlier output can have been computed through this path. Test added.

## 4. Grid metrics per event (BT < 235 K; `event_metrics_by_lead.csv`)

| Lead (min) | CSI P / A: E8 14 May | CSI P / A: E10 4 May | CSI P / A: E11 16 May | Bias P / A: E8 | Bias P / A: E10 | Bias P / A: E11 |
|---|---|---|---|---|---|---|
| 30 | 0.509 / **0.593** | 0.514 / **0.582** | 0.492 / **0.589** | 1.04 / 1.16 | 1.08 / 1.11 | 1.02 / 1.13 |
| 60 | 0.352 / **0.428** | 0.336 / **0.428** | 0.341 / **0.441** | 1.05 / 1.28 | 1.13 / 1.18 | 1.01 / 1.23 |
| 120 | 0.191 / **0.245** | 0.169 / **0.263** | 0.160 / **0.283** | 1.03 / 1.44 | 1.11 / 1.21 | 0.85 / 1.40 |
| 180 | 0.106 / **0.156** | 0.089 / **0.178** | 0.025 / **0.213** | 1.01 / 1.60 | 1.04 / 1.15 | 0.56 / 1.56 |
| 240 | 0.077 / **0.109** | 0.043 / **0.130** | 0.001 / **0.110** | 0.94 / 1.71 | 0.98 / 1.07 | 0.41 / 1.68 |
| 360 | 0.038 / 0.043 | 0.019 / 0.054 | 0.000 / 0.002 | 0.82 / 2.61 | 0.91 / 0.97 | 0.80 / 1.53 |

P = persistence; A = pySTEPS advection.

**Event context:**

| | E8 | E10 | E11 |
|---|---|---|---|
| Base rate (scored pixels, 30-min lead) | 2.7 % | 4.2 % | 0.4 % |
| Unscorable fraction, 30 → 360 min | 9 → 35 % | 12 → 35 % | 4 → 17 % |
| QC-fail frames | 6 | 9 | 0 |

### Within-event uncertainty (`event_block_bootstrap.csv`)

Method: circular block bootstrap over issue times, 6-h blocks (= the longest lead), 1000 resamples, seed 20260925. H/M/F counts are re-pooled on each resample.

95 % CI of CSI(A) − CSI(P):

| Lead | E8 | E10 | E11 |
|---|---|---|---|
| 30 | 0.083 [0.072, 0.112] | 0.068 [0.056, 0.077] | 0.098 [0.045, 0.125] |
| 60 | 0.076 [0.044, 0.087] | 0.092 [0.069, 0.102] | 0.100 [−0.026, 0.148] |
| 120 | 0.054 [0.003, 0.069] | 0.094 [0.066, 0.108] | 0.123 [−0.011, 0.205] |
| 180 | 0.051 [0.016, 0.059] | 0.088 [0.051, 0.112] | 0.188 [−0.020, 0.277] |
| 360 | 0.005 [−0.015, 0.031] | 0.035 [0.001, 0.066] | 0.002 [0.000, 0.005] |

**Reading:**
- The interval excludes 0 at 30–240 min for E8 and at 30–360 min for E10.
- For E11 it excludes 0 only at 30 min. It is a small event (8–80 cold pixels per frame at long leads), so its intervals are wide.
- The block length is a judgement (NEEDS VERIFICATION). These intervals describe variability within one day; they are not independence across events.

## 5. Cross-event comparison (`cross_event_by_lead.csv`, `decay_by_event.csv`)

### Skill

- **Sign:** advection beats persistence on CSI **and** FSS 40 km at **every lead, in all 3 events**.
  - A sign test on 3 events cannot reach p < 0.05; the best possible is p = 0.125, one-sided.
  - This is consistency, not significance.
- **Pooled CSI (summed contingency, 3 events), P → A:**
  - 30 min: 0.511 → 0.586
  - 60 min: 0.342 → 0.429
  - 120 min: 0.176 → 0.258
  - 180 min: 0.092 → 0.172
  - 360 min: 0.022 → 0.049
- **Event-day bootstrap of the pooled difference** (VALIDATION_PLAN §5): 30 min [0.068, 0.098]; 120 min [0.054, 0.123].
  - With 3 events there are only 10 distinct resamples, so this is **indicative only**.

### Decay

| | E8 | E10 | E11 |
|---|---|---|---|
| Useful FSS 40 km (≥ 0.5 + f0/2), P / A | to 90 / **120** min | to 90 / **120** min | to 90 / **120** min |
| Useful FSS 20 km, P / A | to 60 / 90 min | to 60 / 90 min | to 60 / 120 min |
| CSI e-folding time (30–180 min fit), P / A | 96 / 113 min | 87 / 128 min | 54 / 149 min |

- The 30-min CSI is nearly identical across events: 0.49–0.51 for P, 0.58–0.59 for A.
- The Phase-2 finding that **useful skill ends by ~2 h and neither method is useful at 6 h** generalises to all 3 events.
- Persistence decays fastest on the weakest event (E11). Its small cells dissipate within ~3 h, while advection keeps some overlap.

### Frequency bias

- Advection's bias rises with lead in every event. The size of the rise is event-dependent:
  - E8: 1.16 → 2.61
  - E11: 1.13 → 1.78 at 300 min
  - E10: 1.11 → 1.21, then back to ~1.0
- Persistence bias stays near 1 for E8/E10. On E11 it falls to 0.4 at 240 min, because the cold area shrinks there over the day.
- The Phase-2 bias growth is therefore **not universal in size**. Its decomposition (no-decay vs inflow exclusion vs diurnal cycle) is still not done.

## 6. Object metrics — DIAGNOSTIC ONLY (`object_diagnostics_by_event.csv`)

Tracks are Phase-3 v2. "Paired" = the fraction of (cell, issue) pairs where field advection's centroid error is below persistence's.

| Lead | E8 | E10 | E11 |
|---|---|---|---|
| 30 | 0.59 (43 cells) | 0.62 (66) | 0.57 (18) |
| 60 | 0.60 (28) | 0.69 (42) | 0.42 (15) |
| 120 | 0.50 (14) | 0.65 (26) | 0.72 (4) |

- Under v2-flow truth the fraction is 0.55–0.87 in all events. That definition is partly circular.
- The 60-min advantage seen on E8 **does not hold on E11** (0.42, 15 cells). The object claim is therefore limited to **30 min, consistent across 3 events**.

**Tracking audit on the new events** (`audit/`):
- The v1 (tobac) problems recur. Direction reversals are 0.46 / 0.46 (E10 / E11), and ID-switch candidates are 0.23 / 0.09.
- v2 reduces reversals to 0.33 / 0.21, ID switches to 0.00 / 0.00, and area jumps to 0.28 / 0.24.

## 7. Event-specific data / QC limitations

| Event | Limitation |
|---|---|
| E8 | 6 QC-fail frames (kept, flagged); max raw missing 6.1 %. Phase-1 notes apply. |
| E10 | **9 QC-fail frames, 17:00–21:30 UTC**; max raw missing 7.1 %; 4.1 % of in-domain pixels gap-filled on average. The evening issue times score on fewer pixels. |
| E11 | 0 QC-fail frames. **Small deep-convection sample**: base rate 0.4 %, 36 v2 cells, 10 ≥ 2 h. Wide CIs. Pahalgam (34.03° N) lies just outside the domain; tracks within 50 km were still found. |
| E8a | Excluded (§1). Its numbers exist in `data/processed/E8a_20260501/baseline/` but are **not** in any cross-event number. |
| All | Hail reports are context only; place-to-state assignment follows PDF text order (column layout lost). Geocoding failures: Jubbarhatti, Hindon AFS (E8a); Tungnath (E11). |

## 8. Outputs (`data/processed/multi_event/`)

| File | Content |
|---|---|
| `event_qc.csv` | Frames, QC fails, missing/gap-filled fractions, deep-convection presence, suitability |
| `event_metrics_by_lead.csv` | Per event × method × lead: contingency, POD/FAR/CSI/bias, FSS 10/20/40 km, useful thresholds, excluded fraction |
| `event_block_bootstrap.csv` | Within-event 95 % intervals for CSI per method, the CSI difference and bias |
| `cross_event_by_lead.csv` | Pooled CSI/bias, event min/max, event-mean FSS 40 km, sign counts, event-day bootstrap |
| `decay_by_event.csv` | Useful-FSS lead, CSI half-life, e-folding time |
| `object_diagnostics_by_event.csv` | v2 paired object comparison per event (diagnostic) |
| `multi_event_provenance.json` | Config hashes, bootstrap settings, input and output SHA-256 |

**Figures:**
- `data/figures/multi_event_fig11_skill_by_event.png`
- `…fig12_csi_difference_ci.png`
- `…fig13_scorability_base_rate.png`
- Per-event fig1–10 for E10/E11 (and E8a) under `data/figures/<event>_*`

## 9. NEEDS VERIFICATION

1. **Three events from one season and one region** (May 2026, NW India, IMD NW-India hail report). Nothing is shown for monsoon, cloudburst or other regions. The event-day bootstrap has only 10 distinct resamples.
2. **Block length.** The within-event 6-h block length is a judgement; there was no sensitivity study.
3. **Suitability rule.** It removed 1 May, whose hail produced few cloud tops < 235 K on this 4 km source. The 235 K definition may miss hill hailstorms. That is a limitation of the event definition, and it was **not** changed.
4. **Advection bias growth.** Its event-to-event variation is not decomposed.
5. **Object diagnostics** remain unvalidated against independent truth (Phase-3 NEEDS VERIFICATION items stand).
6. **Carried over:** parallax, satellite-ID code, 30-min cadence, pySTEPS local build, place geocoding / PDF column layout.
