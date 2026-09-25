# Final SIH 2026 Idea Presentation — SIH26084 (official template, evaluator-guide redesign)

## Files

| File | What it is |
|---|---|
| [`docs/ppt/FINAL_SIH26084_PRESENTATION.pptx`](ppt/FINAL_SIH26084_PRESENTATION.pptx) | Final deck, built on the official `SIH2026-IDEA-Presentation-Format.pptx` (kept unmodified in `docs/ppt/`) |
| [`docs/ppt/FINAL_SIH26084_PRESENTATION.pdf`](ppt/FINAL_SIH26084_PRESENTATION.pdf) | 6-page PDF exported from that PPTX (LibreOffice). Re-export after filling the placeholders. |
| `docs/ppt/build_sih_ppt.py` | Builds the deck |
| `docs/ppt/make_slide2_storyboard.py` | Renders the storm-cell panels from the frozen E8 replay bundle |
| `docs/ppt/assets/` | Real prototype screenshots (E8, 14 May 2026) and the frozen BSS chart |

**Team details:** Team ID 167858 · Team Name THE FEVICONS (slide 1 and the oval on slides 2–6). **Footer (slides 2–6):** "SIH26084 - StormLife Nowcast" (slide 1 has no footer in the official template). Footer text

## Priority order applied

1. **Official SIH template:**
   - ≤ 6 slides;
   - fixed section titles and idea-detail pointers kept verbatim as labels;
   - SIH branding, team-name oval, footer bar and page numbers unchanged;
   - PDF for upload;
   - instruction slide deleted, as the template allows.
2. **Frozen SIH26084 docs** are the only source of content ([`FINAL_CLAIMS.md`](FINAL_CLAIMS.md), [`FINAL_RESULTS.md`](FINAL_RESULTS.md)).
3. **Evaluator-guide requirements** as written in the request: 10-second skim, PS keyword match, technical deep dive, WHAT → WHY → HOW → PROOF → IMPACT. The guide document itself was not attached.
4. **The Ananta / FloodCast:** storytelling and layout quality only; nothing copied.

**Typography:**
- Template fonts (Times New Roman titles, Arial body); no third family added.
- Smallest text on any slide: 8.8 pt.

**Palette:** navy structure, teal accent, red reserved for the stated limit, decision support and risks, all on a white background.

## One question, one visual, one takeaway per slide

| Slide | Question | Dominant visual | 10-second takeaway |
|---|---|---|---|
| 1 | What is StormLife? | Mandatory fields + template SIH artwork (clean, no extra visual) | "SIH26084, thunderstorms/hail/cloudbursts, 0–6 h, StormLife Nowcast: satellite storm → forecast." |
| 2 | What problem does it solve? | "What we see today" (real IR + 3 open questions) vs the same real storm cell #108 through 6 stages | "Today's image shows where the storm is; StormLife estimates where deep convection may be, and how sure." |
| 3 | How does it work? | Tech stack → 5-stage process (forecast branches into 3 methods) → what it produces | "Satellite data in, storms found and tracked, three forecasts, validated, shown in a replay dashboard." |
| 4 | Can it actually work? | Frozen Brier skill chart + 4 finding cards, with today's evidence on top and the viability path below | "It exists, it was measured, and its limits are stated." |
| 5 | Who uses it, for what decision? | StormLife bar → three equal user cards (icon, question, real screen, sees/decision) → 4 benefit pills | "One storm signal, three decision users; exercise only, not operational." |
| 6 | What did the team contribute? | Research gap → question (dark centre card) → contribution → real evidence screen → official IMD + NOAA/CPC sources | "What can be verified from open IR alone, with evidence and official sources; it complements existing systems." |

---

## Slide 1 — Title page (template: TITLE PAGE)

**Mandatory fields** (template labels verbatim):

| Field | Value |
|---|---|
| Problem Statement ID – | SIH26084 |
| Problem Statement Title- | Convective Scale Nowcasting for Thunderstorms, Hail & Cloudbursts (0–6 hr) |
| Theme- | Disaster Management |
| PS Category- | Software |
| Team ID- | 167858 |
| Team Name | THE FEVICONS |

**Title slot:** StormLife Nowcast.

**Below the fields:** intentionally left clean (no hook strip); SIH artwork unchanged.


## Slide 2 — IDEA TITLE (official heading kept; idea title on the line below)

**Idea title line:** ***StormLife Nowcast:*** *satellite → storm cell → a forecast you can check. Convective-scale nowcasting, 0–6 h: how far can it be trusted?*

**▸ HOW IT ADDRESSES THE PROBLEM:** WHAT WE SEE TODAY
- Image: observed IR, 14 May 2026, 14:00 UTC, labelled "developing storm (cell #108)".
- Questions: ? Where will it move? · ? Will it intensify? · ? How far can we trust the forecast?
- Root problem: *Thunderstorms, hail and cloudbursts grow from deep convection within hours · no open, live radar or lightning feed in India*.

**Centre:** 30 min → 6 h · 2 km grid · target: deep convection, cloud top < 235 K.

**▸ DETAILED EXPLANATION OF THE PROPOSED SOLUTION:** WHAT STORMLIFE ADDS, satellite nowcasting of one real storm cell (#108, 14 May 2026).

| Stage | Text |
|---|---|
| 1 Satellite IR | every 30 min |
| 2 Detect | cold cell < 245 K |
| 3 Track | same cell, by area overlap |
| 4 Forecast | storm movement, 30 min – 6 h |
| 5 Probability + skill | calibrated, validated |
| 6 Replay / decide | knew · predicted · happened |

**Validated skill strip** (3 held-out storm days, pooled):
- **BSS 0.27**: ML probability skill at +2 h (no-fit ref. 0.02).
- **to ≈ 4 h**: best probability skill of the 4 methods tested.
- **1 h**: yes/no maps give no gain over pySTEPS beyond 1 h.

**▸ INNOVATION AND UNIQUENESS OF THE SOLUTION:**
1. Real storm days only
2. Baseline-first
3. Calibrated probability
4. Audited and frozen (386 files)

**Banner:** RESEARCH PROTOTYPE · real satellite data, held-out storm days · hazard-specific (hail, lightning, rain) skill not claimed · not live · not an official IMD warning.

## Slide 3 — TECHNICAL APPROACH (template title)

**Layout:** three connected columns, with the centre as the largest element.

| Column | Header (template pointer kept) | Content |
|---|---|---|
| Left (compact) | ▸ TECHNOLOGIES & TOOLS | 2 × 2 capability grid: category, tools, one purpose line |
| Centre (largest) | ▸ METHODOLOGY AND PROCESS: HOW STORMLIFE WORKS | 5 numbered stages with a vertical arrow flow; stage 4 branches into 3 forecast methods |
| Right | ▸ WORKING PROTOTYPE: WHAT IT PRODUCES | Output chain with real thumbnails from the frozen E8 bundle + product cards |

**Left: ▸ TECHNOLOGIES & TOOLS**, a 2 × 2 capability grid in the same card style as the methodology cards. All tools are confirmed used (`requirements.txt`, `apps/web/package.json`, FINAL_TECHNICAL_REPORT §10).

| # | Block | Technologies | Purpose |
|---|---|---|---|
| 1 | DATA & SCIENCE | Python · NumPy · pandas · xarray · SciPy | Satellite processing & numerical analysis |
| 2 | STORM INTELLIGENCE | OpenCV · scikit-image · custom overlap tracking · optical flow | Detect, track & characterize storm cells |
| 3 | FORECAST & VALIDATION | pySTEPS · scikit-learn · isotonic calibration · pytest | Forecast, calibrate & verify |
| 4 | PRODUCT | React · TypeScript · Vite · MapLibre GL | Interactive replay & decision-support dashboard |

**Note on OpenCV:** it is used through pySTEPS's Lucas–Kanade optical-flow motion (opencv-python-headless 5.0.0.93).

**Centre: how StormLife works.** Each stage has a plain-language line for non-specialists and the real method for technical judges.

| # | Stage | Plain-language line | Technical line |
|---|---|---|---|
| 1 | REAL SATELLITE DATA | What goes in: pictures of cloud-top temperature | NOAA/NCEP/CPC merged IR · 4 km · 30-minute frames · 3 held-out storm days |
| 2 | QC + PREPROCESSING | Clean every frame and put it on one map | Decode · quality control · cloud-top temperature (BT) · 2 km grid |
| 3 | STORM INTELLIGENCE | Find the storms and follow them | Cold cells < 245 K (deep convection) · area-overlap tracking · optical-flow motion |
| 4 | FORECAST ENGINE | Estimate what happens next, 30 min – 6 h | Three branches: **Persistence** (baseline: assume no change) · **pySTEPS advection** (move storms along their motion) · **ML probability** (how likely is deep convection? calibrated) |
| 5 | VALIDATION | Did the forecast actually work? | CSI · FSS · Brier skill · reliability · held-out storm days · same pixels · replay |

**Right: what it produces.** Thumbnails are real, rendered from the frozen E8 bundle; the skill thumbnail is the frozen BSS curves drawn without text.

| Output | Line |
|---|---|
| STORM CELL | cell #108, 14 May 2026 |
| TRACK + MOTION | where it has been and is heading |
| 30 MIN – 6 H FORECAST | where it may be next |
| CALIBRATED PROBABILITY | how likely is deep convection? |
| VALIDATED SKILL | how far to trust it |
| STORMLIFE DASHBOARD | 9-screen replay prototype |

- **Label:** STORMLIFE RESEARCH PROTOTYPE · replay, not live.
- **Product cards:** Replay situation map · 0–6 h forecast · Historical replay · Model performance · Data health · Exercise alert (CAP).

**Bottom strip** (one takeaway): *Real satellite data → audited storm intelligence → forecast + calibrated probability → validated decision support.*

**Deliberately excluded:**
- No frontend/backend/database pattern.
- No REST, WebSocket, cloud services, databases or live feeds (none exist).
- No technology marked "not used" in the project docs.
- No logo wall; numbered stages and real thumbnails carry the visual meaning.

## Slide 4 — FEASIBILITY AND VIABILITY (template title)

**Story strip:** BUILT → MEASURED → VERIFIED → CLEAR LIMITS → NEXT VALIDATION

**Zone 1: ▸ ANALYSIS OF THE FEASIBILITY OF THE IDEA: EVIDENCE AT A GLANCE** (5 compact cards):
- 25 days: 600 real satellite files
- 3 storm days: held out, E8 · E10 · E11
- 9 screens: working replay prototype
- 84 tests pass: incl. 2 browser tests
- 386 files: evidence hash-frozen

**Zone 2: ▸ WHAT THE TESTING SHOWED: 3 HELD-OUT STORM DAYS, POOLED, SAME PIXELS**
- Left: the frozen Brier skill chart (`bss_by_lead.png`, unmodified).
- Right: a 2 × 2 grid of evidence cards:

| Card | Headline | Line |
|---|---|---|
| **3 / 3** | pySTEPS beats persistence | at every tested lead, 30 min – 6 h |
| **≈ 2 h** | Useful baseline skill | FSS 40 km useful to ~90 min (persistence) / ~120 min (pySTEPS) |
| **≈ 4 h** | ML probability skill | BSS 0.27 at 2 h (no-fit ref. 0.02) · calibration error 0.002–0.004 |
| **1 h LIMIT** (red) | LIMIT: no yes/no gain | ML does not improve binary yes/no maps over pySTEPS beyond 1 h |

**Zone 3: ▸ POTENTIAL CHALLENGES AND RISKS → STRATEGIES FOR OVERCOMING THESE CHALLENGES: VIABILITY ROADMAP**

| BUILT NOW | → NEXT (not built) | → FUTURE (not built) |
|---|---|---|
| Research prototype · real satellite data; 3 held-out storm days · IR-only replay | More seasons + regions; forward-time validation; independent radar / lightning verification | INSAT-3DS / Meteosat, 15-min+; radar / lightning truth; live pipeline + initiation score |

**Limits line:** *Limits today: 3 held-out days (May 2026, NW India) · ML tested backward in time · single IR, 30-min · parallax not verified · no radar/lightning truth · replay, not live*

## Slide 5 — IMPACT AND BENEFITS (template title)

**Story:** *One storm signal → three decision users*. Visual order: StormLife → 3 users → 3 decisions → 4 benefits.

**▸ POTENTIAL IMPACT ON THE TARGET AUDIENCE**
- Central bar: **STORMLIFE: storm • forecast • skill • replay**, with an arrow down to each user card.
- Three equal cards, each with a large icon, a quoted question, one real screenshot and two compact label rows:

| Card | Icon | Question | SEES | DECISION | Screenshot (real prototype) |
|---|---|---|---|---|---|
| FORECASTER · IMD / NCMRWF | thunderstorm | "Where is convection developing?" | Storm location + motion + forecast skill | Compare forecast methods and focus attention | 0–6 h forecast, ML probability with validated-skill ribbon |
| DISTRICT DISASTER OFFICIAL · district level, with badge **EXERCISE / NOT OPERATIONAL** | alert | "Where should attention be focused?" | Probability + forecast track + replay | Prioritize areas for exercise / advisory review | Alert Center, exercise drafts + CAP preview |
| RESEARCHER / EVALUATOR · research | analytics | "Did the system predict what happened?" | Replay + held-out events + baseline comparison | Evaluate model skill, limitations and reproducibility | Historical Replay, knew → predicted → happened |

**▸ BENEFITS OF THE SOLUTION (SOCIAL, ECONOMIC, ENVIRONMENTAL, ETC.)** (4 pills):
- **SOCIAL:** Potential earlier awareness of deep convection.
- **ECONOMIC:** Open-data + open-source prototype.
- **ENVIRONMENTAL:** Satellite-first; no new sensing hardware.
- **TRUST:** Traceable metrics + visible limitations.

**Disclaimer:** *Research prototype • replay of real satellite data • not operational • exercise alerts only*

**Wording note:** the SOCIAL pill keeps "Potential", the existing verified wording, because earlier awareness has not been measured. No live alerts, deployment, IMD/NCMRWF integration, savings or disaster-reduction claims are made. Icons are Material Design icons (react-icons, MIT licence).

## Slide 6 — RESEARCH AND REFERENCES (template title)

**Tagline:** *Research gap → our question → our approach → evidence → official data sources*

**Layout** (arrows between columns): left, the research gap → centre, the question and our contribution → right, the evidence; the official sources run along the bottom.

**▸ EXISTING APPROACHES** (four compact cards):

| Card | Line |
|---|---|
| RADAR | cell tracking, e.g. MeteoSwiss TRT; IMD radar nowcasts |
| LIGHTNING | flash data in severe-storm guidance |
| NWP | model environment, e.g. in NOAA ProbSevere v3 |
| SATELLITE PRODUCTS | storm objects + phases, e.g. NWCSAF RDT |

Caption: *Operational and research systems already provide storm detection, tracking and severe-weather guidance.*

**↓ DATA / ACCESS CONSTRAINT:** *Indian open-data access and latency constrain reproducible, independent validation.* Every line is from DATA_REALITY.md and the research report Part 6:
- IMD radar raw data: licence or research request (DATA_REALITY: UNAVAILABLE / RESTRICTED).
- INSAT via MOSDAC: general users get data after ~3 days (DATA_REALITY: PARTIAL, 3-day latency).
- Lightning networks: restricted research access (NRSC treated as RESTRICTED; IITM research request only).
- IMD AWS/ARG portal: closed to the public, May 2025 (research report Part 6 [V]).

**▸ OUR RESEARCH QUESTION** (large dark card, visual centre): **WHAT CAN ACTUALLY BE VERIFIED FROM OPEN GEOSTATIONARY IR ALONE?**

**↓ STORMLIFE CONTRIBUTION** (6 cards + limitations):

| Card | Line |
|---|---|
| SATELLITE-FIRST | open geostationary IR only |
| BASELINE-FIRST | vs persistence + pySTEPS |
| CALIBRATED PROBABILITY | reliability shown |
| AUDITED TRACKING | ID switches 21 % → 0.4 % |
| REAL-EVENT REPLAY | knew · predicted · happened |
| TRACEABLE EVIDENCE | every number → hashed file |
| + EXPLICIT LIMITATIONS | 3 days · single IR · no radar/lightning truth |

**▸ VERIFIED PROTOTYPE**
- Real Model Performance screen (E8 replay, frozen ml-v0), including its claim-guard banner.
- Caption: *3 held-out storm days • reproducible replay • validated metrics • evidence frozen*.
- Card: **StormLife complements existing operational systems; it does not replace them.** · Research prototype · real-event replay · held-out validation.

**▸ DETAILS / LINKS OF THE REFERENCE AND RESEARCH WORK: DATA SOURCES USED**

| Badge | Source | Used for | Clickable links on the slide | QR code |
|---|---|---|---|---|
| IMD · Govt. of India | India Meteorological Department (IMD) | Hail-report dates to select the storm days (context only, not verification truth) | [Hail-storm report (PDF)](https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf) · [mausam.imd.gov.in](https://mausam.imd.gov.in/) | hail-report PDF |
| NOAA · NCEP · CPC | NOAA / NCEP Climate Prediction Center (CPC) | Globally Merged IR: all satellite inputs + verification truth · ~4 km IR · 30-minute cadence | [Merged IR page](https://www.cpc.ncep.noaa.gov/products/global_precip/html/wpage.merged_IR.shtml) · [Full-res IR](https://www.cpc.ncep.noaa.gov/products/global_precip/html/wpage.full_res.shtml) · [Data archive used](https://ftp.cpc.ncep.noaa.gov/precip/global_full_res_IR/) | Merged IR page |

**▸ METHODS & REPRODUCIBILITY** (separate panel, bottom right; data sources on the left are visually distinct):

| Row | Purpose line | Link |
|---|---|---|
| pySTEPS | external open-source: advection baseline + FSS (an external framework, not a StormLife contribution) | [pySTEPS official repo](https://github.com/pySTEPS/pysteps), clickable, HTTP 200 |
| STORMLIFE REPOSITORY | GitHub: our code · replay pipeline · validation · evidence | **[REPOSITORY URL]**, placeholder (no repo exists; the project folder is not a git repository) |
| DEMO / REPLAY | short demo of the verified prototype | **Demo video [VIDEO LINK]**, placeholder (no video URL exists) |

No StormLife repository or video URL appears anywhere in the project files. The GitHub links found in the docs are third-party repositories cited in the research report, so none was used.

**Story strip:** Research question → StormLife contribution → verified prototype → data sources → methods & reproducibility.

**Full citations** (in the speaker notes; no longer on the slide):
- pySTEPS: Pulkkinen et al., GMD 12, 4185 (2019)
- tobac: Heikenfeld et al., GMD 12, 4551 (2019); v1.5, GMD 17, 5309 (2024)
- TITAN: Dixon & Wiener (1993)
- FSS: Roberts & Lean (2008)
- ProbSevere v3: Cintineo et al., Wea. Forecasting 39(12) (2024)

**Not included:**
- **data.gov.in:** not used anywhere in the project (no mention in any project doc), so it does not appear.
- **Future sources** (Meteosat-9, INSAT-3DS, IMD radar, lightning) appear only as constraints, never as "used".

**Link checks** (2026-09-25):
- All 5 data-source URLs (plus the pySTEPS repo) returned HTTP 200 (IMD hail PDF: `application/pdf`; CPC pages titled "Globally Merged IR Data" and "Full-resolution IR Data").
- All 5 are clickable in both the PPTX and the exported PDF.
- Both QR codes decode to the intended URLs from the rendered PDF.

## Number audit

| # | Slide | Value | Source file |
|---|---|---|---|
| 1 | 1 | SIH26084; PS title; Disaster Management; Software | `SIH26084_Research_Report.md` §1 |
| 2 | 1–5 | 30 min – 6 h / 0–6 h | `config/baseline.yaml` (12 leads × 30 min); PS text |
| 3 | 2, 3 | cloud top < 235 K; cells < 245 K | `config/ml_dataset.yaml`; `config/tracking.yaml` |
| 4 | 2, 3 | 2 km grid; 453 × 603 px | `config/domain.yaml`; FIRST_EVENT |
| 5 | 2, 3, 5 | every 30 min; 4 km | FIRST_EVENT (CPC merged IR) |
| 6 | 1, 2 | cell #108; 14 May 2026; 14:00 UTC; −60/−30 min outlines; +30 m/+1 h/+2 h path; ML P at +2 h | E8 replay bundle (`cells/f26–f28`, `tracks.json`, `cellfc/i26.json`, `fc/pysteps_i26_l120.png`, `fc/ml_i26_l120.png`), hash-listed in its `manifest.json` |
| 7 | 2, 4 | BSS 0.27 at +2 h; no-fit ref. 0.02 | `ml_eval/ml-v0/metrics_pooled_lead.csv` (ML 0.273; NP31 0.015) |
| 8 | 2, 4 | best probability skill of 4 methods to ≈ 4 h | same file; FINAL_CLAIMS A5 |
| 9 | 2, 4 | yes/no p ≥ 0.5; no gain beyond 1 h | FINAL_CLAIMS B1 |
| 10 | 2, 4, 6 | 386 evidence files | `docs/FREEZE_ml-v0.json` (`n_files`) |
| 11 | 3 | QC ≤ 5 % missing; ≤ 4-px gaps | `pipelines/preprocess/qc.py` (0.05); `gapfill.py` (4) |
| 12 | 3, 4, 6 | 3 held-out storm days E8, E10, E11 | MULTI_EVENT §1; `model_card.json` |
| 13 | 3 | Python 3.11 | `docs/FREEZE_ml-v0.json` (3.11.16) |
| 14 | 4 | 25 days; 600 satellite files | `data/raw/cpc_merged_ir/manifest.json` (600 hourly files, 25 days; verified by count) |
| 15 | 4, 6 | 84 tests pass; 2 browser tests | SUBMISSION_CHECKLIST §7 (76 Python + 6 web + 2 Playwright) |
| 16 | 4, 6 | 9 screens | PRODUCT_DEMO |
| 17 | 4 | chart: BSS vs lead, 4 methods | `metrics_pooled_lead.csv`, plotted unmodified (min −1.11 unclipped) |
| 17a | 3 | skill thumbnail (BSS curves, no text) | same file, plotted unmodified (`docs/ppt/assets/thumb_skill.png`) |
| 18 | 4 | 3 / 3 days; CSI 0.586 vs 0.511 at 30 min | `multi_event/cross_event_by_lead.csv` |
| 19 | 4 | ≈ 2 h; FSS 40 km useful to 90 / 120 min | `multi_event/decay_by_event.csv` |
| 20 | 4 | calibration error 0.002–0.004 | `reliability.csv`; FINAL_CLAIMS A7 |
| 21 | 4 | May 2026 NW India; 7 convective training days | MULTI_EVENT; `model_card.json` (gate 7 of 14) |
| 22 | 4 | 30-min frames; 15-min future | FIRST_EVENT; DATA_REALITY |
| 23 | 5 | ML P ≥ 0.5 within 10 km; CAP 1.2 | `apps/web/public/bundles/E8_20260514/alerts.json` (rule); PRD F12 |
| 24 | 6 | ~156 cities, 0–2 h | Research report Part 9 (IMD WDSS-II) |
| 25 | 6 | AWS/ARG closed May 2025; MOSDAC 3-day latency | Research report Part 6 [V]; DATA_REALITY |
| 26 | 6 | citation years | Research report Part 9; FINAL_TECHNICAL_REPORT §28 |
| 27 | 6 | ID switches 21 % → 0.4 % | `E8_20260514/audit/audit_v1.json` (0.206) → `audit_v2_none.json` (0.004); FINAL_CLAIMS A9 |
| 28 | 6 | ~4 km IR, 30-minute cadence; ~3-day MOSDAC latency | FIRST_EVENT; DATA_REALITY |

**Status: PASS.** Every number found in the slide text is listed above. No cost figure is shown, because none is documented.

## Claim audit (vs `docs/FINAL_CLAIMS.md`)

| Claim | Slide | Source | Status |
|---|---|---|---|
| Real data only; days fixed before scoring | 2, 3 | A1, A8 | Supported |
| pySTEPS beats persistence at every lead, 3 of 3 days | 4 | A2 | Supported |
| Useful baseline skill ≈ 2 h | 4 | A3 | Supported |
| ML best probability skill of the 4 methods to ≈ 4 h; calibrated | 2, 4 | A5, A7 | Supported (measured ranking) |
| ML not better than pySTEPS as yes/no beyond 1 h; not universally better | 2, 4 | B1 | Stated |
| Tracking audited | 2, 3 | A9 | Supported |
| Exercise advisories only; alert skill not verified | 2, 5 | PRD F12 | Supported |
| Thunderstorms, hail and cloudbursts grow from deep convection; StormLife targets deep convection; hazard-specific skill not claimed | 2 | FINAL_TECHNICAL_REPORT §3; FINAL_CLAIMS C5 | Supported (scope statement) |
| Complements, does not replace, existing systems | 6 | REVIEW_AND_SCOPE R6 | Supported |
| All required limits: 3 days, May NW India, backward-in-time ML, 30-min, single IR, no radar/lightning truth, parallax, replay not live | 4 (+ 2, 5) | §C–§D | Shown |

**Automatic scan of the slide text found none of:**
- "revolutionary", "100 %", "first ever", "guaranteed", "real-time", "state-of-the-art";
- any not-used technology (SatPy, rasterio, MetPy, Tailwind, deck.gl, LightGBM, FastAPI, PostGIS, REST, WebSocket).

The only "best" is the measured ranking. **Status: PASS.**

## Evaluator tests (self-simulated from the rendered PDF)

| Test | Result |
|---|---|
| 10-second skim | **Pass.** Problem, solution, domain and time horizon are all visible on slides 1–2 without reading body text. |
| Technical deep dive | **Pass.** Slide 3 shows data → QC → grid → detection → tracking → forecast (3 methods) → ML → validation → product, with the hand-off named on every arrow. Slide 4 gives the evidence. |
| Credibility | **Pass.** Real IR imagery, real events (E8/E10/E11), frozen metrics chart, real screenshots, 84 tests, stated limits. |
| Differentiation | **Pass.** Slide 6 names the question and seven contributions and states the complement-not-replace position. |
| Feasibility | **Pass.** Slide 4 separates "what exists today" (KPIs + chart) from the viability path (only the first step built). |
| PS keywords in context | convective-scale (2), 0–6 h (1–3), thunderstorms / hail / cloudbursts (1–2), storm movement (2), deep convection (1, 2, 5), satellite (all), forecasting (1–5), validation (2–5), GIS map (3), decision support (3, 5) |

## Visual check

- All 6 slides were rendered and inspected. No overlap, no clipping, no shape outside the slide.
- Smallest text is 8.8 pt; section labels 10.5 pt; big numbers 14–20 pt.
- The pptx skill validator (`--original` template) passes, and no leftover template text remains.

## Fields to add manually

| Item | Where |
|---|---|
| **[REPOSITORY URL]** | Slide 6 |
| **[VIDEO LINK]** | Slide 6 (delete if the portal does not ask) |

After filling these, re-export the PDF from PowerPoint or Google Slides.
