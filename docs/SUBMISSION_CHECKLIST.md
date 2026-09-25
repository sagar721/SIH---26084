# SIH26084 Submission Checklist (final)

**Deadlines** (VERIFIED in `SIH26084_Research_Report.md` §1, `docs/ACTION_PLAN_48H.md`):
- Idea submission on the SIH portal closes **30 Sep 2026**. **Internal target: 29 Sep** (one-day buffer).
- *"No request will be entertained after the deadline."*

Tick each box only after checking it yourself. Every number used must come from [`FINAL_CLAIMS.md`](FINAL_CLAIMS.md).

---

## 1. SIH portal requirements (from the project docs)

| ✓ | Item | Source / note |
|---|---|---|
| [ ] | College SPOC has nominated the team; the team leader has portal login (screenshot of the portal team page) | ACTION_PLAN_48H #1 |
| [ ] | Official **Idea PPT template** downloaded: `SIH2026-IDEA-Presentation-Format.pptx` from https://sih.gov.in/letters/2026/SIH2026-IDEA-Presentation-Format.pptx, saved to `docs/ppt/` | Research report §2.2; ACTION_PLAN_48H #2. **Not yet in the repo.** |
| [ ] | Deck is in the **prescribed format**; judges score "clarity and details in the prescribed format" | Guidelines, quoted in report §2.2 |
| [ ] | Team submits to **at most 2 PS**; this idea is new and not from any previous event/programme | Guidelines, report §2.2 |
| [ ] | Team leader submits the idea on the portal **by 29 Sep**; save the submission confirmation | ACTION_PLAN_48H; ROADMAP Phase 1 deliverables |
| [ ] | Aware that 4–5 teams *may* be selected and the organisation may select none. No selection is promised anywhere in the deck. | Guidelines, report §2.2 |
| [ ] | Is a video link or prototype link requested on the portal form? **Check on the portal: NEEDS VERIFICATION.** The docs only list the Idea PPT as mandatory. | — |

## 2. PPT

| ✓ | Item |
|---|---|
| [ ] | Content from [`docs/FINAL_PPT.md`](FINAL_PPT.md): 10 slides mapped into the official template sections |
| [ ] | Placeholders filled: `[TEAM NAME]`, `[TEAM ID]`, `[COLLEGE]`, `[TEAM LEADER]` |
| [ ] | Every number checked against the **Numbers audit** table at the end of FINAL_PPT.md |
| [ ] | None of the forbidden claims appear (FINAL_CLAIMS §C), in particular: ML beats pySTEPS as yes/no beyond 1 h · 6-h ML skill · hail/lightning/rain forecasting · storm-initiation prediction · significance across events · live/operational · deep learning |
| [ ] | Replay/prototype status stated on slides 1, 8 and 10; footer "Research prototype — not an official IMD warning" |
| [ ] | Slide 10 limitations complete: 3 held-out days · backward-in-time test · thin training data · 30-min cadence · single IR channel · no radar/lightning validation · replay only |
| [ ] | No IMD/NDMA logos (PRD §11: no impersonation) |
| [ ] | Exported as **PDF** as well as PPTX (ROADMAP Phase 1: "PPT (PDF)"); file size checked against any portal limit |

## 3. Prototype video

| ✓ | Item |
|---|---|
| [ ] | Recorded from [`docs/DEMO_VIDEO_SCRIPT.md`](DEMO_VIDEO_SCRIPT.md): E8 → Situation 14:00 UTC → cell #108 → 0–6 h forecast → ML probability → Replay → Model Performance → Data Health (→ optional Alert Center) |
| [ ] | Length 3–5 min (script: 4:40, or about 4:05 without Alert Center) |
| [ ] | Recorded in a **fresh private window** (alert approvals are kept in browser storage) |
| [ ] | Narration avoids the forbidden claims; REPLAY and "not an official warning" are visible or said |
| [ ] | Exported as MP4 (1080p or 1440×900); uploaded (unlisted) only if the portal asks for a link; a local copy is kept as the backup video (ROADMAP: "backup video") |

## 4. Working local prototype

| ✓ | Item |
|---|---|
| [ ] | Starts from the repository root with `cd apps/web && npm run build && npm run preview`; **http://localhost:4173/** opens |
| [ ] | On a fresh machine: `.venv/bin/python -m pipelines.replay.build_bundle --event E8_20260514 E10_20260504 E11_20260516` (only if `apps/web/public/bundles/` is missing), then `cd apps/web && npm ci && npm run build && npm run preview` |
| [ ] | Port 4173 is free (otherwise Vite silently uses 4174: read the printed URL) |
| [ ] | Internet available for the basemap, or the basemap is switched off in the sidebar (all data layers are local) |
| [ ] | E8 opens; E10 and E11 open; E1–E7, E8a and E9 are greyed with a reason |
| [ ] | Demo laptop rehearsed once end-to-end (ROADMAP: rehearsal) |

## 5. Screenshots (real E8 prototype and figures)

| ✓ | Item | Where |
|---|---|---|
| [ ] | Prototype screenshots (basemap on, 1440×900), from the verified browser run: situation, cell by map click, forecast (pySTEPS/ML), replay, performance, health, E10, 1280-px layout | `apps/web/e2e-shots/verify/*.png` |
| [ ] | Prototype screenshots (basemap off), all 9 screens + E10 | `apps/web/e2e-shots/*.png`. Regenerate with `cd apps/web && npm run e2e` (preview server running or auto-started). |
| [ ] | Science figures for slides | `data/figures/`: `E8_20260514_fig1/2/3/8`, `multi_event_fig11/12`, `phase5_fig14`, `phase6_fig17/18/19/20` |
| [ ] | Chosen screenshots **copied into a committed folder** (e.g. `docs/ppt/assets/`). `apps/web/e2e-shots/` is git-ignored. | — |

## 6. Repository / source

| ✓ | Item |
|---|---|
| [ ] | **Initialise version control.** The project folder is currently **not a git repository**. Then commit code, configs, docs, tests and `docs/FREEZE_ml-v0.json`. |
| [ ] | Decide what data to publish. Raw data is 16 GB and processed data 1 GB, and both are git-ignored. Keep `data/raw/cpc_merged_ir/manifest.json` (URLs + SHA-256) so anyone can re-download. Include the 82 MB replay bundles only if the repo host allows it (otherwise a release asset). |
| [ ] | Licences recorded. Code licence chosen by the team. Dependencies: pySTEPS, tobac, scikit-learn and MapLibre are BSD-3; React is MIT. NOAA CPC data: US Government work. IMD hail PDF: public document, attributed. Basemap: Esri tiles, display only; terms for public deployment NEEDS VERIFICATION. |
| [ ] | No credentials in the repo (`.env` git-ignored); no raw MOSDAC/EUMETSAT files (none were used) |
| [ ] | README points to: `docs/FINAL_RESULTS.md`, `docs/FINAL_CLAIMS.md`, `docs/PRODUCT_DEMO.md`, and the phase docs (FIRST_EVENT, BASELINE_EVAL, TRACKING_AUDIT, MULTI_EVENT, DECAY_AWARE, ML_PROTOTYPE) |

## 7. Final build / tests (last verified results)

| ✓ | Command (from the repository root) | Last result |
|---|---|---|
| [ ] | `.venv/bin/python -m pytest -q` | 76 passed, 1 skipped (the excluded event E8a) |
| [ ] | `.venv/bin/python -m pytest -q tests/test_phase7_freeze.py` | 2 passed: all 386 frozen files unchanged |
| [ ] | `cd apps/web && npm run build` | type-check + production build pass |
| [ ] | `cd apps/web && npm test` | 6/6 unit tests pass |
| [ ] | `cd apps/web && npx playwright install chromium && npm run e2e` | 2/2 pass (full E8 demo flow; E10 + unavailable events) |
| [ ] | Re-run all of the above on the day of submission. Any freeze-test failure means a frozen file changed: stop and investigate. | — |

## 8. Final claims / limitations (must match the deck and video)

| ✓ | Item |
|---|---|
| [ ] | Supported claims only: FINAL_CLAIMS §A (A1–A12), each with its evidence file |
| [ ] | Results stated alongside: FINAL_CLAIMS §B (yes/no ML no gain beyond 1 h; ML mostly smoothing of pySTEPS; 1 May excluded; object claims only to 30 min) |
| [ ] | Forbidden claims absent: FINAL_CLAIMS §C (12 items) |
| [ ] | Limitations shown: FINAL_CLAIMS §D, on slide 10 and in the video close |
| [ ] | Replay/prototype status explicit everywhere: REPLAY badge, "latency not modelled", CAP `status=Exercise`, footer disclaimer |

## 9. Known open items to disclose if asked

- **No forward-in-time test:** the NOAA archive on this server starts 2026-05-01.
- **Satellite source:** NOAA CPC merged IR substitutes for INSAT-3DS/Meteosat-9. No accounts were used for MOSDAC or EUMETSAT.
- **Basemap:** provider terms and boundary depiction for an Indian government review are not verified. The basemap can be switched off.
- **Other open items:** parallax is not corrected; the satellite-ID code is unverified; pySTEPS is built locally without OpenMP; LightGBM was replaced by scikit-learn HistGradientBoosting.
