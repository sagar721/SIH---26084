# Data Reality — What We Can Actually Use

**Source:** research report Part 6 (verified 24–25 Sep 2026). Re-check any row marked NEEDS VERIFICATION before depending on it.

**Status legend:**

| Status | Meaning |
|---|---|
| **AVAILABLE** | Openly obtainable for our use now |
| **PARTIAL** | Obtainable, with limits on latency, period, coverage or sampling |
| **UNAVAILABLE / RESTRICTED** | Not usable without a licence or permission we don't have |
| **FALLBACK** | What we use instead of a restricted source |

**Standing rule:** never assume live IMD DWR or live lightning access. The UI and PPT always show them as not connected, unless access is formally granted and documented here.

---

## 1. Satellite

| Dataset | Status | Use in system | Limits | Access |
|---|---|---|---|---|
| Meteosat-9 IODC SEVIRI L1.5 (45.5°E; Meteosat-8 at 41.5°E before 1 Jun 2022) | **AVAILABLE** | **Primary training + LIVE input** (15-min archive from 2017-02-01; ~337k products) | Hourly when < 3 h latency; 15-min after > 3 h. ~3 km nadir → ~4–5 km over India (inference). Platform switch in 2022 (risk K2). File volume (K1, NEEDS VERIFICATION). Meteosat-9 EOL listed April 2027 (WMO OSCAR). | EUMETSAT account + `eumdac`; product `EO:EUM:DAT:MSG:HRSEVIRI-IODC` |
| INSAT-3DR / INSAT-3DS Imager L1B | **PARTIAL** | Event-day inputs; primary if MOSDAC access proves sufficient (D1) | Registered general users: "limited datasets", **3-day latency**; NRT only for privileged users. Which archives count as "limited" — **NEEDS VERIFICATION** (K6). | MOSDAC SSO + `mdapi.py` |
| INSAT derived products (OLR, HEM, CMV, LST) | **PARTIAL** | Optional features | Same access policy | MOSDAC |
| MOSDAC gallery images | **AVAILABLE (display only)** | Not used as model input | Rendered images, not calibrated data | Public web |

## 2. Radar

| Dataset | Status | Use | Limits | Access |
|---|---|---|---|---|
| IMD DWR raw volumes | **UNAVAILABLE / RESTRICTED** | Adapter interface only (PyScanCf → CfRadial) | Licence / MoES research request | Formal request via mentor (long shot) |
| IMD radar product images (`mausam.imd.gov.in/Radar/`) | **UNAVAILABLE for modelling** | Not used (optional display only, with attribution — team decision) | Not calibrated data; website terms, not a data licence | — |
| MOSDAC 3D Volumetric TERLS DWR | **PARTIAL** | **Radar case study E1** (stretch B "value of radar") | **May 1–31, 2018 only**, S. Kerala (6–11°N, 74–79°E); 1 km × 1 km × 250 m | MOSDAC Open Data (SSO) |
| ISRO SHAR S-band DWR | **NEEDS VERIFICATION** | Possible second radar case | Period/access unconfirmed in MOSDAC catalogue | MOSDAC (per IJRS 2024) |
| RainViewer tiles | **PARTIAL (display only)** | Not used | Past 2 h only; no availability guarantee; data owners can withdraw | Public API |
| **FALLBACK for radar** | — | Satellite IR/VIS cells + satellite precipitation (IMERG/GSMaP) + GPM DPR overpasses for 3D ice structure | — | — |

## 3. Lightning

| Dataset | Status | Use | Limits | Access |
|---|---|---|---|---|
| ISS-LIS (GHRC) | **PARTIAL** | **Lightning labels** (train 2017–2021, val 2022, test 2023) | Mission ended **16 Nov 2023**; overpass snapshots only (~90 s view per site) → labels exist only for cells under an overpass | NASA Earthdata |
| NRSC Lightning Detection Sensor Network (46 sensors) | **NEEDS VERIFICATION → treat as RESTRICTED** | Best Indian labels if granted | 2021 paper says 1-day lag on Bhuvan/NDEM; the NDEM URL returns 404 today; the Bhuvan portal requires login | Email NRSC via mentor |
| IITM ILLN / Damini (83 sensors) | **UNAVAILABLE / RESTRICTED** | — | Research request only | Email IITM via mentor |
| Blitzortung | **UNAVAILABLE (terms prohibit storm-warning use)** | **Never used** | — | — |
| WWLLN | **RESTRICTED (paid/academic)** | Only if a university licence exists | — | — |
| **FALLBACK for lightning** | — | ISS-LIS-verified P(lightning); where no label exists, a BT/OT **proxy** clearly labelled "proxy"; stretch: LightningCast transfer (GPL, isolated) | — | — |

## 4. Precipitation

| Dataset | Status | Use | Limits | Access |
|---|---|---|---|---|
| GPM IMERG V07 (Early/Late/Final) | **AVAILABLE** | Heavy-rain labels; "what happened" layer | 0.1° (~10 km), 30 min; Early ~4 h latency | Earthdata |
| GSMaP NRT / GSMaP_NOW | **AVAILABLE** (registration) | LIVE rain context; secondary labels | 0.1°; GSMaP_NOW realtime covers India via Meteosat since Nov 2018 | JAXA |
| IMD gridded rainfall (0.25° daily) | **PARTIAL** | Not used (too coarse in time) | Daily | IMD Pune |
| IMD AWS/ARG stations | **UNAVAILABLE / RESTRICTED** | — | Public portal locked May 2025; paid via dsp.imdpune.gov.in | — |
| **FALLBACK for station rain/gusts** | — | IMERG/GSMaP; published station values quoted from IMD press/news for case studies (cited, not used as training data) | — | — |

## 5. NWP / reanalysis (environment features)

| Dataset | Status | Use | Limits | Access |
|---|---|---|---|---|
| ERA5 | **AVAILABLE** | Training environment features | 0.25°, hourly; ~5-day latency | CDS + `cdsapi` |
| IMDAA (NCMRWF) | **PARTIAL** | Optional Indian reanalysis features (good optics with NCMRWF) | 12 km, **1979–2020 only** | NCMRWF RDS registration |
| GFS 0.25° | **AVAILABLE** | **LIVE** environment features | ~10 days on NOMADS; older via NCEI/AWS | Open |
| ECMWF IFS open data | **AVAILABLE** | Optional LIVE features | 0.25° | Open, CC-BY-4.0 |
| NCMRWF NCUM-G/R, NEPS | **NEEDS VERIFICATION** | Future 2–6 h blending | Public NRT availability unclear | NCMRWF data portal |

## 6. Hail / severe ground truth

| Dataset | Status | Use | Limits |
|---|---|---|---|
| IMD NW-India hailstorm report (PDF, updated 16 May 2026) | **AVAILABLE** | **Hail evaluation** (2026) + replay E8/E9 | Feb–May 2026; NW India only; station/town names (geocoding needed); reports incomplete → FAR not fully measurable. **Archive a copy now** — the PDF may be overwritten. |
| GPM DPR 2A (flagHeavyIcePrecip / flagGraupelHail) | **PARTIAL** | Hail-potential training labels | Overpass sampling only |
| News / NDRF / press reports (E2–E7) | **PARTIAL** | Event T0 and impact for replay (cited) | Not systematic; not training labels |

## 7. Static / GIS

| Dataset | Status | Use |
|---|---|---|
| SRTM / CartoDEM | **AVAILABLE** | Slope/terrain features, hillshade |
| District boundaries (Census / Bhuvan WMS / OSM) | **AVAILABLE** (licence per source — NEEDS VERIFICATION for the chosen file) | Places layer |
| OSM towns | **AVAILABLE** (ODbL, attribution) | Town buffers for ETA |
| IMD DWR network metadata (Figshare/GitHub) | **AVAILABLE** | Radar coverage rings (informational) |

## 8. Development-only data

| Dataset | Status | Use |
|---|---|---|
| SEVIR (AWS open data) | **AVAILABLE** | Pipeline debugging / pre-training experiments only. **Never reported as Indian skill.** |

## 9. Summary for slides

| Input named in the PS | Reality | What we do |
|---|---|---|
| DWR reflectivity/velocity | Restricted | Satellite-first; TERLS 2018 radar case; DWR adapter ready |
| INSAT-3D/3DR IR | Partial (3-day latency for general users) | Replay mode + Meteosat-9 IODC as primary/live |
| Ground lightning network | Restricted | ISS-LIS labels (2017–2023) + clearly labelled proxy; access requested |
| NWP/model data (implied) | Available (ERA5/GFS/ECMWF; IMDAA to 2020) | Environment features |
