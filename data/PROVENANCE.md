# Data Provenance

Generated from the download manifests (`data/raw/*/manifest.json`, `report_manifest.json`). Raw files are git-ignored; this file is tracked.

## Accounts / access status (checked 24–25 Sep 2026)

| Source | Status | Note |
|---|---|---|
| NOAA/NCEP/CPC merged IR (`ftp.cpc.ncep.noaa.gov/precip/global_full_res_IR/`) | **AVAILABLE — anonymous HTTPS** | Used for Phase 1. Rolling archive observed from 2026-03-30 to present (older files not on this server: NEEDS VERIFICATION of long-term archive, e.g. NASA GES DISC GPM_MERGIR). |
| EUMETSAT Data Store (SEVIRI IODC) | Search is public; **download returned HTTP 404 without a token** | Needs EUMETSAT account + API key (not on this machine). Product size from API metadata: ~185,239 KB (~181 MB) per full-disk 15-min slot → ~17 GB/day uncropped (risk K1). |
| MOSDAC (INSAT-3DR/3DS) | No credentials on this machine | NEEDS account (D1/K6) |
| NASA Earthdata / Copernicus CDS / JAXA | No credentials on this machine | Not needed for Phase 1 |
| IMD RMC New Delhi hail report | **AVAILABLE — public PDF** | Archived with SHA-256 |
| OpenStreetMap Nominatim | **AVAILABLE** (usage policy: ≤ 1 req/s, identifying User-Agent) | Geocoding only; © OpenStreetMap contributors, ODbL |

## Satellite IR — NOAA/NCEP/CPC Globally Merged IR

- Product: globally merged ~10.7–11 µm window-channel brightness temperature from geostationary satellites; 4 km (0.03638°), 30 min, 60°S–60°N.
- Descriptor: `merg_4km-pixel.ctl` (1-byte, BT−75 K, 255 = missing, rows north→south).
- Satellite over the whole Phase-1 domain on 14 May 2026: satellite-ID code **5** in `geomerg_satid_202605.Z` (code → satellite mapping not given in the descriptor: NEEDS VERIFICATION; expected to be Meteosat IODC).
- Licence: US Government (NOAA) work; no access restriction observed. Formal licence/attribution statement for this server: NEEDS VERIFICATION.
- Files: 25 (677.5 MB total).

| File | Bytes | SHA-256 | HTTP Last-Modified | Downloaded (UTC) |
|---|---|---|---|---|
| `geomerg_satid_202605.Z` | 3,401,509 | `dc1b4702544e470fd1881406882dffd6b2a899867ad6833617b90eaf8ee95f30` | Mon, 01 Jun 2026 05:56:07 GMT | 2026-09-24T19:36:38+00:00 |
| `merg_2026051400_4km-pixel.Z` | 26,724,209 | `fb3c1a5571b829ecace946d7445cb736a00e8fc79541eeac522a0719d823072a` | Sat, 16 May 2026 00:06:32 GMT | 2026-09-24T19:27:30+00:00 |
| `merg_2026051401_4km-pixel.Z` | 26,827,543 | `744e5d48a3030fb39d7ae2d2d5b62c262f4fc3bd043a08db3e2e135c9879a1ee` | Sat, 16 May 2026 00:06:32 GMT | 2026-09-24T19:28:41+00:00 |
| `merg_2026051402_4km-pixel.Z` | 27,159,575 | `2402419738518b3e03580674412e74686ad0fc7e604d372ac65cdb511d71eeeb` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:29:53+00:00 |
| `merg_2026051403_4km-pixel.Z` | 27,187,415 | `fd23545412bbf20ef28aa331186de9baa7da657e83625ba6f99b9184485ea627` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:31:03+00:00 |
| `merg_2026051404_4km-pixel.Z` | 27,518,439 | `3b2ea6b0eca11067a2302a3a746e6586332784ee7d3f6b1ddac1158fab1561f2` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:32:53+00:00 |
| `merg_2026051405_4km-pixel.Z` | 27,727,833 | `9aabecd63345f5e22be9f2b0726278b20816989e7f3395e9b1809be9f8dcf8c2` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:32:51+00:00 |
| `merg_2026051406_4km-pixel.Z` | 27,783,701 | `0df4408735ac465e17c188fd9141c68a1ebdc8e83df785d919b9ca2e45fa95e4` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:32:51+00:00 |
| `merg_2026051407_4km-pixel.Z` | 28,407,231 | `762f33385d2c49ec51729133f7922f4e709f76383950202fe9e778dcc890e01a` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:32:56+00:00 |
| `merg_2026051408_4km-pixel.Z` | 28,825,051 | `09a24a5f7e4a3e4a056a07e8f3663becc8d674ec0d024b71d69626c5b7ad5ef9` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:32:55+00:00 |
| `merg_2026051409_4km-pixel.Z` | 28,952,209 | `23b848d9dd97eded91ef20cbc4fa4be994f4c6de442b8928d0d95661895c481b` | Sat, 16 May 2026 00:06:33 GMT | 2026-09-24T19:32:56+00:00 |
| `merg_2026051410_4km-pixel.Z` | 28,968,495 | `0170860f163be995f601b4159dc6a80abd86b92e8babc860d28d69a10b93ad8d` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:34:07+00:00 |
| `merg_2026051411_4km-pixel.Z` | 28,880,491 | `2201bfac982be500eb5bc996b86cd82319c96f94cbd9f733915ecce63a6bdc6d` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:34:04+00:00 |
| `merg_2026051412_4km-pixel.Z` | 28,606,841 | `78ed6549eb5b6e9caf454409319641572e88fac6fdb55a6504f6021af20cafec` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:34:06+00:00 |
| `merg_2026051413_4km-pixel.Z` | 28,635,805 | `cce43a6a89a59d9695747448fed945faf45491bb74d03fd72f1d0916e899361e` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:34:11+00:00 |
| `merg_2026051414_4km-pixel.Z` | 28,291,667 | `905c5235eca210b3ee5d0b3e84d83e17b491344f72ebb13b7492f1d2fd395ef6` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:34:09+00:00 |
| `merg_2026051415_4km-pixel.Z` | 28,490,661 | `35a10b9361eb31bbb73b605120db24dc032bbc9bfb3b76210c8034606b16f609` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:34:07+00:00 |
| `merg_2026051416_4km-pixel.Z` | 28,358,835 | `09876c01ca38d6aca0d4909c4e7d74383857a99cadcb7c44b04d1a6054bcbd8b` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:35:18+00:00 |
| `merg_2026051417_4km-pixel.Z` | 28,559,589 | `863612493759735b7091fb4b8b02f98bd0ab9bf725e97a437a10df271292eb6a` | Sat, 16 May 2026 00:06:34 GMT | 2026-09-24T19:35:23+00:00 |
| `merg_2026051418_4km-pixel.Z` | 28,501,537 | `1c91abc56947d4d800f335d54433998a926a7c4f3d0adb4d5d764975d2ae29fb` | Sat, 16 May 2026 00:06:35 GMT | 2026-09-24T19:35:17+00:00 |
| `merg_2026051419_4km-pixel.Z` | 28,287,477 | `34abbc6801c9681df66e77b57ce5ea3e62f927b3bd15a94c76706bb30b694905` | Sat, 16 May 2026 00:06:35 GMT | 2026-09-24T19:35:20+00:00 |
| `merg_2026051420_4km-pixel.Z` | 28,173,367 | `b58f9663c08d350b7f8b8baab6acd0cc56883c86a47bbc718d7b8835cfdcccbb` | Sat, 16 May 2026 00:06:35 GMT | 2026-09-24T19:35:22+00:00 |
| `merg_2026051421_4km-pixel.Z` | 27,961,813 | `b4906e3ac9becba629b006a737af31c789728d11145719ad95570d9296569ae5` | Sat, 16 May 2026 00:06:35 GMT | 2026-09-24T19:35:23+00:00 |
| `merg_2026051422_4km-pixel.Z` | 27,848,829 | `915ae6c7ed0b9febf9cada54b5b89a1fb0871e65f6889c94b7f533882061ba1d` | Sat, 16 May 2026 00:06:35 GMT | 2026-09-24T19:36:24+00:00 |
| `merg_2026051423_4km-pixel.Z` | 27,459,785 | `066337f690a9744e9790824b79e00fb7e589a595426328439e6d6236d12121d7` | Sat, 16 May 2026 00:06:35 GMT | 2026-09-24T19:36:27+00:00 |

## Ground truth — IMD hail report

- URL: https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf
- HTTP Last-Modified: Sat, 16 May 2026 10:37:35 GMT; bytes 59,837; SHA-256 `face59166ab1c47ec8979e687d9e6b7307dc0410d765f9217242f495a0556798`
- Archived at `data/raw/hail_reports/hailstorm_report_face59166ab1.pdf` on 2026-09-24T19:26:26+00:00
- Row used: `14-05-2026`. Geocoded places (OSM Nominatim):

| Name (printed) | Query | Lat | Lon | Status |
|---|---|---|---|---|
| Sonmarg (Sonmarg) | Sonmarg, Jammu and Kashmir, India | 34.302387 | 75.2965551 | OK |
| Ganderbal (Ganderbal) | Ganderbal, Jammu and Kashmir, India | 34.2889322 | 75.0407983 | OK |
| Shopian (Shopian) | Shopian, Jammu and Kashmir, India | 33.718807 | 74.8333311 | OK |
| Kulgam (Kulgam) | Kulgam, Jammu and Kashmir, India | 33.6446899 | 75.0188432 | OK |
| Shirsi (Shirsi) | Shirsi, Uttarakhand, India | — | — | NOT_FOUND |
| Bageshwar (Bageshwar) | Bageshwar, Uttarakhand, India | 30.0087902 | 79.9280183 | OK |
| Chamoli (Chamoli) | Chamoli, Uttarakhand, India | 30.4985956 | 79.6190537 | OK |
| Amritsar (Amritsar) | Amritsar, Punjab, India | 31.6356659 | 74.8787496 | OK |
| Ambala (Ambala) | Ambala, Haryana, India | 30.3843674 | 76.770421 | OK |
| Gurugram (Gurugram) | Gurugram, Haryana, India | 28.4646148 | 77.0299194 | OK |
| Bahadurgarh (Bahadurgarh) | Bahadurgarh, Haryana, India | 28.6933239 | 76.9332373 | OK |
| Bareilly (Barely) | Bareilly, Uttar Pradesh, India | 28.4582345 | 79.4047452 | OK |
| Prayagraj (Prayagraj) | Prayagraj, Uttar Pradesh, India | 25.4381302 | 81.8338005 | OK |
| Varanasi (Varanasi) | Varanasi, Uttar Pradesh, India | 25.3356491 | 83.0076292 | OK |
| Unnao (Unnao) | Unnao, Uttar Pradesh, India | 26.5673264 | 80.6198193 | OK |
| Churu (Churu) | Churu, Rajasthan, India | 28.2047781 | 74.6912996 | OK |

## Derived products

| Product | Path | Region | Resolution |
|---|---|---|---|
| BT cube (QC'd, gap-flagged) | `data/interim/grid2km/E8_20260514.nc` | LAEA box enclosing 26–34°N, 72–84°E (453×603 px); `in_domain` mask for the lat/lon box | 2 km grid (effective ~4 km), 30 min, 00:00–23:30 UTC |
| Tracking outputs | `data/processed/E8_20260514/` (`features.parquet`, `mask.nc`, `merge_split.json`, `cells_per_frame.csv`, `cells_summary.csv`, `run_summary.json`) | same | same |
| Figures | `data/figures/E8_20260514_fig*.png` | same | — |

## Phase 2 — baseline forecasts (added 2026-09-24)

No new data acquired. Inputs are Phase-1 outputs (hashes below, from `data/processed/E8_20260514/baseline/baseline_provenance.json`).

| Input | SHA-256 |
|---|---|
| `data/interim/grid2km/E8_20260514.nc` | `fac2de11ff0ad8a19266e8bca70215bcfbc3762875e940a0e0f974784ee41d3f` |
| `data/processed/E8_20260514/features.parquet` | `66bd9b4bbb6ce91ce8a2ff5b2c2049b7ffaa99cd8df2b53a3cb1f1e6e2592b70` |
| `data/processed/E8_20260514/mask.nc` | `0e9963ca60fcd1d907e38df0f3e3079509f24a01813dfee11fafb8822c92fac2` |
| `config/baseline.yaml` | `8e233b604e1c20ebe32a0c1cf0062fe1d2a62134d8746a6cff96f0ffdd774eed` |

| Output | SHA-256 |
|---|---|
| `baseline/grid_metrics_by_lead.csv` | `7083accfbc8b382f707d583442dcd7002c415a825445446b2ea260d7c550a580` |
| `baseline/grid_metrics_per_issue.csv` | `a5d4dcdb775b3723b16fc0c3ecfa33728c8fd00fbe6650f2459ed2067e52d100` |
| `baseline/object_metrics_by_lead.csv` | `d1039b827aef335de8f5938f87fccb8fcb54dc4d3ca88acc00694c220540aea1` |
| `baseline/object_predictions.csv` | `0539bdf9e0a18491d4c1e1402a189dafe5f82d9333137ba066093e37830dec6e` |

- Issue times: 45 (2026-05-14 01:00:00 … 2026-05-14 23:00:00 UTC); leads 30–360 min.
- Fitted parameters: none (baselines only; no training, no tuning).
- Versions: pysteps 1.21.5, opencv-python-headless 5.0.0.93, numpy 2.4.6, scipy 1.17.1, xarray 2026.7.0, tobac 1.6.2.
- Build note: pysteps 1.21.5 built from the PyPI sdist with -fopenmp removed from setup.py (Apple clang has no OpenMP); affects only multithreading of the Proesmans/VET C extensions, which are not used here. Lucas-Kanade and semi-Lagrangian code paths are unmodified.
- Region/resolution: as Phase 1 (2 km LAEA grid, effective ~4 km, 30 min).

## Phase 3 — tracking audit (added 2026-09-24)

No new data acquired. Inputs: Phase-1 `features.parquet`, `mask.nc`, cube; Phase-2 `baseline/advection_forecasts.nc` (motion fields). Phase-1 lifecycle tables and Phase-2 grid metrics are unchanged (hash-tested).

| Output | SHA-256 |
|---|---|
| `tracking_v2_none/cells_per_frame.csv` | `f9e522331855e199b12be3b6496e0c5f7d03e9076bf0aafdf6f61d1660269ec2` |
| `tracking_v2_none/cells_summary.csv` | `965e7061c7009e05518a1b1156521ed7bc5841bde8cbef3b27254a926cc7429c` |
| `tracking_v2_none/genealogy_events.csv` | `64800e93b74681d6ea2bc391ec8f8d067995b3d46204af66ce0bbb21d8131c4e` |
| `tracking_v2_none/object_metrics_by_lead.csv` | `397a3eda520b6bc894dbec184030685dac2862f447d25086773ff7655af98143` |
| `tracking_v2_none/object_paired_comparison.csv` | `c4a65fd138d0a04bce78a79ed915b246db77c5abc0d952e0afbf465fa9e6f6f3` |
| `tracking_v2_none/object_predictions.csv` | `595c9f5177f3f1ce10310db3bb3075dec564bcecb81a47766a4dfb9b3c523242` |
| `tracking_v2_flow/cells_per_frame.csv` | `fb0869262b562978530e2e910dac131d5c606762d55704389c83e8e13030ab7d` |
| `tracking_v2_flow/cells_summary.csv` | `02bbf0d8dad6da60b7173145175de1fa8a08e9fee756440a6b22d3baec5055b7` |
| `tracking_v2_flow/genealogy_events.csv` | `90b8c70e98a35b41d1ac3cd9369de38343ec6d9b35e4f514da1b6497bb6756d5` |
| `tracking_v2_flow/object_metrics_by_lead.csv` | `fb5de3447af81af567f4a31d18d4a75b4e14999ec02238c49b5d411cc554dac5` |
| `tracking_v2_flow/object_paired_comparison.csv` | `a4ac34ad5a12696ea837dd65549ddaa309ad23b6a9e2aca8abf4b7ce67fee161` |
| `tracking_v2_flow/object_predictions.csv` | `1644def19526960e80e6c3b09dc5e8f3cfd917b32dc4596e7e75d176a3d9e522` |
| `audit/audit_v1.json` | `a1de37c5b14aad9eb356107602b0310d563538398d0bac0f5afc9ed48806b5a0` |
| `audit/audit_v2_flow.json` | `f8ece4a0822f55a74d14f7a6f43ee6ca2a562b9b7d0fc7474bda4b1746f5ac74` |
| `audit/audit_v2_flow_ov0.1.json` | `0e0757b7248b2013818c4fba679fad79294edf2946b308b78aa45e95adbc725e` |
| `audit/audit_v2_flow_ov0.3.json` | `6ded21b2862e4e4a4d43cee45c6631e3f273d74ac4f678365ed563455bd675e4` |
| `audit/audit_v2_none.json` | `c0e8f98c059ff573f0014e97b729b924c5a54efbe0947ed555b2d7caa39a6456` |
| `audit/audit_v2_none_ov0.1.json` | `4abc49de779412c1bdd4e8d2bfaa0de5059d50bd06ca7a7af35071b2bb5ee4fb` |
| `audit/audit_v2_none_ov0.3.json` | `f9ac6d400129ef6b09351489268ff998eb263fa5641a7c737732527adf91451e` |

- Config: `config/tracking_v2.yaml` (objects = cold segments < 245 K, overlap linking min 0.2, coldness-weighted centroid, min 2 frames). Primary = `tracking_v2_none`; `tracking_v2_flow` and `*_ov0.1/_ov0.3` are sensitivity runs.
- Input hashes (from `tracking_v2_none/run_summary.json`): `E8_20260514.nc` fac2de11ff0a…; `features.parquet` 66bd9b4bbb6c…; `mask.nc` 0e9963ca60fc…; `advection_forecasts.nc` 2dacecb15097…; `tracking_v2.yaml` 4126666c0c5f…; `baseline.yaml` 8e233b604e1c….
- Region/resolution unchanged (2 km LAEA grid, effective ~4 km, 30 min).

## Phase 4 — multi-event validation (added 2026-09-25)

- Source: same NOAA/NCEP/CPC merged IR archive (no new source). New raw files: 72 hourly files for 2026-05-01, 05-04, 05-16, each with URL, Last-Modified, size and SHA-256 in `data/raw/cpc_merged_ir/manifest.json`.
- April 2026 not on the archive (HTTP 404, checked 2026-09-25), so E9 (5 and 9 Apr) could not be used.
- Hail context: same archived IMD PDF (sha face5916…); geocoding cached in `data/raw/hail_reports/geocoded_2026-05-{01,04,16}.json` (OSM Nominatim).
- Pipeline changes: `config/tracking.yaml` gains `subnetwork_size_max: 50` (trackpy solver cap; E8 re-tracked byte-identically); `shifted_iou` off-grid fix. No threshold or baseline setting changed.
- `config/baseline.yaml` sha256 `8e233b604e1c20ebe32a0c1cf0062fe1d2a62134d8746a6cff96f0ffdd774eed` (identical in every event's baseline provenance); `config/tracking.yaml` `49623395106cbdd4…`; `config/tracking_v2.yaml` `4126666c0c5fd279…`.
- Events used: E8_20260514, E10_20260504, E11_20260516; excluded by the suitability rule: E8a_20260501.

| Event | Cube SHA-256 (first 16) |
|---|---|
| E8_20260514 | `fac2de11ff0ad8a1` |
| E8a_20260501 | `75fc191136a91f9e` |
| E10_20260504 | `efa2a6fdb268d64f` |
| E11_20260516 | `49578d3465a44599` |

| Output (`data/processed/multi_event/`) | SHA-256 (first 16) |
|---|---|
| `cross_event_by_lead.csv` | `aa0893b169772db1` |
| `decay_by_event.csv` | `b72b42397dfc9720` |
| `event_block_bootstrap.csv` | `8aeeec6d2810fe96` |
| `event_metrics_by_lead.csv` | `ead7a26add0a2e15` |
| `event_qc.csv` | `edd2063a257018d6` |
| `object_diagnostics_by_event.csv` | `fed5b142b0b4b397` |

Bootstrap: 1000 resamples, seed 20260925, 12-issue-time circular blocks (within event); whole event days (across events). Details: `docs/MULTI_EVENT.md`.

## Phase 5 — decay-aware forecast: decomposition and stop decision (added 2026-09-25)

- No new data. Inputs: Phase-1 cubes and Phase-3 v2 lifecycle tables of E8, E10, E11 (hashes in the JSON files below); `config/baseline.yaml` sha256 `8e233b604e1c20ebe32a0c1cf0062fe1d2a62134d8746a6cff96f0ffdd774eed` (unchanged).
- Nothing fitted. The ORACLE area-matched CSI uses the observation and is a bound, not a forecast.
- Lifecycle gate: rule 'build only if a tendency on the development event E8 has phi > 0 with 95 % cell-bootstrap CI excluding 0'; decision **STOP**; cell bootstrap n=1000, seed 20260925.
- No decay-aware forecast was built, frozen or scored (Phase-5 stop clause). Details: `docs/DECAY_AWARE.md`.

| Output (`data/processed/multi_event/phase5/`) | SHA-256 (first 16) |
|---|---|
| `decomposition_per_issue.csv` | `3d7079ef9b29564b` |
| `decomposition_by_lead.csv` | `b0e6cab8abce6943` |
| `decomposition_by_issue_block.csv` | `44e1eb338ba436a2` |
| `lifecycle_reliability.csv` | `a3055872ad335ce5` |
| `lifecycle_phase_outcomes.csv` | `209fc1be3927523d` |

## Phase 6 — ML forecast prototype ml-v0 (added 2026-09-25)

- Source: same NOAA/NCEP/CPC merged-IR archive; new raw files for 2026-05-06..12 and 2026-05-18..31 (504 hourly files) recorded in `data/raw/cpc_merged_ir/manifest.json` (URL, Last-Modified, bytes, SHA-256). Downloader now resumes broken transfers (HTTP Range, size check) and locks the manifest across processes.
- Config `config/ml_dataset.yaml` sha256 `bda7c3859a93474d9329286e905a58f8a76dba6af2acf6bdc848d7e0628fe4f4`; `config/baseline.yaml` `8e233b604e1c20eb…` (unchanged).
- Dataset manifest `data/processed/ml_dataset/dataset_manifest.json` sha256 `9e66e49a1485e3bd…`: 21 days, cube and parquet SHA-256 per day; forbidden days 2026-04-30, 2026-05-01, 2026-05-02, 2026-05-03, 2026-05-04, 2026-05-05, 2026-05-13, 2026-05-14, 2026-05-15, 2026-05-16, 2026-05-17.
- Model `data/models/ml-v0/`: model.joblib `597e3c06c5db7ec2…`, calibrators.joblib `0da01eb8bd2f3598…`; n_iter 216; sklearn 1.9.1; gate PROCEED.
- Test events scored once with the frozen model (E8, E10, E11); tables re-derived with `--resummarise` (no new predictions).

| Output (`data/processed/ml_eval/ml-v0/`) | SHA-256 (first 16) |
|---|---|
| `bootstrap_ml_vs_pysteps.csv` | `7c071db6e4c89f58` |
| `metrics_by_event_lead.csv` | `929318a725ed5068` |
| `metrics_by_issue_block.csv` | `0f7e125566c29be8` |
| `metrics_edge_only.csv` | `135fa7ba89fc99b3` |
| `metrics_pooled_lead.csv` | `8db86e356b537943` |
| `per_issue.csv` | `ecc8350dba52cc3d` |
| `reliability.csv` | `f41cdc48483e124e` |

## Phase 7 — evidence freeze (added 2026-09-25)

- Frozen model **ml-v0**: model.joblib `597e3c06c5db7ec2f6c9e7e847b49a7743949a1a69a01ca20285d56c52f51857`, calibrators.joblib `0da01eb8bd2f35988141c5fdcab03658bcc6e4136bfb2299a85a72a7aacc1bc7`, model_card.json `2a763b0aaeae985834bf22fc47b2e6d0fa367975892759439c94049c2f29728e`.
- Config `config/ml_dataset.yaml` `bda7c3859a93474d9329286e905a58f8a76dba6af2acf6bdc848d7e0628fe4f4`; dataset manifest `9e66e49a1485e3bda6c9e051ba58937d43a11bbc1591f67367fab8e5db9459fe`; evaluation provenance `d2dadac4140240f0a9eb255a2d13c86543f88685fa30cbc9efddc5b50bc32784`.
- Freeze manifest `docs/FREEZE_ml-v0.json` sha256 `b5c48807bab48dccab1706d6d2bc144260cd4f3249dc533b09647323d653fe35`: 386 files (code, configs, raw manifests, cubes, processed outputs, model, figures, docs), frozen at 2026-09-25T07:26:44+00:00.
- Test suite at freeze: 66 passed, 1 skipped in 62.54s (0:01:02) (excluding the freeze guard); `tests/test_phase7_freeze.py` re-hashes all frozen files.
- No model, dataset, threshold or result was changed in Phase 7; `docs/FINAL_CLAIMS.md` and `docs/FINAL_RESULTS.md` only quote frozen files.

## Phase 8 — product prototype (added 2026-09-25)

- No frozen file modified (tests/test_phase7_freeze.py passes after Phase 8). New code only: `pipelines/replay/build_bundle.py`, `apps/web/`, `tests/test_phase8_bundle.py`.
- Replay bundles are derived display products of frozen files; each bundle's `manifest.json` lists its inputs with SHA-256 (verified against `docs/FREEZE_ml-v0.json` at build time) and every output file's SHA-256.

- `E8_20260514`: bundle manifest sha256 `3e8fb26731e86fac…`, 20 frozen inputs, 735 output files.
- `E10_20260504`: bundle manifest sha256 `f288ed49184df318…`, 20 frozen inputs, 735 output files.
- `E11_20260516`: bundle manifest sha256 `2919ff0f60b1b6f5…`, 20 frozen inputs, 735 output files.
- Basemap: CARTO light raster tiles (© OpenStreetMap contributors © CARTO), display context only, not used in any result.

- 2026-09-25 local-run check: basemap switched from CARTO (tiles now watermark "API KEY REQUIRED") to Esri World Light Gray Canvas (display context only); MapLibre request-cancellation AbortErrors filtered. No bundle or frozen file changed.
