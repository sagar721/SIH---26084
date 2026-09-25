# 48-Hour Immediate Action Plan (25–27 Sep 2026)

**Objective:** by hour 48, have accounts, real data on disk, a first tracked-cell figure, and a PPT draft. The idea deadline is **30 Sep** (VERIFIED). **Target submission is 29 Sep** (one-day buffer).

Owners use the workstreams from decision D8. Assign names in the first stand-up.

| Code | Workstream |
|---|---|
| DA | Data |
| TR | Tracking/ML |
| VA | Validation |
| BE | Backend |
| FE | Frontend |
| PP | PPT/Demo |
| TL | Team lead |

## Hours 0–4 — unblock

| # | Task | Owner | Done when |
|---|---|---|---|
| 1 | Confirm the team is nominated by the college SPOC and the team leader has portal login | TL | Screenshot of the portal team page |
| 2 | Download the official Idea PPT template (`SIH2026-IDEA-Presentation-Format.pptx`) | PP | File in `docs/ppt/` |
| 3 | Open accounts: EUMETSAT, NASA Earthdata, Copernicus CDS (instant); MOSDAC SSO, JAXA GSMaP, NCMRWF RDS (may take days) | DA | Account table in `data/PROVENANCE.md` |
| 4 | **Archive the IMD NW-India hail report PDF** with its download date | DA | `data/raw/hail_reports/hailstorm_report_2026-05-16.pdf` + sha256 |
| 5 | Create the repo with the ARCHITECTURE §9 layout (empty), `.gitignore` for `data/` and `.env`, Apache-2.0 licence (D5) | BE | First commit |
| 6 | Python env: satpy, pyresample, xarray, zarr, tobac, pysteps, MetPy, eumdac, cdsapi, earthaccess, lightgbm | TR | `environment.yml` resolves |

## Hours 4–16 — real data for one event

| # | Task | Owner | Done when |
|---|---|---|---|
| 7 | Pick the proof event: **E8 (14 May 2026 hail)** by default; E4 if SEVIRI retrieval for E8 fails | TL | Decision logged |
| 8 | Download SEVIRI IODC for T0 ± 6 h (15-min). **Record bytes per slot** (risk K1); try Data Tailor crop/channel subset | DA | Files on disk + size note in `REVIEW_AND_SCOPE` risk K1 |
| 9 | Download ERA5 (CAPE, CIN, winds 850/500 hPa, TCWV) for the event day | DA | NetCDF on disk |
| 10 | Download IMERG (Late/Early) half-hourly for the event window | DA | Files on disk |
| 11 | Check MOSDAC: can a general user get INSAT-3DS L1B for 14 May 2026? (K6) | DA | Yes/no + screenshot |
| 12 | Geocode the hail-report stations for 14 May 2026 | VA | CSV (station, lat, lon, source) |

## Hours 16–32 — first science

| # | Task | Owner | Done when |
|---|---|---|---|
| 13 | satpy load → 10.8 µm BT → resample to the 2 km LAEA grid (PRD F2) | TR | Zarr + quick-look PNG |
| 14 | tobac detection (thresholds 273/253/235/221/208 K) + watershed + linking on the window. Fallback: pySTEPS T-DaTing | TR | Tracks table; cell ID overlay PNG |
| 15 | Compute cooling rate (ΔBT 15 min); apply the phase rule table v0 | TR | Lifecycle curve PNG for one hail-producing cell |
| 16 | Overlay hail-report stations + IMERG max rain on the tracked cells | VA | Figure: cells × reports × rain |
| 17 | pySTEPS extrapolation of BT for one issue time (baseline preview, **no metrics claimed**) | TR | Side-by-side PNG |

## Hours 32–48 — PPT draft + review

| # | Task | Owner | Done when |
|---|---|---|---|
| 18 | PPT draft in the official format: problem → data reality (DATA_REALITY §9 table) → architecture A/B → differentiation vs RDT/TRT/ProbSevere → validation plan → real figures (from #14–#17) → limitations → roadmap | PP | Draft v1 |
| 19 | Evidence audit: every claim tagged; no metric we haven't computed; no "novel lifecycle" claim | VA | Checklist signed |
| 20 | Mentor/faculty review (meteorology if possible) | TL | Feedback notes |
| 21 | Close decisions D1–D4, D8 | TL | `REVIEW_AND_SCOPE.md` §5 updated |

**After hour 48:**
- Finalise the PPT (day 3–4); team leader submits by **29 Sep**.
- Then start ROADMAP Phase 2.

**Stop conditions / escalation:**
- EUMETSAT download blocked for > 6 h → switch to MOSDAC INSAT (if accessible) or use another EUMETSAT access path (NEEDS VERIFICATION).
- tobac not producing sensible cells by hour 28 → use threshold + connected components for the proof figures, labelled as such.
- SPOC nomination missing at hour 4 → escalate to the college immediately. Nothing else matters if the team isn't nominated.
