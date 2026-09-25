# First Real Event — Phase 1 Proof (E8, 14 May 2026, NW India hail)

**Status:** Phase 1 complete (proof slice) · **Run:** 2026-09-24 · **Source-of-truth docs:** [REVIEW_AND_SCOPE.md](REVIEW_AND_SCOPE.md), [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_REALITY.md](DATA_REALITY.md), [ROADMAP.md](ROADMAP.md)

**What was proven:** real geostationary IR for one Indian event → reproducible QC and 2 km grid → tobac detection and tracking → per-cell centroid, area, movement, lifetime, growth/decay, merge/split families and rule-based phases → 4 figures. **No synthetic or random data is used anywhere in the pipeline.** No probabilities, forecasts or skill metrics are produced in Phase 1.

---

## 1. Phase-1 decisions (urgent items from REVIEW_AND_SCOPE §5)

| # | Decision | Resolution for Phase 1 | Status |
|---|---|---|---|
| D1 | Primary satellite | **NOAA/NCEP/CPC Globally Merged IR** (4 km, 30 min, anonymous). This source is **not listed in DATA_REALITY.md**. Every approved satellite route needs credentials that are not on this machine: EUMETSAT download returned HTTP 404 without a token; there is no MOSDAC account. The CPC product merges geostationary window-channel IR; one satellite (ID code 5) covers the whole domain. | **PROPOSED addition to DATA_REALITY** (team to approve). Meteosat-9 IODC / INSAT remain the Phase-2 primaries once accounts exist. Satellite-ID code mapping: NEEDS VERIFICATION |
| D2 | Domain | Frozen domain used: 26–34°N, 72–84°E, 2 km LAEA (centre 30°N 78°E) | Resolved |
| D2 | Season | Not needed for a single event | Open (Phase 2) |
| D3 | Storage | Measured: CPC ≈ 27 MB per hourly global file (~0.65 GB/day). **SEVIRI IODC full-disk ≈ 181 MB per 15-min slot → ~17 GB/day uncropped** (EUMETSAT API metadata). This confirms risk K1: Phase 2 must crop at the source or subsample. | Measured |
| D6 | Basemap / boundaries | Figures **omit international and state boundaries**; orientation is by graticule and station labels. Official display needs Survey-of-India boundaries (licensed source NEEDS VERIFICATION). | Resolved for Phase 1 |
| D7 | Phase thresholds | Rules v0 from PRD F5 used as-is (`config/phases.yaml`) | Mentor sign-off still pending |
| D4, D8, D10 | Second PS, owners, mentor | Team decisions; not resolvable in code | Open |

## 2. Event and data

| Item | Value |
|---|---|
| Event | **E8** (REPLAY_SPEC §1): NW-India hail, **14 May 2026** |
| Truth | IMD RMC New Delhi "Hail storm report of the Northwest India updated on 16 MAY 2026", row 14-05-2026: Sonmarg, Ganderbal, Shopian, Kulgam, Shirsi, Bageshwar, Chamoli, Amritsar, Ambala, Gurugram, Bahadurgarh, Bareilly ("Barely"), Prayagraj, Varanasi, Unnao, Churu |
| Satellite input | CPC merged IR, 24 hourly files × 2 fields = **48 frames, 00:00–23:30 UTC**, 677.5 MB compressed (incl. satellite-ID file) |
| Grid | 2 km LAEA, 453 × 603 px; `in_domain` mask for the lat/lon box; effective resolution ~4 km |
| Provenance | Every file's URL, bytes, SHA-256, HTTP Last-Modified and download time: [`data/PROVENANCE.md`](../data/PROVENANCE.md) |

## 3. Reproduce

```bash
uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m pipelines.ingest.cpc_merged_ir --start 2026-05-14T00:00 --end 2026-05-14T23:00 --satid
.venv/bin/python -m pipelines.ingest.hail_report --event E8_20260514
.venv/bin/python -m scripts.run_first_event --event E8_20260514 --rebuild     # ~35 s on a laptop
.venv/bin/python -m pytest -q
```

**Reproducibility check (done):** two full `--rebuild` runs from the same raw files produced bit-identical outputs.
- BT cube SHA-256 `1305380a…9b55`
- `cells_summary.csv` `e14e0e7e…4ae8`
- `cells_per_frame.csv` `f3e9a4c6…a9ab`

## 4. Pipeline (modules)

| Stage | Module | What it does |
|---|---|---|
| Acquisition | `pipelines/ingest/cpc_merged_ir.py` | Parallel, idempotent HTTPS download; manifest with SHA-256 |
| Acquisition | `pipelines/ingest/hail_report.py` | Archives the IMD PDF (hash-named) and geocodes stations (Nominatim, 1 req/s, cached) |
| Decode | `pipelines/preprocess/decode.py` | 1-byte → K (`+75`), 255 → NaN, north→south row flip. Orientation checked on real data: at 05:30 IST, Tibet 278 K, Thar 300 K, Arabian Sea 297 K |
| Gap fill | `pipelines/preprocess/gapfill.py` | Fills only source gaps ≤ 4 connected native px from valid neighbours; flags every filled pixel (`gapfilled`) |
| Regrid | `pipelines/preprocess/regrid.py` | NaN-aware bilinear onto the LAEA grid |
| QC | `pipelines/preprocess/qc.py` | BT 170–330 K, residual missing ≤ 5 %, monotonic time |
| Cube | `pipelines/preprocess/build_cube.py` | NetCDF cube with QC vars and raw-file hashes (NetCDF rather than the Zarr in ARCHITECTURE §4, which is fine for one event; Zarr in Phase 2) |
| Tracking | `ml/tracking/track.py` | tobac 1.6.2: `feature_detection_multithreshold` [273, 253, 235, 221, 208 K] → `segmentation_2D` (< 245 K) → `linking_trackpy` → `merge_split_MEST` |
| Lifecycle | `ml/tracking/lifecycle.py` | Per feature: min BT, area < 245 K, cold core < 221 K, centroid, motion, rates per 30 min, phase (rules v0), missing-data flag. Per cell: lifetime, net motion, extremes, phases seen, merge/split family |
| Orchestration | `scripts/run_first_event.py`, `scripts/make_figures.py` | End-to-end run + figures + `run_summary.json` |

## 5. Results (from `data/processed/E8_20260514/run_summary.json`)

| Quantity | Value |
|---|---|
| Frames | 48 (30 min) |
| Frames failing QC | **6** (10:00–12:30 UTC): residual missing 5.0–5.4 % > 5 % limit. **Kept and flagged, not hidden.** Gaps concentrate over the NE Himalaya/Tibet corner (14 % missing there vs 0.5–2 % over the plains). |
| Source missing (before fill) | 0.8–6.1 % per frame; after fill 0.6–5.4 %. Missing pixels line cloud edges (pink in figures), consistent with holes left by a parallax shift in the merged product (NEEDS VERIFICATION) |
| Features detected / linked | 2,920 / 2,493 |
| Cells (≥ 2 frames) | **613** |
| Cells living ≥ 2 h | **181** |
| Deep-convective cells living ≥ 2 h (min BT < 235 K) | **36**: net speed median **31 km/h** (IQR 19–41), median heading **106°** (moving ESE) |
| Cells reaching < 221 K | 19 |
| Merge/split (`merge_split_MEST`) | OK; **103** families with > 1 cell (sizes 2–12) |
| Cells with ≥ 1 frame touching missing data | 145 (flagged per frame: `touches_missing`) |
| Phase labels (per cell-frame) | Unclassified 2,049 · Developing 224 · Initiation 199 · Decaying 21 · **Mature 0** (see §7) |

**Per-cell outputs** (`cells_summary.csv`): `cell`, `track_family`, first/last time, `n_frames`, `lifetime_min`, start/end lat-lon, `min_bt_K`, `max_area_km2`, `max_cold_core_km2`, `median_step_speed_kmh`, `net_speed_kmh`, `net_heading_deg`, `net_displacement_km`, `max_cooling_K_per_30`, `phases_seen`, `frames_touching_missing`, `merge_split_family_size`.

**Per-frame outputs** (`cells_per_frame.csv`): centroid (lat/lon, LAEA x/y, `centroid_source`), `area_km2`, `cold_core_km2`, `min_bt_K`, `speed_kmh`, `heading_deg`, `d_min_bt_30`, `area_change_frac_30`, `d_cold_core_30`, `phase`, `touches_missing`.

**Example — cell #293** (the fig. 4 cell):
- Born 08:30 UTC (14:00 IST) near 33.56°N 74.63°E; tracked for 5 h (11 frames); ended 13:30 UTC near 33.19°N 76.37°E.
- Net 167 km at 33 km/h, heading 104°.
- Min BT 218.6 K. Area < 245 K grew from ~10,000 to 45,576 km² (peak ~16:00 IST), then shrank.
- Phases: Developing → Decaying. Merge/split family of 5 cells.
- Passes 18 km from Kulgam (hail reported 14 May). **The report gives no time, so this shows co-location, not causation.**

## 6. Figures (all from real data)

| # | File | Content |
|---|---|---|
| 1 | [`data/figures/E8_20260514_fig1_satellite_frame.png`](../data/figures/E8_20260514_fig1_satellite_frame.png) | Enhanced IR BT at 13:30 UTC (19:00 IST) + hail-report stations. Cold convective shields over Punjab (near Amritsar) and N Rajasthan (near Churu) |
| 2 | [`data/figures/E8_20260514_fig2_detected_cells.png`](../data/figures/E8_20260514_fig2_detected_cells.png) | Same frame: tobac segments (< 245 K) outlined by phase, cell IDs |
| 3 | [`data/figures/E8_20260514_fig3_trajectories.png`](../data/figures/E8_20260514_fig3_trajectories.png) | All cells living ≥ 2 h; deep-convective ones coloured by time with direction arrows |
| 4 | [`data/figures/E8_20260514_fig4_lifecycle_cell293.png`](../data/figures/E8_20260514_fig4_lifecycle_cell293.png) | Lifecycle of cell #293: min BT, area/cold core, ΔminBT per 30 min, phase shading, missing-data markers |

**Figure-frame rule:** the frame with the largest in-domain area < 221 K.

**Figure-4 cell rule (v2, fixed before viewing the result):** among deep cells (min BT < 235 K) living ≥ 2 h whose track passes within 50 km of a reported hail station, take the coldest; ties go to the longest-lived.
- Rule v1 ("longest-lived") was dropped because it favours chained linking errors: it picked a track moving ~120 km/h.
- An earlier variant without the deep-convection condition picked a warm (~270 K) non-convective cloud.
- Both drafts were discarded; this is recorded here so the choice is auditable.

## 7. Method changes made during Phase 1 (with evidence)

| Change | Why (measured on this event) | Where |
|---|---|---|
| Min feature size 25 px (100 km²) at the 273 K level (colder levels 4–8 px) | 3,581 of 4,617 features were small 273 K fragments. trackpy subnetworks exceeded 30 points; linking failed, and with adaptive search it hung for > 10 min. Now linking takes < 1 s. | `config/tracking.yaml` |
| `method_linking: random` instead of `predict` | With `predict`, spurious jumps compounded: step speed 99th pct 246 km/h, max 305 km/h. With `random`: 99th pct 105, max 108 km/h (= v_max); median 42 km/h; more ≥ 2 h cells (261 vs 235 at the ≥ 4-frame level) | `config/tracking.yaml` |
| numba installed | trackpy's pure-Python fallback was impractically slow | `requirements.txt` |
| Small-gap fill + NaN-aware bilinear | NaN-propagating bilinear doubled missing data (e.g., 2.3 % → 5.2 %), failing 36/48 frames. After the change, 6/48 fail, and they are reported | `gapfill.py`, `regrid.py` |
| Segment centroid for segmented cells | Feature position jumps when the coldest threshold level changes (median step 90 vs 60 km/h). The segment centroid is used for area-consistent position; net displacement is reported as the robust motion measure | `lifecycle.py` |
| Phase rates per 30 min | Source cadence is 30 min; the PRD's −4 K/15 min is applied as −8 K/30 min | `config/phases.yaml` |

## 8. Known limitations / NEEDS VERIFICATION

1. **Source substitution.** CPC merged IR is not in DATA_REALITY.md. It is a single IR channel, so there are no WV/tri-spectral interest fields. It is 30 min, not 15 min. Its long-term archive on this server starts only 2026-03-30 (older data: NEEDS VERIFICATION, e.g. NASA GES DISC GPM_MERGIR, which requires Earthdata login). **The team must approve it as a Phase-1/fallback source or replace it.**
2. **Satellite ID** code 5 → satellite name: NEEDS VERIFICATION.
3. **Parallax.** Whether the merged product is already parallax-corrected: NEEDS VERIFICATION. The cloud-edge gap pattern suggests it may be.
4. **Segmentation at 245 K merges cells into mesoscale shields** (cell #293 reaches 45,576 km²). Cold-core segmentation (235/221 K) should be evaluated in Phase 3.
5. **Mature phase never triggered.** Rule v0 requires min BT < 221 K and |area change| ≤ 10 %/30 min. At 30-min cadence, areas rarely stay within ±10 %, and few cells reach < 221 K. The rule needs recalibration or mentor review (D7). **Rules v0 are PROPOSED, not validated.**
6. **Per-step motion of large shields is noisy** (shape changes). Use net displacement, or smoothed/Kalman motion (Phase 3/7). No per-cell motion uncertainty is claimed yet.
7. **merge_split_MEST families** were not manually audited; family sizes up to 12 may over-group (Phase 3 audit).
8. **Hail report** gives dates and places only, with no times. "Shirsi" (Uttarakhand) was not found by the geocoder and is excluded (NEEDS VERIFICATION of spelling/location). The PDF's column layout did not survive text extraction, so state assignments are geocoding hints.
9. **No tracking audit sheet yet.** PRD F4's ≥ 90 % criterion is Phase 3 work and is not claimed here.
10. **Six midday frames fail QC** (> 5 % residual missing) but are used for tracking, with per-cell flags.

## 9. Tests (`tests/test_phase1.py`, 10 passing)

**Unit tests** use tiny hand-built arrays to check arithmetic only. They are fixtures, never used as weather data or reported:
- decode scaling / missing / row flip
- wrong-size rejection
- source-grid bounds
- 2 km target grid covers the domain
- movement: 1° north in 1 h = 110.9 km/h at 0°
- QC flags
- phase-rule sequence

**Real-data tests** skip if data is absent:
- raw files match manifest SHA-256 and size
- cube: consistent QC, 30-min steps, BT within 170–330 K, raw hashes match the manifest
- tracks: ≥ 1 cell with ≥ 4 frames, no duplicate cell-frames, non-negative areas, linker invariant (feature step ≤ v_max·Δt + 1 px), median centroid speed < v_max, valid phase labels

## 10. Definition of Done

| Criterion | Result |
|---|---|
| One real Indian event works | ✅ E8, 14 May 2026, 48 frames |
| Reproducible preprocessing works | ✅ bit-identical reruns; hashes recorded |
| Real cells detected | ✅ 2,920 features, 613 cells |
| Cells tracked through time | ✅ 181 cells ≥ 2 h; linker invariant tested |
| Lifecycle output produced | ✅ per-frame and per-cell tables incl. growth/decay, phases (rules v0), merge/split families |
| Figures generated from real data | ✅ 4 figures |
| No synthetic/random data | ✅ none in the pipeline; unit-test fixtures are arithmetic checks only |
| Provenance documented | ✅ [`data/PROVENANCE.md`](../data/PROVENANCE.md) |
| Basic tests pass | ✅ 10/10 |

**Caveat carried forward:** the satellite source is a documented substitution (§8.1) that needs team approval.
