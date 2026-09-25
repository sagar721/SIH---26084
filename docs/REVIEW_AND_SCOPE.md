# Review & Scope Freeze — SIH26084

**Status:** Phase 0 · **Date:** 25 Sep 2026 · **Primary source of truth:** [`../SIH26084_Research_Report.md`](../SIH26084_Research_Report.md)

**Tags:**
- **VERIFIED** — established in the research report, with a source
- **PROPOSED** — a design decision made here
- **NEEDS VERIFICATION** — not supported by the research files; check before relying on it

**Files reviewed:**
- `SIH26084_Research_Report.md` — 17 parts, sources, competitors, data, architectures
- `WhatsApp Image 2026-09-24 at 19.43.10 (1).jpeg` — reference UI (a flood decision-support dashboard). Used as **visual/layout reference only**.

---

## 1. What the research has already established

| # | Finding | Status |
|---|---|---|
| R1 | SIH26084 asks for 0–6 h, 1–3 km, multi-source nowcasting with CI detection, lightning density, hail probability, downburst velocity, cloudburst thresholds, and a GIS dashboard with storm-arrival countdowns. No dataset, YouTube or contact links are given. | VERIFIED (Part 1) |
| R2 | Idea deadline is **30 Sep 2026**. "4–5 teams per PS **may** be selected"; the organization may select none. Criteria: novelty, complexity, clarity, feasibility, practicability, sustainability, impact, UX, future work. | VERIFIED (Part 2) |
| R3 | 9/500 submissions on 24 Sep 2026. At least 4 public SIH26084 repos and 6+ SIH26072 repos exist. Most use simulated or foreign data, ConvLSTM/XGBoost, and accuracy-style metrics. | VERIFIED (Parts 2, 4) |
| R4 | No open live Indian radar or lightning feed exists. IMD DWR is licence-only. IMD AWS was locked in May 2025. Blitzortung's terms forbid storm-warning use. | VERIFIED (Part 6) |
| R5 | Usable data: Meteosat-9 IODC (15 min, 2017→), INSAT-3DR/3DS L1B (MOSDAC; general users 3-day latency), ERA5, IMDAA (1979–2020), GFS/ECMWF open, IMERG, GSMaP_NOW, GPM DPR, ISS-LIS (Mar 2017–Nov 2023), IMD NW-India hail report (Feb–May 2026), MOSDAC TERLS 3D DWR (May 2018). | VERIFIED (Part 6) |
| R6 | "Storm lifecycle intelligence" already exists operationally: NWCSAF RDT-CW (phases), MeteoSwiss TRT (severity rank), NOAA ProbSevere v3 (per-cell hazard ML). **It is not novel as a concept.** | VERIFIED (Part 9) |
| R7 | Differentiation must come from: real Indian events, transition forecasting, genealogy, calibration, conformal ETA, reproducible validation against baselines. | Research inference (Parts 7, 9, 14) |
| R8 | Reusable, permissive building blocks: pysteps (BSD-3), tobac (BSD-3), tathu (MIT), TINT (BSD-2), satpy (Apache-2.0), MetPy (BSD-3), xskillscore (Apache-2.0), c4dl-multi (BSD-3). GPL-3.0: LightningCast, ProbSevere v3 scripts, DiffCast, ThunderCast. **No licence (do not copy):** SmaAt-UNet, ml4convection, goes16ci, lc_br. | VERIFIED (Part 3) |
| R9 | Architecture A (satellite + tabular ML, CPU) is the floor; B (advection-informed U-Net, LightningCast transfer, TERLS radar case) is stretch; C (generative) is future work. | Research recommendation (Part 8) |

## 2. What must be preserved

1. **Tagging discipline.** Every claim in docs, UI and PPT carries its evidence status. Every number traces to one evaluation script.
2. **Satellite-first, radar- and lightning-ready framing.** Never imply live IMD DWR or lightning access.
3. **Resolution honesty.** 2 km product grid; effective IR resolution ~3–4 km (Meteosat ~4–5 km over India); VIS 1 km by day only; 1 km observed radar only in the TERLS case.
4. **Baselines are first-class.** Persistence, pySTEPS extrapolation and Mecikalski rules are scored with the same code as our model.
5. **Time-blocked splits, event-day holdouts, no pixel-random splits.**
6. **Hazard wording rules:**
   - "Probability" only for calibrated, label-verified heads (CI, lifecycle transition, lightning, heavy rain).
   - "Potential" or "Indicator" for hail, cloudburst and downburst.
7. **Research terminology:** Architecture A/B/C, gaps G1–G13, events E1–E9, cell card (§9.3), 10 screens (Part 13).
8. **The prediction envelope.** Every prediction carries issue time, valid time, model version, data status and confidence. (This is Critical Rule 9 in the task.)

## 3. What should NOT be built (from Part 15, plus UI reference translation)

- Synthetic-data training with reported metrics; random or rule-generated "AI" probabilities.
- ConvLSTM as the headline; training DGMR, NowcastNet, MetNet or diffusion as a core dependency.
- Custom NWP/WRF runs; IoT/hardware; mobile app; 13-language UI; LLM forecaster; blockchain.
- Scraped IMD radar PNGs or MOSDAC gallery JPGs as **model input** (display-only is allowed with attribution, if at all).
- Blitzortung data in any form.
- "1 km" claims from interpolation; plain accuracy on rare events.
- Kubernetes/microservices; national/global coverage.
- **From the reference UI, do not port:**
  - What-if sliders that invent weather (a "rainfall multiplier" or any hypothetical scenario generator)
  - Routing engine
  - Drainage what-ifs
  - Any "SIMULATED" mode

  Our only modes are **LIVE** and **REPLAY** (historical observed data).
- Copying any competitor repo or unlicensed research code.

## 4. Key technical risks (new items flagged beyond the report)

| # | Risk | Why it matters | Mitigation | Status |
|---|---|---|---|---|
| K1 | **Data volume.** Full-disk SEVIRI native files are large (order of 100s of MB per 15-min slot). A multi-season archive could reach TBs. | Report estimated "a few hundred GB cropped", but only if we crop at the source. | Use EUMETSAT Data Tailor (server-side crop + channel subset) or keep only event windows plus sampled storm days. **Measure the size of the first download.** | NEEDS VERIFICATION |
| K2 | **Satellite switch in the lightning training window.** ISS-LIS labels end Nov 2023. Meteosat-8 (41.5°E) was IODC until 1 Jun 2022, then Meteosat-9 (45.5°E). | Viewing-geometry and calibration shift inside the training data. | Include a `platform` feature and test per-platform, or use INSAT-3DR, which is consistent over 2017–2023. | VERIFIED facts; mitigation PROPOSED |
| K3 | **Parallax.** Cold cloud tops seen obliquely from 45.5°E (or 74°E for INSAT-3DR) are displaced from the ground position. | Biases ETA and district intersection. | satpy parallax correction (**NEEDS VERIFICATION** of API/version), or a first-order height-based correction. Report ETA error with and without it. | NEEDS VERIFICATION |
| K4 | **Split conflicts.** The report's generic test split (2025–2026) can't evaluate lightning (labels end 2023) or hail (IMD reports only 2026). | Invalid evaluation if a single split is applied to every head. | **Per-head splits** (VALIDATION_PLAN §3). | PROPOSED |
| K5 | **Event leakage.** E1 (2018) and E2 (2020) fall in training years; E3 (2024) falls in the calibration/validation year. | Replay results would look better than true skill. | Event days ±1 excluded from training *and* calibration. | PROPOSED |
| K6 | **MOSDAC "limited datasets" for general users.** | May not include INSAT L1B archives. | Check on Day 1; Meteosat-9 is the fallback primary. | NEEDS VERIFICATION |
| K7 | **tobac tuning on coarse IR.** | Over-splitting or merging of cells → noisy genealogy. | Tune on 5 labelled days; fall back to pysteps T-DaTing. | Report risk |
| K8 | **Satellite-defined "arrival".** Cold-cloud arrival ≠ rain or gust arrival. | ETA claims could be misread. | Define ETA truth explicitly; optionally validate against IMERG rain arrival. | PROPOSED |
| K9 | **GPL-3.0 components** in combination with the SIH IP-split clause. | Licensing conflict at the finale. | Isolate as an optional separate module, or skip. | Report risk |
| K10 | **Deadline (5 days).** | Missing it ends participation. | Phase 1 is only a proof slice plus the PPT. | VERIFIED |

## 5. Missing decisions (owner: team; blocking status noted)

| # | Decision | Recommended default | Blocks |
|---|---|---|---|
| D1 | Primary training satellite | **Meteosat-9/8 IODC** (known free archive). INSAT-3DR/3DS for event days, and as primary if MOSDAC access proves sufficient. | Phase 2 |
| D2 | Domain & season | **NW India + IGP (26–34°N, 72–84°E), Mar–Sep.** Mar–Sep rather than the report's Mar–Jun so the Himalayan cloudburst events E5–E7 fall inside the season. | Phase 2 |
| D3 | Storage/compute budget | ≤ 1 TB disk, 1 laptop + free Colab; subsample training days if needed | Phase 2 |
| D4 | Submit a second PS (e.g., SIH26072)? | Team call. Guidelines allow 2 PS per team; check the "idea must be new" clause with your SPOC | Phase 1 |
| D5 | Repo licence & GPL policy | Apache-2.0 for our code; GPL parts in a separate optional repo or service | Phase 5+ |
| D6 | Basemap | Neutral OSM-based vector basemap. IR brightness temperature is the "imagery" layer. Satellite basemap only if its terms allow (NEEDS VERIFICATION). | Phase 10 |
| D7 | Phase-rule thresholds sign-off | Use the report §9.2 defaults; get a meteorology mentor to review | Phase 6 |
| D8 | Owners per workstream | Data, Tracking/ML, Validation, Backend, Frontend, PPT/Demo | Now |
| D9 | Demo hosting | Offline-capable local Docker Compose. Replay bundles precomputed. | Phase 13 |
| D10 | Mentor with meteorology background | Strongly recommended. The finale allows up to 2 mentors. | Phase 1 |

## 6. Final recommended product scope (FROZEN for Phases 1–13)

**Product name (working):** Storm Lifecycle Intelligence — *satellite-first, verified on Indian events*

**In scope — Architecture A (minimum working system):**
1. Ingest Meteosat-9/8 IODC SEVIRI (+ INSAT-3DR/3DS event days), ERA5, IMERG, ISS-LIS, GPM DPR 2A, IMD hail report; GFS for live context.
2. QC → 2 km equal-area grid over the domain → IR interest fields.
3. CI detection (rules baseline + LightGBM).
4. tobac detection, segmentation, linking, merge/split → cells, tracks, genealogy.
5. Objective lifecycle phases (rule table) → **transition probabilities + remaining-life survival model**.
6. Hazard heads:
   - Lightning (ISS-LIS labels)
   - Heavy rain (IMERG)
   - Hail *potential* (DPR flags; evaluated against IMD reports)
   - Cloudburst and downburst *indicators* (case-study only)
7. Isotonic calibration; split-conformal ETA intervals to district/town polygons.
8. SHAP explanations with climatological percentiles.
9. Replay of E1–E9 with latency-faithful as-of bundles, including the baseline toggle.
10. FastAPI + PostGIS; React/TS/Vite/Tailwind/MapLibre/deck.gl UI with the 10 screens.
11. Validation report: persistence vs pySTEPS vs rules vs model, time-blocked, bootstrap CIs.

**Stretch — Architecture B (pick at most two, only after A passes Phase 11 gates):**
- Advection-informed U-Net (0–3/6 h gridded)
- LightningCast zero-shot/fine-tune transfer
- TERLS radar "value of radar" case
- Deep ensembles

**Out of scope:** Architecture C (generative) — one "future work" slide only. Everything in §3.
