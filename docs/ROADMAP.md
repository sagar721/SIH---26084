# Roadmap — Phases 0–13

**Rules:**
- **Architecture A is the minimum working system**; Phases 2–11 deliver it.
- Architecture B items are marked **[B-stretch]** and start only after the Phase 11 gate passes.
- Architecture C is not a dependency anywhere.

**Dates (PROPOSED):**
- Idea deadline: **30 Sep 2026** (VERIFIED).
- Finale: proposed December 2026 (VERIFIED). The shortlist announcement date is unknown (NEEDS VERIFICATION).
- Phases 2–13 assume we keep building regardless of the shortlist outcome.

| Phase | Window (PROPOSED) |
|---|---|
| 0 | 25 Sep |
| 1 | 25–29 Sep |
| 2 | 1–8 Oct |
| 3 | 6–14 Oct |
| 4 | 12–18 Oct |
| 5 | 16–26 Oct |
| 6 | 22–31 Oct |
| 7 | 27 Oct–5 Nov |
| 8 | 3–10 Nov |
| 9 | 15 Oct–10 Nov (parallel) |
| 10 | 20 Oct–20 Nov (parallel) |
| 11 | 10–22 Nov |
| 12 | 20–30 Nov |
| 13 | 1 Dec → finale |

---

### PHASE 0 — Scope + Data Feasibility
- **Goal:** Freeze scope and confirm what data we can actually get.
- **Tasks:**
  1. Review the research.
  2. Write the specs (this folder).
  3. Open accounts: EUMETSAT, Earthdata, CDS, MOSDAC, JAXA, NCMRWF RDS.
  4. Test-download one SEVIRI slot and one INSAT L1B file; record file sizes (risk K1).
  5. Check what MOSDAC "limited datasets" includes (K6).
  6. Save the IMD hail report PDF.
  7. Close decisions D1–D10.
- **Deliverables:** `docs/*`, a filled decisions table, `data/PROVENANCE.md` with the first entries, a measured bytes/slot figure.
- **Acceptance:**
  - All specs are committed.
  - ≥ 1 real SEVIRI file has been opened in satpy.
  - Account status is known for every source.
- **Dependencies:** none.
- **Risk:** MOSDAC approval delay → Meteosat is primary.

### PHASE 1 — SIH Idea Submission Proof
- **Goal:** A submitted Idea PPT backed by real figures from real data.
- **Tasks:**
  1. Download one event window. Choose E8 (14 May 2026 hail) or E4 (2 May 2025 Delhi): SEVIRI 12 h around T0 + ERA5.
  2. Regrid, run tobac, render three figures:
     - tracked cells with IDs;
     - cooling-rate map;
     - one cell's lifecycle curve with phase bands.
  3. Overlay IMD hail report locations (E8).
  4. Fill the official PPT format: problem, data reality, architecture A/B, differentiation vs RDT/TRT/ProbSevere, validation plan, figures, limitations.
  5. Team leader submits via the SPOC.
- **Deliverables:** PPT (PDF), `notebooks/phase1_proof.ipynb`, 3 PNG figures, submission confirmation.
- **Acceptance:**
  - Submitted **before 29 Sep 23:59 IST** (one-day buffer).
  - Every figure regenerates from the notebook.
  - No metric appears that we haven't computed.
- **Dependencies:** Phase 0 accounts; SPOC nomination.
- **Risk:** Deadline. If tobac tuning stalls, use pySTEPS T-DaTing or a simple threshold + connected-components labelling for the proof figures, labelled as such.

### PHASE 2 — Data Pipeline
- **Goal:** Reproducible, idempotent ingest + QC + 2 km grid for the chosen period.
- **Tasks:**
  1. Ingest modules for SEVIRI, ERA5, IMERG, ISS-LIS, GPM DPR, GFS (live), hail report parser; INSAT for event days.
  2. Data Tailor cropping (K1).
  3. QC module.
  4. Zarr writer.
  5. Provenance manifest.
  6. Training-day sampling plan: all event days + N storm days/year (N chosen to fit the ≤ 1 TB budget, D3).
- **Deliverables:** `pipelines/ingest/*`, `pipelines/preprocess/*`, Zarr cubes, QC report notebook.
- **Acceptance:**
  - Re-running a day produces identical checksums.
  - ≥ 95 % of expected slots present or explicitly flagged.
  - Regrid test passes (PRD F2).
- **Dependencies:** Phase 0.
- **Risk:** Volume/bandwidth → reduce channels (10.8, 12.0, 6.2/7.3, 8.7, 0.6, 1.6) and use 30-min cadence for non-event days.

### PHASE 3 — Storm Detection + Tracking
- **Goal:** Stable cells, tracks and genealogy across all ingested days.
- **Tasks:**
  1. Tune tobac thresholds, min area and v_max on 5 audit days.
  2. Segmentation polygons.
  3. merge/split.
  4. Write to PostGIS.
  5. Manual audit sheet.
  6. Phase rule table v1 (`config/phases.yaml`).
- **Deliverables:** `ml/tracking/*`, tracks DB, audit sheet, phase-labelled tracks.
- **Acceptance:**
  - PRD F4: ≥ 90 % of mature cells tracked ≥ 3 frames without ID swap on audit days.
  - Tracking < 2 min/frame.
- **Dependencies:** Phase 2.
- **Risk:** Coarse IR over-merging → fallback to T-DaTing; document the choice.

### PHASE 4 — Baseline Forecasting
- **Goal:** All baselines produce forecasts in the same format as our model.
- **Tasks:**
  1. Persistence.
  2. pySTEPS Lucas–Kanade + semi-Lagrangian (BT and IMERG).
  3. Mecikalski CI rules.
  4. Constant-velocity ETA.
  5. Stay-in-phase and climatological transition matrix.
  6. BT-threshold lightning rule.
- **Deliverables:** `ml/forecasting/baselines/*`, baseline predictions for val/test, **first verification table** (baselines only).
- **Acceptance:**
  - Baselines are scored by `ml/verification` on the per-head splits (VALIDATION_PLAN §3).
  - The table regenerates from one command.
- **Dependencies:** Phase 3.
- **Risk:** None major. This phase is what makes every later claim credible.

### PHASE 5 — ML V1
- **Goal:** Calibrated LightGBM heads for CI, lightning, heavy rain and hail potential.
- **Tasks:**
  1. Feature builder with climatology percentiles (train years only).
  2. Label joins (ISS-LIS overpass mask, IMERG, DPR flags).
  3. Train with time-blocked CV.
  4. Isotonic calibration.
  5. SHAP.
  6. Model cards.
- **Deliverables:** `ml/models/*`, artifacts + cards, verification table v2 (model vs baselines).
- **Acceptance:**
  - Metrics come from test splits only, with bootstrap CIs.
  - Reliability diagrams exist.
  - The leakage checklist passes.
  - Results are reported **whether or not they beat the baselines**.
- **Dependencies:** Phase 4.
- **Risk:** Sparse lightning labels → evaluate-only fallback with the proxy clearly labelled.

### PHASE 6 — Lifecycle Transition + Genealogy
- **Goal:** Transition probabilities, remaining-life survival model, genealogy features and the hypothesis test.
- **Tasks:**
  1. Transition heads (30/60 min).
  2. Discrete-time survival.
  3. Genealogy features (n_merges, time since merge, parent max intensity).
  4. Ablation: with vs without genealogy.
  5. Mentor review of phase rules (D7).
- **Deliverables:** transition + survival models; ablation result ("Do recently merged cells intensify more?"); genealogy API data.
- **Acceptance:**
  - BSS vs both transition baselines, per horizon.
  - C-index reported.
  - Ablation reported with CIs.
- **Dependencies:** Phases 3, 5.
- **Risk:** Phase-rule noise → smooth with a 2-frame hysteresis; report sensitivity to thresholds.

### PHASE 7 — ETA + Uncertainty
- **Goal:** ETAs to places with conformal intervals and measured coverage.
- **Tasks:**
  1. Places layer (districts + town buffers).
  2. Kalman motion.
  3. Polygon advection + intersection.
  4. Parallax on/off experiment (K3).
  5. Split-conformal per lead bin.
  6. `p_arrival`.
- **Deliverables:** `ml/forecasting/eta.py`, `conformal.py`, ETA metrics.
- **Acceptance:**
  - PRD F7: coverage within ±5 pp of nominal on test, or the shortfall is shown.
  - ETA MAE vs the constant-velocity baseline.
- **Dependencies:** Phases 3, 6.
- **Risk:** Few arrival events per place → pool across places; report counts.

### PHASE 8 — Historical Replay
- **Goal:** Latency-faithful replay bundles for E1–E9, with the baseline toggle.
- **Tasks:**
  1. `config/latency.yaml`.
  2. `build_bundle.py`.
  3. `leakage_check.py`.
  4. "What happened" layers (IMERG, LIS, hail reports, news T0).
  5. Scorecards.
- **Deliverables:** `data/replay/*`, leakage report.
- **Acceptance:**
  - REPLAY_SPEC §8 acceptance criteria pass.
  - Events are excluded from train/cal.
- **Dependencies:** Phases 5–7.
- **Risk:** Missing slots on event days → show gaps honestly.

### PHASE 9 — Backend/API
- **Goal:** FastAPI + PostGIS serving every screen with envelopes.
- **Tasks:**
  1. Schema + migrations.
  2. Routers (ARCHITECTURE §5).
  3. Envelope model + contract tests.
  4. CAP builder (`status=Exercise`).
  5. Token for alert approval.
  6. OpenAPI → TS client.
- **Deliverables:** `services/api`, OpenAPI spec, tests.
- **Acceptance:**
  - p95 < 300 ms on the demo data.
  - 100 % of prediction endpoints pass envelope contract tests.
  - CAP validates.
- **Dependencies:** Phase 3 (DB shape); fill-in continues through Phase 8.
- **Risk:** Scope creep → only the endpoints listed.

### PHASE 10 — Forecaster UI
- **Goal:** The 10 screens per [UI_UX_SPEC.md](UI_UX_SPEC.md).
- **Tasks:**
  1. Shell (sidebar, top bar, context panel, timeline).
  2. Map layers.
  3. Cell card.
  4. Genealogy tree.
  5. Replay three-pane.
  6. Performance and Data Health screens.
- **Build order:** Live → Cells → Replay → Confidence → Performance → Forecast → Hazards → Explain → Alerts → Health.
- **Deliverables:** `apps/web`.
- **Acceptance:**
  - UI spec acceptance criteria pass.
  - Mode badge is always visible.
  - Every number shows its model version + data tier.
  - 60 fps pan with ≤ 500 cells.
- **Dependencies:** Phase 9 (mock JSON fixtures, **from real pipeline outputs only**, allowed earlier).
- **Risk:** UI polish consuming ML time → timebox; the judge-critical screens come first.

### PHASE 11 — Validation
- **Goal:** Frozen, reproducible verification report.
- **Tasks:**
  1. Run VALIDATION_PLAN end to end.
  2. Ablations (sources, genealogy, parallax).
  3. Skill-vs-lead curves.
  4. Report HTML.
  5. Freeze the commit hash.
- **Deliverables:** `evaluation/report.html`, `metrics` table, figures for the PPT.
- **Acceptance:**
  - Every UI/PPT number links to the report.
  - The leakage checklist is signed off by two team members.
- **Dependencies:** Phases 4–8.
- **Risk:** Results weaker than hoped → report them anyway. Honest skill curves are a strength with this jury.
- **Gate:** only after Phase 11 passes may **[B-stretch]** start. Pick at most two:
  - (a) LightningCast transfer on ISS-LIS
  - (b) advection-informed U-Net 0–3 h
  - (c) TERLS radar "value of radar" case
  - (d) deep ensembles

### PHASE 12 — Hardening
- **Goal:** Demo-safe, offline-capable, licence-clean.
- **Tasks:**
  1. Docker Compose offline mode.
  2. Precomputed bundles/tiles.
  3. Error states.
  4. Licence audit.
  5. `data/PROVENANCE.md` complete.
  6. Model cards.
  7. README "real / proxy / future" table.
  8. Security review (secrets, tokens).
- **Deliverables:** Release tag, offline demo bundle, licence report.
- **Acceptance:**
  - Clean-machine install ≤ 30 min.
  - Demo runs with network off.
  - No GPL code in the core (D5).
- **Dependencies:** Phases 9–11.
- **Risk:** Last-minute features → freeze a week before the finale.

### PHASE 13 — SIH Demo
- **Goal:** A 5-minute demo + Q&A that survives technical questioning.
- **Tasks:**
  1. Script per report Part R (data reality → E8 replay → cell card → performance → skill curve → radar-ready → future).
  2. Q&A drill (the research's list + "why not ConvLSTM?").
  3. Backup video.
  4. Printed one-pager of metrics.
- **Deliverables:** Demo script, rehearsal recordings, backup video.
- **Acceptance:**
  - Three timed rehearsals ≤ 5 min.
  - Every Q&A answer is backed by a slide or screen.
- **Dependencies:** Phase 12.
- **Risk:** Live network at the venue → offline mode by default.
