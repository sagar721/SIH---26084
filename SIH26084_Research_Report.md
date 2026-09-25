# SIH26084 — Convective-Scale Nowcasting (0–6 h): Deep Research Report

**Prepared:** 25 September 2026 · **Status of evidence:** live web + GitHub API + official SIH portal/guidelines, fetched 24–25 Sep 2026

**Legend used throughout**

| Tag | Meaning |
|---|---|
| **[V]** | VERIFIED FACT — checked against the linked source during this research |
| **[I]** | INFERENCE — my reasoning from verified facts; could be wrong |
| **[P]** | PROPOSED IDEA — a design recommendation, not a fact |
| **[U]** | UNVERIFIED — plausible but I could not confirm it; check before relying on it |

---

## ⚠️ READ FIRST — three things that change your plan

1. **The idea-submission deadline is 30 September 2026 — 5 days from today.** [V] The official PS page lists `30 September 2026` against SIH26084, and the SIH 2026 Guidelines say: *"The last date for team nomination and idea submission by College SPOC and Team leader on SIH portal is till 30th Sept 2026 only. No request will be entertained after the deadline."* ([sih.gov.in/sih2026PS](https://sih.gov.in/sih2026PS), [SIH 2026 Guidelines PDF](https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf)). An older scraped copy of the PS list (22 Aug) showed 20 Sept, so the deadline was extended once. The 30-day roadmap in Part M starts with a **5-day idea-PPT sprint**.
2. **There is no open, live Indian radar or lightning feed you can train on.** [V] IMD DWR raw data needs a licence/research request; IMD locked its AWS/ARG portal to the public in May 2025; Blitzortung's terms **forbid use in storm-warning systems**. (Sources in Part 6.) A credible design has to be **satellite-first, with radar and lightning used where data really exists**. Most competing student projects handle this by *simulating* radar and lightning. That is a weakness you can exploit.
3. **"Storm lifecycle intelligence" already exists in operational systems:** NWCSAF RDT-CW (development phases), MeteoSwiss TRT (severity rank), NOAA ProbSevere v3 (per-cell hazard probabilities, operational Aug 2025). [V] The idea is sound, but it is **not new as a concept**. What sets you apart has to come from *how* you do it for India and *how you prove it works* (Part 9).

---

# PART 1 — OFFICIAL PS ANALYSIS

## 1.1 Official source

- Official portal entry: [https://sih.gov.in/sih2026PS](https://sih.gov.in/sih2026PS) (downloaded 24 Sep 2026; the PS text is inside the modal for ID 26084). [V]
- Mirror, useful for diffing: [NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements](https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements) (snapshot 22 Aug 2026). [V]

## 1.2 FACT FROM OFFICIAL PS [V]

| Field | Official content |
|---|---|
| PS ID / Title | SIH26084 — "Convective scale nowcasting for Thunderstorms, Hail & Cloudbursts (0–6 hr)" |
| Organization / Dept | Ministry of Earth Sciences (MoES) / NCMRWF |
| Category / Theme | Software / Disaster Management |
| Motivation | Convective storms (severe thunderstorms, hail, downburst winds, cloudbursts) are among India's deadliest hazards, especially pre-monsoon and monsoon. NWP "often fail[s] to accurately capture these mesoscale extreme weather events" because the storms develop within minutes at scales that "slip through coarse grid resolutions". |
| Objective | "Build a real-time, convective-scale Nowcasting System (0–6 hour lead time) operating at a hyper-local 1–3 km spatial resolution." |
| Architectural mandate | "Participants must design a system rooted in Multi-Source Data Fusion architectures." |
| Core tasks | "Ingest high-frequency, heterogeneous meteorological streams, automatically detect early convective initiation, and dynamically forecast severe storm parameters (including lightning strike density, hail probability, downburst velocity, and cloudburst thresholds)." |
| Expected inputs | "Doppler Weather Radars (DWR – reflectivity and velocity fields), geostationary satellite imagery (INSAT-3D/3DR thermal/infrared bands), and ground-based lightning detection networks." |
| Expected outputs | "A real-time, interactive GIS-mapped dashboard showcasing high-resolution (1–3 km) hazard zones with live countdown clocks for storm arrivals." |
| Users named | Local administrations, aviation sectors, rural farming communities |
| Lead time | 0–6 h |
| Spatial resolution | 1–3 km |
| Temporal resolution | **Not stated** — only "high-frequency" streams |
| Hazards | Thunderstorms, lightning (strike density), hail (probability), downbursts (velocity), cloudbursts (thresholds) |
| Dataset link | **Empty** |
| YouTube link | **Empty** |
| Contact info | **Empty** |
| Evaluation criteria specific to the PS | **None stated** |
| Submission count (portal, 24 Sep 2026) | **9/500** |
| Deadline | 30 September 2026 |

## 1.3 YOUR INTERPRETATION (mine, labelled)

- **[I] The input list is aspirational, not a data offer.** The organizers give no dataset link. Judges who work with NCMRWF/IMD data every day know that students cannot get live DWR volumes or national lightning feeds. An honest *data-reality* section is likely to earn credibility, not lose marks.
- **[I] "0–6 h at 1–3 km" is physically hard.** Extrapolation-based cell nowcasts lose most of their skill after roughly 1–2 h. Beyond that, the literature blends in NWP or environment-conditioned ML (see Metzl et al. 2025, Global MetNet 2025, Stormscope 2026 in Part 5). A defensible system is **seamless**: object/cell nowcast for 0–2 h plus probabilistic area guidance for 2–6 h, with a **skill-vs-lead-time curve** shown openly.
- **[I] "Live countdown clocks for storm arrivals"** is the one concrete UI requirement. It implies per-location ETA, which requires *cell tracking* and not just gridded fields. That supports your lifecycle direction.
- **[I] "Detect early convective initiation"** is a separate task from nowcasting existing storms. It is where geostationary IR (cloud-top cooling) beats radar, because radar only sees a cell once precipitation forms.
- **[I] "Downburst velocity" and "cloudburst thresholds"** are the weakest-labelled hazards. There is no open Indian downburst dataset, and IMD's cloudburst definition (≈100 mm/h over ~20–30 km²) is finer than any open gridded rainfall product. Treat these as *potential/threshold indicators with stated limits*, not trained probabilities.
- **[I] Related PS in the same ministry:** SIH26072 (IMD) — "AIML based Nowcasting of thunderstorm and lightning using ... multiple radars, satellite, lightning and model data" (10/500), and SIH26077 — "AI-Driven Hyper-Local Early Warning System for Severe Weather Nowcasting" (31/500). [V] These overlap heavily with SIH26084, and their public repos are part of your competitive landscape.

---

# PART 2 — COMPETITION / SUBMISSION ANALYSIS

## 2.1 Verified numbers [V]

Parsed from the official PS page on 24 Sep 2026 ([sih.gov.in/sih2026PS](https://sih.gov.in/sih2026PS)):

| Metric | Value |
|---|---|
| SIH26084 submissions | **9 / 500** (you estimated ~10 — confirmed) |
| Number of PS on portal | 240 |
| Median submissions per PS | 49.5 |
| Mean submissions per PS | 84.2 |
| PS with fewer than 9 submissions | 2 |
| Total ideas across all PS | 20,202 |
| Related: SIH26072 (IMD nowcasting) | 10/500 |
| Related: SIH26077 (severe-weather nowcasting) | 31/500 |
| Related: SIH26085 (urban flood nowcasting, NCMRWF) | 88/500 |
| Related: SIH26068 (WeatherGPT, IMD) | 178/500 |

## 2.2 Shortlisting rules [V]

From the official [SIH 2026 Guidelines](https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf):

- *"4-5 teams per problem statement **may** be selected for the grand finale, but the final decision rests with the problem statement creating organization, which isn't obligated to declare a winner unless student proposals meet their expectations."* → Your "~5 teams" figure is **officially stated as 4–5, and as a possibility, not a quota.**
- *"Only 500 ideas will be submitted for a particular PS"*; counts are public; one team can submit to at most 2 PS.
- **Idea selection criteria:** *"novelty of the idea, complexity, clarity and details in the prescribed format, feasibility, practicability, sustainability, scale of impact, user experience and potential for future work progression."*
- Grand Finale: offline at nodal centres, *proposed* for **December 2026**.
- Prize: one winning team per PS, **Rs 1,50,000**, paid *"ONLY IF that organization likes the idea"*; not mandatory to announce a winner.
- IP of the winning idea is split between the PS organization and the team, or decided by mutual agreement.
- *"The ideas or solutions ... must be new and must not have been present in any previous event/program of any sort."*
- Idea submission requires the official **Idea PPT format** ([SIH2026-IDEA-Presentation-Format.pptx](https://sih.gov.in/letters/2026/SIH2026-IDEA-Presentation-Format.pptx)).

## 2.3 What the low count does and does NOT mean

**It does NOT mean:**
- **[I]** A high chance of selection. The bar is **absolute**: the organization can select nobody. You are judged against NCMRWF's expectations, not only against the other teams.
- **[I]** That the final count will stay low. Five days remain, and teams often submit near the deadline. Treat 9 as a floor.
- **[I]** That there are few competitors in the topic. At least **four public GitHub repos are explicitly labelled SIH26084** (VARSHANET, nowcasting_sih, Solvix, xarjunpatil — Part 4), and evaluators may see the overlapping IMD PS SIH26072 and SIH26077 teams.

**It probably DOES mean:**
- **[I]** Students see the PS as hard: meteorology knowledge plus inaccessible data. Evaluators will likely see a similar pattern — lots of UI and very little real verification. Real verification is therefore the clearest way to stand out.
- **[I]** Each submission will probably get more reviewer attention than in a 500-idea PS. Depth and honesty in the PPT should matter more.

## 2.4 What a strong SIH26084 submission needs to demonstrate [I/P]

Mapped to the official criteria:

| Official criterion | What would stand out here |
|---|---|
| Novelty | A clearly stated technical contribution relative to named prior art (RDT, TRT, ProbSevere, LightningCast), not "AI + map" |
| Complexity | Object-based tracking with merge/split, multi-hazard probabilities, calibrated uncertainty — built on real data |
| Clarity / details in format | A data-reality table (what's live, what's archived, what's proxied) and an architecture diagram that matches the code |
| Feasibility | Runs on a laptop or a free GPU; uses datasets you have already downloaded (show file counts and dates) |
| Practicability | Outputs in forms IMD/NCMRWF/NDMA use: CAP alerts, district polygons, IST timestamps |
| Sustainability | Uses ISRO/EUMETSAT/NASA open archives that will keep existing; plugs into IMD DWR if access is granted later |
| Scale of impact | India-wide satellite coverage, not one city; plus a targeted case (Kerala radar, NW-India hail) |
| User experience | A forecaster-facing replay ("what the system knew at T–30") rather than a consumer weather app |
| Future work | A clear path to add DWR volumes, NRSC/IITM lightning, NCUM-R fields |

**The single most important differentiator [I]:** a **verification table** showing your model against persistence and optical-flow baselines on held-out Indian events, with CSI/POD/FAR and reliability diagrams. None of the SIH26084/26072 repos I inspected has this on real observed labels.

---

# PART 3 — GITHUB LANDSCAPE

Metadata was pulled via the GitHub API on 24–25 Sep 2026 (stars, last push, language, licence). "NOASSERTION" means GitHub could not auto-detect the licence, so read the LICENSE file. **No licence = all rights reserved: study it, do not copy code.**

## 3.1 Core, production-grade libraries (safe to depend on)

| Repository | ★ | Last push | Lang | License | What it implements | Useful modules | Maturity |
|---|---|---|---|---|---|---|---|
| [pySTEPS/pysteps](https://github.com/pySTEPS/pysteps) | 587 | 2026-09-22 | Python | BSD-3 | Optical flow (Lucas–Kanade, VET, DARTS), semi-Lagrangian extrapolation, STEPS stochastic ensembles, NWP blending, **thunderstorm cell detection & tracking (T-DaTing)**, verification (CSI/FSS/ROC/reliability) | `pysteps/motion/lucaskanade.py`, `extrapolation/semilagrangian.py`, `feature/tstorm.py`, `tracking/tdating.py`, `blending/steps.py`, `verification/detcatscores.py`, `verification/probscores.py`, `verification/spatialscores.py` | Operational-grade (used by several met services) |
| [tobac-project/tobac](https://github.com/tobac-project/tobac) | 144 | 2026-09-01 | Python | BSD-3 | Feature detection, watershed segmentation, trajectory linking, **merge/split detection**, cell statistics — works on satellite BT, radar, model fields | `feature_detection.py`, `segmentation/watershed_segmentation.py`, `tracking.py`, `merge_split.py`, `analysis/cell_analysis.py` | Research-grade, peer-reviewed (GMD 2019, v1.5 GMD 2024) |
| [openradar/TINT](https://github.com/openradar/TINT) | 95 | 2026-05-22 | Python | BSD-2 | TITAN-style radar cell tracking with phase correlation (Py-ART grids) | `tint/tracks.py`, `matching.py`, `phase_correlation.py`, `objects.py` | Stable, small |
| [uba/tathu](https://github.com/uba/tathu) | 42 | 2026-08-31 | Python | MIT | Tracking and **life-cycle analysis of convective systems** from GOES/MSG/radar; ForTraCC-style forecasters | `tracking/trackers.py`, `tracking/descriptors.py`, `tracking/forecasters.py`, `fortracc.py`, `satellite/msg.py` | Research-grade; directly relevant to lifecycle |
| [pytroll/satpy](https://github.com/pytroll/satpy) | 1208 | 2026-09-23 | Python | Apache-2.0 | Readers for SEVIRI (Meteosat-9 IODC), many others; resampling | `satpy` readers `seviri_l1b_native`, `seviri_l1b_hrit` | Operational-grade |
| [ARM-DOE/pyart](https://github.com/ARM-DOE/pyart) | 603 | 2026-09-24 | Python | BSD-style (NOASSERTION) | Radar I/O, gridding, dealiasing, echo classification | `pyart.io`, `pyart.map.grid_from_radars`, `pyart.correct` | Operational-grade |
| [openradar/xradar](https://github.com/openradar/xradar) | 141 | 2026-09-01 | Python | MIT | Radar in xarray (CfRadial2) | readers | Mature |
| [wradlib/wradlib](https://github.com/wradlib/wradlib) | 321 | 2026-09-03 | Python | NOASSERTION (check) | Radar processing, clutter, Z-R | `wradlib.zr`, `clutter` | Mature |
| [syedhamidali/PyScanCf](https://github.com/syedhamidali/PyScanCf) | 19 | 2025-04-19 | Python | MIT | **Converts IMD DWR sweeps to CfRadial** — India-specific | `pyscancf/pyscancf.py`, `maxcappi.py` | Small; only useful if you obtain IMD raw data |
| [Unidata/MetPy](https://github.com/Unidata/MetPy) | 1443 | 2026-09-21 | Python | BSD-3 | CAPE/CIN/shear/DCAPE, thermodynamics | `metpy.calc` | Mature |
| [xarray-contrib/xskillscore](https://github.com/xarray-contrib/xskillscore) | 243 | 2026-09-21 | Python | Apache-2.0 | Contingency scores, Brier, CRPS, reliability on xarray | `xskillscore` | Mature |
| [frazane/scoringrules](https://github.com/frazane/scoringrules) | 103 | 2026-07-25 | Python | Apache-2.0 | CRPS and proper scores | — | Mature |
| [ecmwf/earthkit-data](https://github.com/ecmwf/earthkit-data) | 121 | 2026-09-24 | Python | Apache-2.0 | Read GRIB/NetCDF/ERA5/ECMWF open data | — | Mature |

## 3.2 Deep-learning nowcasting models

| Repository | ★ | Last push | License | What it implements | Dataset | Weights | Local run? | Suitability for you |
|---|---|---|---|---|---|---|---|---|
| [HansBambel/SmaAt-UNet](https://github.com/HansBambel/SmaAt-UNet) | 294 | 2026-09-16 | **None** | Small attention U-Net (4M params) | Dutch KNMI radar | Paper only | Yes (CPU/GPU) | Architecture excellent for students — **re-implement from the paper; do not copy code** (no licence) |
| [hydrogo/rainnet](https://github.com/hydrogo/rainnet) | 154 | 2021 | MIT | U-Net radar nowcasting | DWD RY | Yes (Keras) | Yes | Good simple baseline; old TF |
| [hydrogo/rainymotion](https://github.com/hydrogo/rainymotion) | 197 | 2019 | MIT | Optical-flow nowcasting | DWD | — | Yes | Superseded by pysteps |
| [Hzzone/Precipitation-Nowcasting](https://github.com/Hzzone/Precipitation-Nowcasting) | 605 | 2026-09-15 | None | TrajGRU/ConvLSTM (PyTorch) | HKO-7 | — | Yes | Reference only (no licence) |
| [sxjscience/HKO-7](https://github.com/sxjscience/HKO-7) | 431 | 2026-09-10 | MIT | ConvLSTM/TrajGRU benchmark | HKO-7 (request) | — | Yes | Historical reference |
| [chengtan9907/OpenSTL](https://github.com/chengtan9907/OpenSTL) | 1152 | 2026-03-01 | Apache-2.0 | Benchmark of ~15 spatiotemporal models (ConvLSTM, PredRNN, SimVP, TAU...) | Moving-MNIST, SEVIR-like | Some | Yes | **Best way to try ConvLSTM/SimVP quickly and legally** |
| [amazon-science/earth-forecasting-transformer](https://github.com/amazon-science/earth-forecasting-transformer) | 470 | 2023 | Apache-2.0 | Earthformer (cuboid attention) | SEVIR, N-body | Yes | GPU needed | Stretch goal |
| [openclimatefix/skillful_nowcasting](https://github.com/openclimatefix/skillful_nowcasting) | 297 | 2026-09-21 | MIT | DGMR (PyTorch port) | UK radar | HF weights (UK) | Heavy GPU | Not realistic to retrain; domain mismatch |
| [openclimatefix/metnet](https://github.com/openclimatefix/metnet) | 304 | 2026-09-21 | MIT | MetNet/MetNet-2 (PyTorch) | — | No | Heavy | Architecture reference |
| [MeteoSwiss/ldcast](https://github.com/MeteoSwiss/ldcast) | 147 | 2023 | Apache-2.0 | Latent diffusion nowcasting | Swiss radar | Yes (Zenodo) | GPU | Architecture C only |
| [gaozhihan/PreDiff](https://github.com/gaozhihan/PreDiff) | 160 | 2025-10 | Apache-2.0 | Latent diffusion + knowledge alignment | SEVIR | Yes | GPU | Architecture C only |
| [DeminYu98/DiffCast](https://github.com/DeminYu98/DiffCast) | 139 | 2025-09 | **GPL-3.0** | Residual diffusion | SEVIR etc. | Yes | GPU | GPL copyleft risk |
| [Applied-IAS/DDMS](https://github.com/Applied-IAS/DDMS) | 13 | 2025-12 | MIT | 4-h **satellite** thunderstorm diffusion (PNAS 2025) | FY-4A | [U] | GPU | Closest to 0–6 h satellite nowcasting; MIT → study/reuse with attribution |
| [MIT-AI-Accelerator/neurips-2020-sevir](https://github.com/MIT-AI-Accelerator/neurips-2020-sevir) | 102 | 2020 | MIT | SEVIR loaders + baselines | SEVIR (AWS open data) | Yes | Yes | **Pre-training/benchmark data for the pipeline while Indian data downloads** |

## 3.3 Thunderstorm / lightning / CI / hail specific

| Repository | ★ | Last push | License | What it implements | Data | Relevance |
|---|---|---|---|---|---|---|
| [MeteoSwiss/c4dl-multi](https://github.com/MeteoSwiss/c4dl-multi) | 34 | 2023 | BSD-3 | Multi-hazard (lightning, hail, heavy rain) fusion nowcasting with **Shapley source-importance**, calibration, Lagrangian features | Swiss radar+satellite+lightning+NWP+DEM | **Highest conceptual relevance.** Reusable: `analysis/calibration.py`, `analysis/shapley.py`, `analysis/lagrangian.py`, `analysis/evaluation.py` |
| [MeteoSwiss/c4dl-lightningdl](https://github.com/MeteoSwiss/c4dl-lightningdl) | 18 | 2022 | BSD-3 | Recurrent-conv lightning nowcasting | Swiss | Lightning loss and feature design |
| [gitlab.ssec.wisc.edu/jcintineo/lightningcast](https://gitlab.ssec.wisc.edu/jcintineo/lightningcast) | — | 2026-09-15 | **GPL-3.0** | **NOAA ProbSevere LightningCast** U-Net: P(lightning in 60 min) from ABI 0.64/1.6/10.3/12.3 µm; pip/Docker; supports GOES & Himawari L1 | GOES ABI + GLM | **Pre-trained lightning model whose input channels match INSAT-3D (0.65/1.625/10.8/12.0 µm) and SEVIRI (0.6/1.6/10.8/12.0 µm)** → transfer-learning candidate (Part 9). GPL implications in Part Q |
| [aurelienne/lc_br](https://github.com/aurelienne/lc_br) | 3 | 2026-04 | None | Fine-tuning LightningCast to Brazil | GOES-16 + GLM | **Proof that LightningCast domain transfer has been done** — cite it as precedent; don't copy (no licence) |
| [jlc248/ProbSevere_v3_paper_2024](https://github.com/jlc248/ProbSevere_v3_paper_2024) | 1 | 2025-08 | GPL-3.0 | Train/evaluate GBDTs on per-storm attributes (ProbSevere v3) | Zenodo storm-attribute tables (2018–2023) | **Blueprint for object-based hazard ML**; the data schema is instructive |
| [sortland33/ThunderCast](https://github.com/sortland33/ThunderCast) | 3 | 2025-04 | GPL-3.0 | U-Net thunderstorm nowcasting from GOES | GOES + MRMS | Reference |
| [thunderhoser/ml4convection](https://github.com/thunderhoser/ml4convection) | 30 | 2023 | None | U-Net convection nowcast from Himawari-8 (Lagerquist et al. 2021) | Himawari + Taiwan radar | Method reference only (no licence) |
| [NCAR/goes16ci](https://github.com/NCAR/goes16ci) | 18 | 2022 | None | GOES-16 CI benchmark | GOES-16 + GLM | Reference only |
| [a-urq/ml-ci-py](https://github.com/a-urq/ml-ci-py) | 5 | 2026-02 | None | ML CI probability, 2-h lead | [U] | Reference only |
| [dxf424/CIUQ](https://github.com/dxf424/CIUQ) | 1 | 2026-01 | None | Bayesian NN for CI + uncertainty | [U] | Idea reference |
| [fravij99/EO_hail_nowcaster](https://github.com/fravij99/EO_hail_nowcaster) | 0 | 2026-05 | MIT | Probabilistic hail nowcasting, EO fusion, physics-informed | [U] | Small; inspect before relying on it |
| [nathanmitchell8675/ExplainableBoostingMachine-OvershootingTops](https://github.com/nathanmitchell8675/ExplainableBoostingMachine-OvershootingTops) | 0 | 2026-09 | None | **EBM (glass-box)** for overshooting tops | Satellite | Idea: glass-box models for explainability |
| [haraltho/lightning-nowcasting-deep-learning](https://github.com/haraltho/lightning-nowcasting-deep-learning) | 3 | 2026-03 | None | Lightning from polarimetric radar | [U] | Reference |
| [seominseok0429/ProbSevere-LightningCast-...](https://github.com/seominseok0429/ProbSevere-LightningCast-A-Deep-Learning-Model-for-Satellite-Based-Lightning-Nowcasting) | 4 | 2024 | None | Unofficial PyTorch re-implementation | GOES | Reference |

## 3.4 India-specific satellite / radar tooling

| Repository | ★ | License | What it does | Use |
|---|---|---|---|---|
| [mosdac/Python](https://github.com/mosdac/Python) | 2 | GPL-3.0 | MOSDAC-published Python code for MOSDAC data | Read for format hints |
| [MOSDAC mdapi](https://www.mosdac.gov.in/downloadapi-manual) | — | (ISRO tool) | **Official scripted download API** (`mdapi.py` + `config.json`, datasetId, bbox, time range) | **Primary INSAT download route** |
| [santacodes/COG](https://github.com/santacodes/COG) | 12 | None | INSAT-3DR → Cloud-Optimized GeoTIFF | Idea reference |
| [zeroby0/insatinator](https://github.com/zeroby0/insatinator) | 3 | MIT | INSAT-3D imagery processing | Small, reusable |
| [rupeshs/insat3d_imagen](https://github.com/rupeshs/insat3d_imagen) | 9 | GPL-3.0 | INSAT-3D image processor | Reference |
| [urmilkadakia/Rainfall-prediction-...Gujarat](https://github.com/urmilkadakia/Rainfall-prediction-for-the-state-of-Gujarat-using-deep-learning-technique) | 24 | GPL-3.0 | INSAT IR → rainfall DL (2018) | Historical |
| [syedhamidali/IMD_RADAR_NETWORK_2023](https://github.com/syedhamidali/IMD_RADAR_NETWORK_2023) | 1 | BSD-3 | IMD DWR locations/bands/ranges | **Radar-coverage map layer for the dashboard** (also on [Figshare](https://figshare.com/articles/dataset/Network_of_Doppler_Weather_Radars_of_India_Meteorological_Department/22704910)) |

## 3.5 Summary table (as requested)

| Repository | Purpose | Dataset | Model | License | Reusable component | Relevance to SIH26084 |
|---|---|---|---|---|---|---|
| pysteps | Nowcasting framework | Any radar/sat grid | Optical flow, STEPS, T-DaTing | BSD-3 | Motion, extrapolation, cell tracking, verification | ★★★★★ baseline + verification |
| tobac | Cloud/cell tracking | Sat BT, radar | Detection + watershed + linking + merge/split | BSD-3 | Entire tracking layer | ★★★★★ lifecycle core |
| tathu | Convective lifecycle | GOES/MSG/radar | ForTraCC-style | MIT | Lifecycle descriptors | ★★★★ |
| TINT | Radar cell tracking | Py-ART grids | TITAN-like | BSD-2 | Radar case study | ★★★ |
| satpy | Satellite I/O | SEVIRI, many | — | Apache-2.0 | Meteosat-9 IODC reader | ★★★★★ |
| MetPy | Thermodynamics | NWP/ERA5 | — | BSD-3 | CAPE, CIN, shear, DCAPE | ★★★★ |
| c4dl-multi | Multi-hazard fusion | Swiss multi-source | RNN-conv + Shapley | BSD-3 | Calibration, Shapley, Lagrangian code | ★★★★★ design reference |
| LightningCast | Sat lightning nowcast | GOES/Himawari + GLM | U-Net | GPL-3.0 | Pre-trained model for transfer | ★★★★ (licence caution) |
| ProbSevere v3 scripts | Object hazard ML | Storm-attribute tables | GBDT | GPL-3.0 | Feature schema, evaluation | ★★★★ design reference |
| OpenSTL | Spatiotemporal DL zoo | Various | ConvLSTM, SimVP, TAU... | Apache-2.0 | Gridded DL models | ★★★ |
| SmaAt-UNet | Light U-Net | KNMI radar | Attention U-Net | none | Paper only | ★★★ (re-implement) |
| DDMS | 4-h sat diffusion | FY-4A | Diffusion | MIT | Architecture C ideas | ★★★ |
| LDCast / PreDiff | Generative nowcast | Radar / SEVIR | Latent diffusion | Apache-2.0 | Architecture C | ★★ |
| SEVIR | Benchmark data | GOES + NEXRAD + GLM | — | MIT | Pre-training while Indian data downloads | ★★★ |
| xskillscore / scoringrules | Verification | — | — | Apache-2.0 | Metrics | ★★★★ |

---

# PART 4 — STUDENT / SIH PROJECT LANDSCAPE

I inspected READMEs and, where noted, the code. Everything below describes what the repo says, or what I found in its files. Nothing here is copied. **Do not copy any of these; they are your competitors or prior student work.**

| # | Project (repo) | PS / context | Architecture & data | Model | Unique feature | Weaknesses (evidence) | Production-like? | Lesson |
|---|---|---|---|---|---|---|---|---|
| 1 | **VARSHANET** — [adarshsisodiya2007-web/sih86](https://github.com/adarshsisodiya2007-web/sih86) | **SIH26084** | FastAPI + React/Leaflet; PostGIS schema; CAP 1.2 alerts; 11 screens | GBM regressor + RF classifier ("R² > 0.95, ROC-AUC > 0.98") | CAP-XML alerts, TITAN/SCIT-style tracking claims, "scientific honesty notice" | **`ml_engine.py` `_generate_synthetic_training_data()` draws features from `np.random.uniform` ranges** → the high R²/AUC measure how well the model recovers synthetic rules, not real skill; README says all live cells run in "SIMULATION MODE" | Polished UI, simulated science | Do **not** report metrics on synthetic data. Judges will ask "trained on what?" |
| 2 | **nowcasting_sih** — [Avizanzane44/nowcasting_sih](https://github.com/Avizanzane44/nowcasting_sih) | **SIH26084** | pysteps example **Finnish (FMI) radar**, 40 frames; OpenCV Farnebäck fallback; FastAPI + Leaflet; SQLite | ConvLSTM PoC trained on 40 frames | Honest `PROGRESS.md`; ETA countdown logic | Non-Indian data; satellite/lightning "physically-informed simulations"; ConvLSTM "suffers from ETA drift and hallucination" (their words) | Demo | Honesty is good, but foreign data mapped onto Indian cities is weak |
| 3 | **Solvix** — [RushilAmreliya/Solvix](https://github.com/RushilAmreliya/Solvix) | **SIH26084** (Assam) | PERSIANN-CCS 4 km, GPM IMERG, SRTM, RainViewer live tiles, Open-Meteo CAPE/shear; React + Streamlit | pysteps Lucas–Kanade + U-Net (30 % blend) | Terrain downscaling to 1 km, IMD threshold engine, tests | Data simulator for live feed; "1 km" from DEM downscaling ≠ observed 1 km skill; RainViewer data isn't guaranteed (see Part 6) | Demo with real pieces | The closest real-data competitor — make sure your verification beats theirs |
| 4 | [xarjunpatil/SIH26084-...](https://github.com/xarjunpatil/SIH26084-Convective-scale-nowcasting-for-Thunderstorms-Hail-Cloudbursts-06-hr) | **SIH26084** | Static HTML + FastAPI "anomaly scoring"; same author has near-identical repos for SIH26072 | — | — | Template-style, generic "production-ready" claims | Template | Generic "mission control" UIs are already common |
| 5 | **ThunderWatch AI** — [nachiket-mr360/AIML_Thunderstorm_nowcasting_by_ThunderWatch_AI](https://github.com/nachiket-mr360/AIML_Thunderstorm_nowcasting_by_ThunderWatch_AI) | SIH26072 | Station thunderstorm observations + GFS + INSAT-3DR case evidence; deployed on Render | Random Forest, +1/+2/+3 h | **Real observed labels**, causal features, historical replay, "fail-closed inference" | Point-based (5 locations), not gridded/cell-based | Research prototype, honest | The most scientifically careful competitor pattern: real labels + replay |
| 6 | **Avenger2007/SIH-Nowcasting-** — [link](https://github.com/Avenger2007/SIH-Nowcasting-) | SIH26072 | Streamlit; scrapes **MOSDAC gallery images** (`mosdac.gov.in/gallery/getImage.php`) and **IMD radar images** (`mausam.imd.gov.in/Radar/`); GFS NOMADS; Open-Meteo; Bhuvan WMS | XGBoost | Calibration, consistency checks, honest banner "model fitted to synthetic labels" | Labels synthetic; scraping product images, not calibrated data | Honest demo | Shows the "no-credential" data route (images) — fine for display, weak for science |
| 7 | **STORMTRACE** — [targaryenv2/STORMTRACE](https://github.com/targaryenv2/STORMTRACE) | SIH26072 | Radar + INSAT-3DR + ERA5 claims; React | ConvLSTM + MC-Dropout; TITAN | 13-language UI, MC-dropout bands | Claims not backed by visible real-data evaluation | Demo | MC-dropout "confidence bands" are already taken; calibration is not |
| 8 | [dhyeyRathi/sih26072](https://github.com/dhyeyRathi/sih26072) | SIH26072 | 5-source pipeline design, forecaster/DDMA/responder personas | [U] | Good user-persona framing | Mostly design in README | Early | User personas are a good framing |
| 9 | [Abinash-08/SIH26072-Megh](https://github.com/Abinash-08/SIH26072-Megh) | SIH26072 | Bhuvan scripts embedded, Keras ConvLSTM file | ConvLSTM | Bhuvan base map | [U] data | Demo | ConvLSTM is the default choice |
| 10 | [DevshreevasAI-ML/thunderstorm-nowcasting-india](https://github.com/DevshreevasAI-ML/thunderstorm-nowcasting-india) | Student | ERA5/Open-Meteo hourly, 50 cities | XGBoost 98 %, RF 97.7 %, LSTM 83 % "accuracy" | 50-city scale | **Accuracy on imbalanced classes** is misleading; no CSI/FAR | Demo | Use CSI/POD/FAR and Brier, never plain accuracy |
| 11 | [Kaushik1223/SIH_cloudburst_prediction](https://github.com/Kaushik1223/SIH_cloudburst_prediction) | SIH 2023 cloudburst | Front-end only | — | — | No model | UI only | Earlier SIH cloudburst work was UI-heavy |
| 12 | [avd1729/Cloudburst-Prediction-System](https://github.com/avd1729/Cloudburst-Prediction-System) | Student | Kaggle "IndianWeatherRepository.csv" | Keras dense model; YouTube demo | Video demo | Tabular city weather cannot resolve convective cells | Demo | Tabular weather → "cloudburst" is a common anti-pattern |
| 13 | [SatyamVyas00/Cloudburst-Prediction-using-GAF-and-CNN](https://github.com/SatyamVyas00/Cloudburst-Prediction-using-GAF-and-CNN) | Published (Layek et al. 2026, *Model. Earth Syst. Environ.*) | Time series → Gramian Angular Field images, Uttarakhand | CNN; AUC 97.7 % (6 h) | Peer-reviewed | [I] AUC on case-vs-non-case samples can overstate operational skill (base-rate issue) | Research code | Cite as prior Indian cloudburst work; ask "what's the FAR at operational base rates?" |
| 14 | [nalin7sharma/Cloudburst-Early-Warning-and-Alarm-System](https://github.com/nalin7sharma/Cloudburst-Early-Warning-and-Alarm-System) | Student | IoT nodes, LoRa, solar | ConvLSTM anomaly | Hardware | Wrong category (Software PS); cost | Concept | Hardware is out of scope for this PS |
| 15 | [shivajaysaxena/Satellite_Cloudburst_Prediction](https://github.com/shivajaysaxena/Satellite_Cloudburst_Prediction) | Student | Landsat/Sentinel/MODIS indices (NDVI etc.), `data_generator.py` | RF/SVM/XGB/CNN | — | Polar-orbiting land indices can't nowcast convection; sample-data generator | Demo | Wrong sensor for the timescale |
| 16 | [jagadeesh0413/CloudBurstPredictionML](https://github.com/jagadeesh0413/CloudBurstPredictionML) | Student | Met parameters | Random Forest | — | Generic | Demo | — |
| 17 | [aneeshpatne/mausam3.0](https://github.com/aneeshpatne/mausam3.0) | Independent (Mumbai) | IMD radar PPI/SRI images, rain stations, GFS/ECMWF charts → **LLM decides severity**, change-gated | LLM | Excellent ops engineering (idempotent alerts, heartbeats) | Not a quantitative forecast | Production-like ops | Borrow **ops ideas** (change-gating, data-health) — not the LLM-as-forecaster |
| 18 | [mendrika-mdg/zambia-nowcasting](https://github.com/mendrika-mdg/zambia-nowcasting) | Research (Zambia) | Satellite-based thunderstorm nowcast deployment | [U] | Global-South satellite-first | — | [U] | A precedent for satellite-first nowcasting where radar is sparse |
| 19 | [ai4os-hub/thunderstorm-nowcast-microstep](https://github.com/ai4os-hub/thunderstorm-nowcast-microstep) | EU project | Radar thunderstorm nowcast for agrometeorology | [U] | MIT | — | [U] | Agro-user framing |
| 20 | [ANDRIANANTENAINA001Angelo/Storm-Nowcasting-Hackathon---IndabaX-Madagascar-24](https://github.com/ANDRIANANTENAINA001Angelo/Storm-Nowcasting-Hackathon---IndabaX-Madagascar-24) | Hackathon (Madagascar 2024) | Notebook | [U] | — | — | Notebook | Hackathon-scale satellite nowcasting exists |

## 4.1 COMMON APPROACHES — "what everyone is already doing" [I from the table above]

1. React/Leaflet "mission control" dark dashboard, 8–11 screens, KPI cards, red/amber/green alerts.
2. ConvLSTM (sometimes a U-Net) trained on tiny or foreign data (FMI 40 frames, Kaggle CSVs).
3. pysteps / OpenCV optical flow as the "real" engine, with the DL model blended on top.
4. **Simulated** radar, satellite and lightning streams to make the dashboard "live".
5. RF/XGBoost on tabular point weather (ERA5/Open-Meteo) → "thunderstorm probability", reported as **accuracy**.
6. "Explainability" = feature importance bar charts.
7. "Uncertainty" = MC-dropout bands, not validated.
8. Multilingual SMS/WhatsApp alerts, CAP XML.
9. Scraping IMD radar PNGs / MOSDAC gallery JPGs for display.
10. Claiming "1 km" resolution via interpolation or DEM downscaling.

## 4.2 UNDEREXPLORED APPROACHES — in the student/SIH space [I]

1. **Object-based verification** (matching predicted cells to observed cells; CSI of cell tracks, ETA error in minutes).
2. **Real observed labels for India:** ISS-LIS lightning (2017–2023), IMD hail reports (2026), GPM DPR heavy-ice/graupel-hail flags, IMERG/GSMaP extreme rain rates.
3. **Self-supervised labels:** the future satellite frame *is* the label for CI and lifecycle, so you need no external dataset.
4. **Calibration** (reliability diagrams, Brier skill score, isotonic/Platt) and **conformal prediction intervals** for ETA.
5. **Lifecycle-transition forecasting** (P(cell becomes mature within 30 min), expected time to decay), rather than current-state labels.
6. **Merge/split genealogy** using tobac's `merge_split`.
7. **Transfer learning** from an operational, openly licensed model (LightningCast) to INSAT/SEVIRI.
8. **Baseline-relative skill:** everything shown as improvement over persistence and Lagrangian extrapolation.
9. **Skill-vs-lead-time honesty curve** for 0–6 h.
10. **Data-health-aware inference:** degrading gracefully when a source is missing, and showing it.

---

# PART 5 — RESEARCH LANDSCAPE

"Student-realistic?" rating: ✅ realistic on a laptop or free Colab · ⚠️ needs a GPU and effort · ❌ out of reach (compute or data).

## 5.1 Foundational & tracking

| Paper | Year | Authors | Method | Data | Res / horizon | Key result | Limitation | Student-realistic |
|---|---|---|---|---|---|---|---|---|
| [TITAN](https://doi.org/10.1175/1520-0426(1993)010%3C0785:TTIDTA%3E2.0.CO;2) | 1993 | Dixon & Wiener | Threshold cell ID + optimal matching tracking | Radar | ~1 km / 0–60 min | Classic operational cell tracker | Linear extrapolation; no growth/decay | ✅ (via TINT) |
| [pysteps](https://gmd.copernicus.org/articles/12/4185/2019/) | 2019 | Pulkkinen et al. | Open nowcasting framework (optical flow, STEPS) | Radar | 1 km / 0–2 h | Reference implementation of many methods | Radar-centric | ✅ |
| [tobac](https://gmd.copernicus.org/articles/12/4551/2019/) · [v1.5](https://gmd.copernicus.org/articles/17/5309/2024/) | 2019/2024 | Heikenfeld et al.; Sokolowsky et al. | Multi-dataset feature tracking, merge/split | Sat, radar, model | any | Community-standard tracking | Parameter tuning needed | ✅ |
| [MeteoSwiss TRT](https://www.meteoswiss.admin.ch/about-us/research-and-cooperation/projects/en/2002/trt.html) | 2004– | Hering et al. | Radar cell tracking + **severity rank** (VIL, EchoTop45, max Z, area > 55 dBZ) | Swiss radar | 2 km, 5 min / 0–60 min | Operational | Needs 3D radar | ✅ concept |
| [NWCSAF RDT-CW](https://www.nwcsaf.org/rdt_description_2025) | ongoing | Météo-France / NWCSAF | Satellite cell detection + tracking + **development phase** + cooling rate + severity | GEO sat (+NWP, lightning) | sat pixel / 0–60 min | Operational in Europe | Forecast ≤ 1 h; licensed software for NMHSs | ✅ concept (re-implement ideas) |

## 5.2 Convective initiation (satellite)

| Paper | Year | Authors | Method | Data | Horizon | Key result | Limitation | Realistic |
|---|---|---|---|---|---|---|---|---|
| Mecikalski & Bedka (MWR 134) | 2006 | Mecikalski & Bedka | **IR "interest fields"** (10.8 µm BT drop below 0 °C, cooling rate ≤ −4 K/15 min, WV−IR differences) | GOES | 30–60 min | Physics-based CI rules | Cirrus contamination | ✅ **your physics baseline** |
| [Lagerquist et al. (MWR 149)](https://www.researchgate.net/publication/354875598_Using_Deep_Learning_to_Nowcast_the_Spatial_Coverage_of_Convection_from_Himawari-8_Satellite_Data) | 2021 | Lagerquist, Stewart, Ebert-Uphoff, Kumler | U-Net, convection mask nowcast | Himawari-8 + Taiwan radar | 0–2 h | Good FSS at 0–1 h | Radar labels needed | ⚠️ |
| [CIUnet (MWR 152(1))](https://journals.ametsoc.org/view/journals/mwre/152/1/MWR-D-22-0216.1.xml) | 2024 | (see link) | U-Net on 8 AHI interest fields + terrain, **explainable** | Himawari-8 | 30 min | **POD 93.3 %, FAR 18.3 % at 30 min**; 7.3−10.4 µm BTD most important; tri-spectral BTD reduces FAR | Region-specific | ✅ **directly transferable to INSAT WV (6.8) − TIR (10.8)** |
| [Physics-augmented RF CI (ESS)](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024EA003571) | 2024 | Yang et al. | Physics-augmented random forest | Himawari (S. China) | 0–1 h | RF competitive for CI | Regional | ✅ |
| [Goenka et al. (GRL)](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024GL112764) | 2025 | Goenka, Taori, Rao, Chauhan (NRSC) | INSAT-3D OLR, LST, winds as lightning precursors | INSAT-3D + NRSC lightning network | **~2.5 h lead**, agreement 0.6–0.8 | **First INSAT-based lightning-precursor study** | Coarse products | ✅ **cite: Indian, ISRO-authored** |
| [GeoConvNet (Research Square preprint)](https://www.researchsquare.com/article/rs-10978955/v1) | 2024–25 | (see link) | Pixel segmentation of convection classes from INSAT TIR/WV | INSAT-3D/3DR, NE India, 65k tiles | Detection | 4-class deep-convection mask | Preprint | ✅ |

## 5.3 Lightning / hail / multi-hazard

| Paper | Year | Authors | Method | Data | Horizon | Key result | Limitation | Realistic |
|---|---|---|---|---|---|---|---|---|
| ProbSevere LightningCast (WAF 37) | 2022 | Cintineo et al. | U-Net P(lightning ≤ 60 min) | GOES ABI + GLM | 60 min | Operational at NOAA | Needs GLM labels to retrain | ✅ via transfer |
| [ProbSevere v3 (WAF 39(12))](https://journals.ametsoc.org/view/journals/wefo/39/12/WAF-D-24-0076.1.pdf) | 2024 | Cintineo et al. | Object tracking + **GBDT on per-storm predictors** → P(hail/wind/tornado) | Radar + GOES + GLM + NWP | 0–60 min | **Operational Aug 2025** | US data | ✅ **the design pattern for your object model** |
| [c4dl-multi (GRL)](https://arxiv.org/abs/2211.01001) | 2023 | Leinonen, Hamann, Sideris, Germann | Recurrent-conv multi-hazard fusion, **Shapley source importance** | Radar, lightning, sat, NWP, DEM | 1 km, 5 min / 60 min | Radar most important for all hazards | Needs radar | ⚠️ concept |
| Leinonen et al. (AIES 1(4)) | 2022 | Leinonen et al. | Seamless lightning nowcasting | Swiss multi-source | 60 min | Source ablations | Needs radar | ⚠️ |
| [Metzl et al. — "Physical Scales Matter"](https://arxiv.org/abs/2504.09994) | 2025 | Metzl, Vahid Yousefnia, Müller, Poli, Celano, Bölle | ResU-Net vs **advection-informed** NN (adds Lagrangian persistence of inputs) | Satellite + lightning | up to > 2 h | Advection gains grow **after 2 h** and at high speeds | European | ✅ **key recipe for your 2–6 h extension** |
| GPM DPR heavy-ice detection ([JTECH 35(3)](https://journals.ametsoc.org/view/journals/atot/35/3/jtech-d-17-0120.1.xml)) | 2018 | Iguchi et al. | `flagHeavyIcePrecip` from dual-frequency ratio + Z above −10 °C | GPM DPR | — | Thunderstorm/graupel indicator from space | Sparse overpasses | ✅ as **hail/graupel validation proxy** |
| [flagGraupelHail evaluation (Remote Sens. 17, 3741)](https://doi.org/10.3390/rs17223741) | 2025 | (see link) | Validates DPR graupel/hail flag vs phased-array radar | GPM + MP-PAWR | — | Flag has useful skill | Japan | ✅ supports your proxy |
| Waldvogel et al.; Witt et al. (SHI/POSH/MESH) | 1979/1998 | — | Radar hail proxies (45 dBZ above freezing level) | Radar | — | Operational hail proxies | Needs 3D radar | ✅ for TERLS radar case |

## 5.4 Deep-learning & generative nowcasting

| Paper | Year | Authors | Method | Data | Res / horizon | Key result | Limitation | Realistic |
|---|---|---|---|---|---|---|---|---|
| [ConvLSTM](https://arxiv.org/abs/1506.04214) | 2015 | Shi et al. | Conv-recurrent | HKO radar | 0–90 min | Beat optical flow on HKO | Blurry at long leads | ✅ (common — don't make it your novelty) |
| [RainNet (GMD 13)](https://gmd.copernicus.org/articles/13/2631/2020/) | 2020 | Ayzel, Scheffer, Heistermann | U-Net | DWD radar | 1 km / 60 min | Beats optical flow at low intensities | Smoothing | ✅ |
| [SmaAt-UNet](https://arxiv.org/abs/2007.04417) | 2021 | Trebing, Stańczyk, Mehrkanoon | Attention U-Net, 1/4 params | KNMI | 30 min | Comparable with 4× fewer params | Short horizon | ✅ |
| [DGMR (Nature 597)](https://www.nature.com/articles/s41586-021-03854-z) | 2021 | Ravuri et al. | Conditional GAN ensemble | UK radar | 1 km / 90 min | Forecasters preferred it 89 % of the time | Heavy compute | ❌ retrain |
| [Earthformer](https://arxiv.org/abs/2207.05833) | 2022 | Gao et al. | Cuboid-attention transformer | SEVIR | 60 min | SOTA on SEVIR (2022) | GPU | ⚠️ |
| [NowcastNet (Nature 619)](https://www.nature.com/articles/s41586-023-06184-4) | 2023 | Zhang et al. | Physics-conditioned generative (evolution + GAN) | US/China radar | 1 km / 3 h | Best for extreme precipitation (expert eval) | Heavy | ❌ retrain / ✅ concept |
| [PreDiff](https://arxiv.org/abs/2307.10422) · [LDCast](https://arxiv.org/abs/2304.12891) · [DiffCast](https://arxiv.org/abs/2312.06734) | 2023–24 | Gao et al.; Leinonen et al.; Yu et al. | Latent / residual diffusion | SEVIR / Swiss radar | 1–2 h | Sharper, calibrated ensembles | GPU-days | ⚠️/❌ |
| MetNet-3 ([arXiv 2306.06079](https://arxiv.org/abs/2306.06079)) | 2023 | Andrychowicz et al. | Densification transformer | US radar + stations + sat | 24 h | Beats HRRR to ~24 h | Google compute | ❌ |
| [DDMS (PNAS)](https://arxiv.org/abs/2404.10512) | 2025 | Dai et al. | Diffusion on **satellite BT** | FY-4A, 4 km, 15 min | **4 h** | First effective 4-h convection nowcast from satellite (authors' claim) | Large training | ⚠️ (study; C only) |
| [Global MetNet](https://arxiv.org/abs/2510.13050) | 2025 | Agrawal et al. (Google) | Satellite + NWP + GPM CORRA → 0–12 h precip | Global, **Global South focus** | ~5 km, 15 min / 12 h | Operational globally | Google compute | ❌ retrain / ✅ **motivation: satellite-first for sparse-radar regions** |
| [Stormscope](https://arxiv.org/abs/2601.17268) | 2026 | Pathak et al. (NVIDIA) | Transformer diffusion on sat + radar | CONUS | 10 min / **6 h** | Competitive with mesoscale NWP at 1–6 h | Very heavy | ❌ / ✅ citation for 6-h feasibility |

## 5.5 India-specific nowcasting & operations

| Paper / system | Year | Key content | Use |
|---|---|---|---|
| [IMD nowcasting with WDSS-II](https://link.springer.com/article/10.1007/s00703-014-0315-7) · [WDSS-II note](https://nwp.imd.gov.in/WDSSII_website.pdf) | 2014– | IMD nowcast T+0–2 h; thunderstorm/squall/hail nowcasts started Dec 2012 for 125 cities, now 156 | **Operational baseline to position against** (0–2 h, radar-covered cities) |
| [SWIRLS with Indian DWR (MAUSAM)](https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/1442) | ~2012 | HKO's SWIRLS adapted for IMD (Commonwealth Games 2010) | Prior art |
| [IMD-HRRR](https://www.academia.edu/117476801/Development_of_India_Meteorological_Department_High_Resolution_Rapid_Refresh_IMD_HRRR_Modeling_System_for_Very_Short_Range_Weather_Forecasting) · [NCUM-R 1.5 km hourly DA](https://srf.tropmet.res.in/srf/ts_prediction_system/ncum-r.php) | 2020s | Rapid-refresh convective-scale NWP in India | **The NWP your 2–6 h guidance competes/blends with** |
| [Validation of INSAT-3D/3DR nowcasting rain occurrences (ASR)](https://www.sciencedirect.com/science/article/abs/pii/S0273117723003873) | 2023 | SAC INSAT-based nowcast product validation | Shows ISRO already has satellite nowcast products |
| [LSTM prediction of INSAT-3DR images (MAUSAM)](https://mausamjournal.imd.gov.in/index.php/MAUSAM/article/view/6893) | 2025–26 | LSTM image extrapolation | Common approach |
| ["Next-gen storm nowcasting ... India" (TAAC)](https://link.springer.com/article/10.1007/s00704-025-05650-5) | 2025 | pySTEPS-based nowcasting on satellite-based reflectivity over India | Prior Indian pysteps work — cite, don't claim pysteps as novel |
| ["Prediction of thunderstorm evolution ... DWR ... southern India"](https://www.researchgate.net/publication/392433160_Prediction_of_thunderstorm_evolution_using_deep_learning_models_with_doppler_weather_radar_observations_over_southern_part_of_India) | 2025 | DL on Indian DWR | Radar-DL prior art (they had data access) |
| [NRSC lightning network (Nat. Hazards)](https://link.springer.com/article/10.1007/s11069-021-05042-8) | 2021 | 46 sensors, ToA, 98 % DE within 300 km | Potential label source |
| [ILLN assessment (Atmos. Res.)](https://www.sciencedirect.com/science/article/abs/pii/S0169809525001619) | 2025 | IITM network, 83 sensors, ~200 m accuracy | Potential label source (request) |
| [IndiaWeatherBench](https://arxiv.org/abs/2509.00653) | 2025 | Regional DL weather benchmark on IMDAA | Context: Indian ML benchmarks exist for NWP scales, not nowcasting |

## 5.6 Uncertainty & explainability (for judges' questions)

- McGovern et al. 2019, *"Making the black box more transparent"*, BAMS — permutation importance, saliency, backwards optimization for meteorology.
- Haynes et al. 2023, *"Creating and evaluating uncertainty estimates with neural networks for environmental-science applications"*, AIES — spread–skill, PIT, CRPS; warns against un-validated MC-dropout.
- Roberts & Lean 2008, MWR — Fractions Skill Score (FSS) for neighbourhood verification.
- Roebber 2009, WAF — performance diagram (POD, SR, CSI, bias on one chart).
- Conformal prediction (e.g., Angelopoulos & Bates 2021, [arXiv 2107.07511](https://arxiv.org/abs/2107.07511)) — distribution-free intervals with guaranteed coverage. Cheap and rigorous for ETA.

---

# PART 6 — DATA FEASIBILITY (most important)

## 6.1 Master table

| Dataset | Access | Temporal | Spatial | Key variables | Historical | Near-real-time | Coverage | Licence / terms | Training? | Live demo? |
|---|---|---|---|---|---|---|---|---|---|---|
| **INSAT-3DR / INSAT-3DS Imager L1B** ([MOSDAC](https://mosdac.gov.in/insat-3dr), [3DS](https://mosdac.gov.in/insat-3ds), [API](https://www.mosdac.gov.in/downloadapi-manual)) | MOSDAC SSO account; `mdapi.py` + `config.json` (datasetId, bbox, time) [V] | 30 min each; **15 min staggered** across two satellites [V] | VIS 0.65 & SWIR 1.625 µm: 1 km; MIR 3.9, TIR1 10.8, TIR2 12.0 µm: 4 km; WV 6.8 µm: 8 km [V per INSAT-3D spec; 3DS "identical sensors" per MOSDAC] | Calibrated radiance/BT, geolocation | 3DR from 2016; 3DS from 2024 (launched Feb 2024) [V] | **Registered general users: limited datasets, 3-day latency; NRT only for privileged users; anonymous: images/metadata/Open Data** [V — [MOSDAC data access policy](https://www.mosdac.gov.in/data-access-policy)] | India + Indian Ocean full disk | ISRO data access policy (read the [guidelines PDF](https://www.mosdac.gov.in/data-access-policy)) | ✅ **Yes (primary Indian source)** | ⚠️ gallery images live (display); L1B arrives with ≥ 3-day lag → **replay mode** |
| INSAT-3D (original) | MOSDAC | 30 min | as above | as above | 2013– (retiring; replaced by 3DS at 82°E) [V] | — | — | — | ✅ archive | — |
| INSAT derived products (OLR, HEM rain, CMV, LST, cloud mask) | MOSDAC | 30 min | 4–10 km | Products | yes | same policy | India | same | ✅ features | ⚠️ |
| **Meteosat-9 IODC SEVIRI L1.5** ([EUMETSAT Data Store](https://data.eumetsat.int/product/EO:EUM:DAT:MSG:HRSEVIRI-IODC)) | Free EUMETSAT account; Data Store API (`eumdac` Python client) | **15 min**; "quarter-hourly with > 3 h latency, hourly if < 3 h" [V] | 3 km at nadir (45.5°E) → coarser (~4–5 km) over India [I] | 12 channels incl. 0.6, 0.8, 1.6, 3.9, 6.2, 7.3, 8.7, 9.7, 10.8, 12.0, 13.4 µm, HRV (1 km) | **From 2017-02-01; ~337,000 products** [V — EUMETSAT API query] | Yes (hourly NRT; latest product was 6 h old at query) [V] | Indian Ocean + all India | EUMETSAT "NRTLicense/GeneralLicense" [V]; free for research | ✅ **Yes — easiest large archive; richer channels (7.3 µm, 8.7 µm) than INSAT** | ✅ hourly live |
| **ERA5** ([CDS](https://cds.climate.copernicus.eu/)) | Free CDS account + `cdsapi` | 1 h | 0.25° (~28 km) | CAPE, CIN, TCWV, winds on levels, T, q | 1940– | ~5 days (ERA5T) | Global | Copernicus licence (free, attribution) | ✅ environment features | ❌ (latency) |
| **IMDAA** ([NCMRWF RDS](https://rds.ncmrwf.gov.in/)) | Registration on NCMRWF portal | 1 h (some 3 h) | 12 km | 57 vars, 63 levels | **1979–2020** [V] | ❌ | India | NCMRWF terms | ✅ **Indian reanalysis — organizer's own product; good optics** | ❌ |
| NCMRWF NCUM-G / NCUM-R / NEPS | [NCMRWF data portal](https://www.ncmrwf.gov.in/data/) | 1–6 h | 12 km (G), 4 km/1.5 km (R) | NWP fields | varies | [U] public NRT availability | India | [U] | ⚠️ if obtainable | ⚠️ [U] |
| **GFS 0.25°** ([NOMADS](https://nomads.ncep.noaa.gov/)) | Open HTTP (grib filter) | 1 h to 120 h | 0.25° | CAPE, CIN, PWAT, winds | ~10 days on NOMADS; archive at NCEI/AWS | ✅ | Global | US Gov open | ⚠️ | ✅ **live environment** |
| ECMWF IFS open data | Open (`ecmwf-opendata`) | 3–6 h steps | 0.25° | Standard fields incl. CAPE | recent | ✅ | Global | CC-BY-4.0 | ⚠️ | ✅ |
| **GPM IMERG V07** ([GES DISC](https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imerghhe-07)) | Free NASA Earthdata login | 30 min | 0.1° (~10 km) | Precip rate | 2000– | Early ~4 h latency [V] | 60°N–S | NASA open | ✅ heavy-rain labels | ⚠️ 4 h lag |
| **GSMaP** ([JAXA](https://sharaku.eorc.jaxa.jp/GSMaP/guide.html)); GSMaP ISRO on MOSDAC | JAXA registration (FTP); MOSDAC | 1 h (NRT, ~4 h lag); **GSMaP_NOW 0.5 h realtime** | 0.1° | Precip rate | 2000– | **GSMaP_NOW covers India via Meteosat since Nov 2018** [V] | Global | JAXA terms | ✅ | ✅ **near-live rain** |
| **GPM DPR 2A** (flagHeavyIcePrecip / flagGraupelHail) | Earthdata | per overpass | ~5 km footprint, 125 m vertical | 3D reflectivity, ice flags | 2014– | ~hours | 65°N–S swath | NASA open | ✅ **sparse hail/graupel validation** | ❌ |
| **ISS-LIS lightning** ([GHRC](https://www.earthdata.nasa.gov/data/catalog/ghrc-daac-isslis-v2-fin-2)) | Earthdata | Orbital snapshots (~90 s view per site) | ~4 km | Flashes, groups, events + background | **1 Mar 2017 – 16 Nov 2023** [V] | ❌ (mission ended) | ±55° | NASA open | ✅ **sparse but real lightning labels for 2017–2023** | ❌ |
| **NRSC Lightning Detection Sensor Network** ([Bhuvan lightning portal](https://bhuvan-app1.nrsc.gov.in/lightning/)) | Bhuvan portal (login); paper says data on NDEM & Bhuvan "with a lag of 1 day" [V — [Nat. Hazards 2021](https://link.springer.com/article/10.1007/s11069-021-05042-8)] | ms strokes | ~200 m | CG strokes | 2019?– [U] | 1-day lag (per 2021 paper) | India, 46 sensors | [U] — **NDEM URL returns 404 today; request access from NRSC** | ✅ **if access granted — best Indian label** | ❌ |
| IITM ILLN / Damini | Research request to IITM | ms | ~200 m | CG/IC | 2014– | App only | India, 83 sensors | Not open | ✅ if granted | ❌ |
| Blitzortung | Contributors only | real-time | ~km | Strokes | — | ✅ | Global | [**"not allowed to use the data ... for storm warning systems"**](https://www.blitzortung.org/) (search summary; verify on site) | ❌ **Do not use** | ❌ |
| WWLLN | Paid/academic licence | real-time | ~5–10 km | Strokes | 2004– | ✅ | Global | Commercial | ⚠️ if a university has it | ⚠️ |
| **IMD DWR raw volumes** | Licence / research request (MoES) [V] | 10 min | 250 m–1 km | Z, V, (W) | — | ❌ | ~40 radars | Restricted | ⚠️ only if granted | ❌ |
| IMD radar product **images** (`mausam.imd.gov.in/Radar/`) | Public web images | ~10 min | image | Colour-coded Z | Not archived publicly [U] | ✅ | Radar cities | Website terms (not a data licence) | ❌ (images, no calibration) | ⚠️ **display only, with attribution** |
| **MOSDAC 3D Volumetric TERLS DWR** ([page](https://www.mosdac.gov.in/3d-volumetric-terls-dwrproduct)) | MOSDAC SSO, "Open Access", `/opendata/volumetric_dwr_product/` | per volume scan | **1 km × 1 km × 250 m, 81×481×481, to 20 km** | De-cluttered Z, de-aliased V | **May 1–31, 2018 (Thiruvananthapuram, 6–11°N, 74–79°E)** [V] | ❌ | S. Kerala | Open Access | ✅ **the one verified open 3D Indian radar set → radar case study** | Replay only |
| ISRO SHAR S-band pol. DWR | MOSDAC (per [IJRS 2024](https://www.tandfonline.com/doi/abs/10.1080/01431161.2024.2388855)) | — | — | Pol. moments | [U] period | [U] | Sriharikota | [U] | ⚠️ verify on MOSDAC catalog | — |
| RainViewer API | No key; tiles | 10 min, past 2 h | tiles | Composite Z | 2 h only | ✅ | [U] India | Free for personal/educational; **no guarantee of availability; owners can withdraw** [V] | ❌ | ⚠️ optional display |
| **IMD AWS/ARG** | **Public portal locked May 2025**; paid via [dsp.imdpune.gov.in](https://dsp.imdpune.gov.in) [V — [DownToEarth](https://www.downtoearth.org.in/climate-change/imd-locking-up-its-awsarg-data-portal-hampers-public-weather-alerts-experts)] | 15 min | stations | T, RH, wind, rain | paid | restricted | India | Paid | ⚠️ | ❌ |
| IMD gridded rainfall 0.25° daily | IMD Pune | daily | 0.25° | Rain | 1901– | — | India | IMD | ⚠️ (daily too coarse) | ❌ |
| **IMD hailstorm report, NW India** ([PDF](https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf)) | Public PDF | daily list | station/town names | Hail occurrence by date & place | **Feb–May 2026** (updated 16 May 2026) [V] | — | J&K, HP, UK, Punjab, Haryana, Delhi, UP, Rajasthan | Public | ✅ **real hail labels (event level)** | ✅ replay |
| SEVIR ([AWS open data](https://registry.opendata.aws/sevir/)) | Open S3 | 5 min | 1–2 km | GOES VIS/IR, NEXRAD VIL, GLM | 2017–2019 | — | USA | MIT/AWS open | ✅ **pre-training & pipeline debugging only** | — |
| SRTM / CartoDEM, OSM, Census/admin boundaries, Bhuvan WMS | Open | static | 30–90 m | Terrain, roads, districts | — | — | India | Open | ✅ features | ✅ map layers |
| IMD radar network metadata ([Figshare](https://figshare.com/articles/dataset/Network_of_Doppler_Weather_Radars_of_India_Meteorological_Department/22704910)) | Open | static | — | Radar sites/bands/ranges | — | — | India | Open | — | ✅ coverage layer |

## 6.2 What this means for the design [I]

1. **Training backbone:** Meteosat-9 IODC (15 min, 2017→) and INSAT-3DR/3DS L1B (MOSDAC, 3-day latency) for 2020–2026 pre-monsoon and monsoon seasons. Environment from ERA5/IMDAA. That is enough for **self-supervised CI/lifecycle labels** (future BT fields).
2. **Real hazard labels, all sparse but real:**
   - Lightning: ISS-LIS 2017–2023 overpasses (and NRSC LDSN if access is granted).
   - Hail: IMD NW-India hail report (2026) + GPM DPR ice flags.
   - Heavy rain / cloudburst potential: IMERG/GSMaP rain rate ≥ thresholds.
3. **Radar:** one real 3D case study (TERLS, May 2018). IMD DWR goes in as a "plug-in if access is granted" interface, with PyScanCf readers ready.
4. **Live demo:** Meteosat-9 hourly NRT + GSMaP_NOW + GFS for the "live" screen. INSAT L1B runs in replay mode (≥ 3-day lag for general users). Be explicit about which is which.
5. **Resolution honesty:** native satellite IR is ~3–4 km (VIS 1 km by day). Put the product on a **2 km grid** and state that the *effective* resolution is ~4 km IR. The only 1 km observed data is TERLS radar, plus VIS channels in daytime. This lands inside the PS's 1–3 km band without pretending.
6. **Do not recommend:** training on Blitzortung (terms), on scraped IMD PNGs (not calibrated data), or on DGMR/NowcastNet-scale models (compute).

---

# PART 7 — THE REAL TECHNICAL GAPS

Scores are 1–5 (5 = best/most favourable; for "Dev time", 5 = fastest). All are **[I]** judgments.

| # | Gap | Evidence it's a gap | Novelty | Tech feas. | Data feas. | SIH relevance | Demo impact | Research cred. | Dev time |
|---|---|---|---|---|---|---|---|---|---|
| G1 | **Real-label verification of Indian nowcasts vs baselines** | No inspected SIH26084/26072 repo has CSI/FAR on observed Indian labels; VARSHANET's metrics come from synthetic data | 3 | 5 | 4 | 5 | 4 | 5 | 4 |
| G2 | **Satellite-first CI detection with physically grounded interest fields** (cooling rate, WV−IR, tri-spectral) + ML, labels self-supervised | Operational abroad (RDT, CIUnet); no Indian open implementation found | 3 | 4 | 5 | 5 | 4 | 5 | 4 |
| G3 | **Lifecycle *transition* forecasting** (P(phase change in 30/60 min), time-to-peak, time-to-decay via survival analysis) | RDT/TRT describe the current phase; transition probabilities/survival curves are rarer in products [I] | 4 | 4 | 5 | 4 | 5 | 4 | 3 |
| G4 | **Merge/split genealogy** tracked and used as a predictor | tobac supports it; no student repo uses it | 3 | 4 | 5 | 3 | 5 | 4 | 4 |
| G5 | **Calibrated probabilities** (reliability diagrams, isotonic) per hazard | Students show MC-dropout bands without validation | 3 | 5 | 4 | 4 | 3 | 5 | 5 |
| G6 | **ETA with conformal prediction intervals** ("arrives in 38 min, 90 % interval 29–51 min") with *measured* coverage | Countdown clocks exist; calibrated intervals do not [I] | 4 | 5 | 5 | 5 | 5 | 4 | 5 |
| G7 | **Transfer of an operational lightning model (LightningCast) to INSAT/SEVIRI**, evaluated on ISS-LIS | lc_br did Brazil; no India transfer found | 4 | 3 | 3 | 5 | 4 | 5 | 3 |
| G8 | **Hazard-specific evidence chains** (why hail? → cold overshooting top + high CAPE/freezing level + DPR ice flag climatology) | Students show one generic "risk score" | 3 | 4 | 3 | 5 | 5 | 4 | 3 |
| G9 | **Advection-informed deep model for the 2–6 h extension** (Metzl et al. 2025 recipe) | Not seen in Indian student work | 4 | 3 | 4 | 4 | 3 | 5 | 2 |
| G10 | **Data-health-aware graceful degradation** (radar missing → satellite-only confidence reduced, shown in UI) | STORMTRACE claims fallback; no quantified skill-by-source-availability [I] | 3 | 4 | 4 | 4 | 4 | 3 | 4 |
| G11 | **Cross-source consistency / false-alarm suppression** (cirrus/anvil false CI rejected with tri-spectral + VIS texture) | CIUnet shows tri-spectral BTD cuts FAR | 3 | 4 | 5 | 4 | 3 | 4 | 4 |
| G12 | **Orographic cloudburst potential** (quasi-stationary cell + extreme rain rate + steep terrain + slow motion) | Cloudburst student work is tabular/point-based | 3 | 3 | 3 | 5 | 4 | 3 | 3 |
| G13 | **Source-ablation study** (skill with/without NWP, WV channels, previous frames) | c4dl-multi did it for Switzerland; nobody for India [I] | 3 | 4 | 4 | 3 | 2 | 5 | 4 |

**Trade-offs (no winner declared):**
- **G1 + G5 + G6** are cheap, rigorous and demo-friendly, but novelty is moderate. They are what makes everything else believable.
- **G3 + G4** best fit your lifecycle vision and give a strong demo, but you must define phases objectively and validate them, or they will look like hand-waving.
- **G7** has high research credibility and is India-specific, but depends on handling the GPL licence and on ISS-LIS label sparsity.
- **G9** is the only credible route to real skill beyond 2 h, but it is the most time-consuming. Consider it a stretch goal.
- **G12** is the most "on-PS" (cloudbursts), but it has the weakest ground truth. Present it as *potential*, not probability.

---

# PART 8 — THREE ARCHITECTURES

## Architecture A — Conservative / highly feasible (CPU-only)

```
 Meteosat-9 IODC (15 min) ─┐                     ┌─► CI detector (LightGBM on interest fields)
 INSAT-3DR/3DS L1B (MOSDAC)├─► Regrid to 2 km ──►│
 ERA5 / GFS environment ───┘   + QC + parallax   ├─► tobac tracking (detect → segment → link → merge/split)
                                                  │         │
                                                  │         ▼
                                                  │   Per-cell feature table (BT min, cooling rate, area growth,
                                                  │   WV−IR, CAPE, shear, motion, age, parent/child)
                                                  │         │
                                                  │         ▼
                                                  ├─► LightGBM heads: phase-transition, lightning, heavy-rain, hail-potential
                                                  ├─► pysteps optical flow → track extrapolation → ETA + conformal interval
                                                  └─► Alert engine (district polygons, CAP 1.2)
 FastAPI + PostGIS/TimescaleDB ─► React + MapLibre dashboard with replay
```

| Layer | Choice |
|---|---|
| Data pipeline | `eumdac` (EUMETSAT) + `mdapi.py` (MOSDAC) + `cdsapi` (ERA5); Prefect or plain cron; files → Zarr |
| Preprocessing | satpy resample to 2 km equal-area grid over India; BT from radiances; parallax correction (satpy has one) optional; land/sea & DEM |
| Features | Mecikalski-style interest fields: 10.8 µm BT, 15/30-min ΔBT, WV(6.8/6.2/7.3)−IR BTD, 8.7−10.8−12.0 tri-spectral, VIS texture (day), cell area growth, min BT, overshooting-top flag (BT < 215 K and colder than anvil mean by 6 K — tune), environment CAPE/CIN/shear/PWAT/freezing level |
| ML | LightGBM (per-cell tabular), logistic regression baseline, isotonic calibration |
| Training | Seasons 2019–2025 (Mar–Sep), split **by date** (never random pixels) |
| Inference | Every 15 min; < 1 min on CPU |
| DB | PostgreSQL + PostGIS (cells, tracks, alerts); files in Zarr/COG |
| APIs | `/cells?time=`, `/cells/{id}/history`, `/forecast/grid?lead=`, `/eta?lat&lon`, `/alerts/cap`, `/health`, `/replay/{event}` |
| Frontend | React + MapLibre GL + deck.gl; Recharts |
| GIS | District boundaries (Census/Bhuvan WMS), radar coverage rings, DEM hillshade |
| Alert engine | Rule layer on calibrated probabilities + ETA intervals; CAP 1.2 XML |
| Validation | Object-based CSI/POD/FAR for CI; Brier/reliability for probabilities; ETA MAE + interval coverage |
| Deployment | Docker Compose; one VM; data volume |

## Architecture B — Advanced / research-oriented (A + gridded deep learning; 1 GPU/Colab)

Everything in A, plus:

| Addition | Detail |
|---|---|
| Gridded deep model | **Advection-informed U-Net** (Metzl et al. 2025): inputs = last 4 frames + pysteps-advected future inputs at each lead; outputs = P(deep convection: BT < 235 K) at 30/60/120/180/240/360 min; SmaAt-UNet-style (re-implemented) or OpenSTL SimVP |
| Lightning | **LightningCast transfer**: run the pre-trained model zero-shot on INSAT/SEVIRI 0.6/1.6/10.8/12.0 µm (with resolution/spectral-response adaptation) → fine-tune head with ISS-LIS labels → compare zero-shot vs fine-tuned vs from-scratch |
| Uncertainty | Deep ensemble (5 seeds) + conformal calibration; spread–skill plots |
| Explainability | SHAP (tabular), permutation importance by channel group, integrated gradients / occlusion maps (U-Net) |
| Radar case | TERLS May 2018: TINT tracking, MESH/POSH hail proxies, 35 dBZ at −10 °C lightning proxy, compared with the satellite-only pipeline over the same cells ("how much does radar add?") |
| Validation | Adds FSS at 10/20/40 km, skill vs lead time 0–6 h, source ablation |

## Architecture C — Ambitious / highly differentiated (B + generative ensembles; GPU-days)

| Addition | Detail |
|---|---|
| Generative nowcast | Latent diffusion (LDCast/PreDiff/DDMS-style) on satellite BT → 10–20 member ensembles to 6 h |
| Ensemble lifecycle | Run tobac on **each member** → a distribution over future cell tracks, phases and merges → P(cell #27 reaches mature + lightning by 14:30) as ensemble frequency |
| Multi-model disagreement | Disagreement between optical flow, U-Net, diffusion ensemble and NWP (GFS/NCUM) as an uncertainty signal |
| Blending | Lead-time-dependent weights learned on validation (pysteps-blending style) |
| Risk | Training cost, instability, limited time to validate. Most likely outcome: one impressive case study, not a verified system |

## Trade-offs [I]

| Aspect | A | B | C |
|---|---|---|---|
| Buildable in ~30 days by 6 students | Yes | Yes, with discipline | Only partially |
| Compute | Laptop | Colab/1 GPU | Multi-GPU days |
| Judge-proof verification | Strong (simple, complete) | Strongest (baselines + ablations) | Risky (hard to verify well in time) |
| Novelty signal | Moderate | High | Highest, but most "just like the papers" |
| 2–6 h skill | Weak (extrapolation) — show honestly | Moderate (advection-informed DL) | Potentially best |
| Failure mode | "Looks traditional" | Scope creep | Nothing finished |

**Direction (with trade-offs, not a guarantee):** make **A** the floor that must work end-to-end by Day 14, add **B's** U-Net, LightningCast transfer and TERLS radar case as stretch goals, and treat **C** as future work in the PPT (one slide).

---

# PART 9 — "STORM LIFECYCLE INTELLIGENCE": IS IT NOVEL?

## 9.1 What already exists [V]

| System | What it does that overlaps your idea |
|---|---|
| **NWCSAF RDT-CW** ([description](https://www.nwcsaf.org/rdt_description_2025), [CWG](https://cwg.eumetsat.int/rapidly-developing-thunderstorm/)) | Satellite-based detection and tracking of convective cells, **development phase** (contour colour), severity, cloud-top cooling rate, trajectory, forecast ≤ 1 h |
| **MeteoSwiss TRT** ([MeteoSwiss](https://www.meteoswiss.admin.ch/about-us/research-and-cooperation/projects/en/2002/trt.html)) | Radar cell tracking + **severity rank** + 1-h extrapolation |
| **NOAA ProbSevere v3** ([WAF 2024](https://journals.ametsoc.org/view/journals/wefo/39/12/WAF-D-24-0076.1.pdf)) | Per-storm objects with **P(hail), P(wind), P(tornado)** from GBDT, predictors shown per storm — operational Aug 2025 |
| **tathu** ([GitHub](https://github.com/uba/tathu)) | Open-source convective-system **life-cycle** tracking |
| pysteps T-DaTing | MeteoSwiss-style cell tracking inside pysteps |
| IMD WDSS-II | Radar cell tracking/nowcast 0–2 h at 156 cities |

**Verdict [I]:** Your *output card* ("Cell #27, mature, NE @ 32 km/h, +40 % growth, P(hail)…") is essentially **RDT + ProbSevere**. That is good news: judges will recognise it as scientifically legitimate. But if you pitch it as "the first system to understand storm lifecycles", an NCMRWF scientist can dismiss it in one sentence.

## 9.2 How to differentiate further [P]

1. **Forecast the transitions, not just the phase.** Output P(Developing→Mature within 30/60 min), P(decay within 60 min), and **expected remaining lifetime** from a discrete-time survival model (LightGBM with a hazard target, or `lifelines`/`scikit-survival`). RDT reports the *current* phase; this predicts the *next* one. Validate it with Brier score per horizon and concordance index.
2. **Make phases objective and reproducible.** Define phases from measurable quantities (min BT trend, area trend, OT presence, lightning/rain trend), e.g.:
   - *Initiation:* first detection at BT < 273 K with cooling ≤ −4 K/15 min
   - *Developing:* area ↑ and min BT ↓
   - *Mature:* min BT < 221 K, area stable ±10 %, OT present or max rain
   - *Decaying:* min BT ↑ ≥ 4 K/30 min and area of coldest core ↓

   Publish the rule table. Report **inter-method agreement** with a simple clustering (e.g., HMM on trends) as a sanity check.
3. **Genealogy as a predictor.** Use merge/split history (tobac `merge_split`) as features, and test whether "recently merged" cells intensify more. That is a measurable, testable hypothesis — a mini research result.
4. **Calibrated ETA intervals.** Conformal intervals on arrival time per district/town, with **empirical coverage reported** ("90 % intervals contained the true arrival 88 % of the time on 2025 test events").
5. **India-specific, satellite-first, radar-optional.** RDT needs NWCSAF licensing for NMHSs; ProbSevere needs NEXRAD/GLM. Your pitch: *an open, India-trained, satellite-first lifecycle engine that runs today on INSAT/Meteosat and plugs into IMD DWR when available.* That is a practical gap [I].
6. **Lightning via transfer learning** (G7) with measured skill on ISS-LIS. This is an honest answer to "where is your lightning data?".
7. **Evidence-linked explanations.** Each card lists its top SHAP contributors *with the raw value and its climatological percentile* ("cooling −9 K/15 min — 97th percentile for May, NW India"), not generic words.

## 9.3 Proposed card (data-backed version) [P]

```
CELL #27  (born 13:15 IST; parent of #31 after split 14:00)
Phase now: MATURE (since 13:55)           P(decay in next 60 min): 0.34 (calibrated)
Motion: 062° @ 31 km/h (90% CI 24–38)     Expected remaining life: 75 min (IQR 45–110)
Growth: area +38%/30 min, min BT 208 K (−11 K/30 min)
Next 60 min:  lightning 0.81 · heavy rain ≥20 mm/h 0.46 · hail potential: HIGH (proxy)
ETA → Karnal: 38 min (90% conformal interval 29–51)   Coverage on 2025 test: 88%
Why: [1] cooling −11 K/30 min (p97)  [2] OT detected  [3] CAPE 2600 J/kg (p90)  [4] merged w/ #22 at 13:40
Data used: Meteosat-9 ✓  INSAT-3DS ✓ (replay)  GFS ✓  Radar ✗ (no coverage)  → confidence −1 tier
```

---

# PART 10 — MINIMUM SCIENTIFICALLY CREDIBLE MVP

Scope: **NW India + Indo-Gangetic Plain (26–34°N, 72–84°E)** for pre-monsoon (Mar–Jun), plus one Kerala radar case. [P]

| # | Requirement | Concrete implementation |
|---|---|---|
| 1 | Real dataset | Meteosat-9 IODC SEVIRI 15-min, Mar–Jun 2019–2026 (start with 2023–2026 if storage is tight: ~a few hundred GB for a cropped domain [I]); INSAT-3DR/3DS L1B for event days; ERA5 hourly; IMERG 30-min; ISS-LIS 2019–2023; IMD hail report 2026; GPM DPR 2A overpasses |
| 2 | Real preprocessing | satpy → BT, crop, resample to 2 km; ΔBT over 15/30 min; BTD features; ERA5 → MetPy CAPE/CIN/shear/freezing level interpolated to cell centroid & time |
| 3 | Real baseline | (a) persistence; (b) pysteps Lucas–Kanade + semi-Lagrangian extrapolation of BT; (c) **Mecikalski rule-based CI** (≥ 4 of 6 interest-field thresholds) |
| 4 | Real ML model | LightGBM per-cell models: CI (is this young cloud going to reach BT < 235 K within 60 min?), phase transition, lightning (ISS-LIS), heavy rain (IMERG ≥ 10/20 mm/h in 30–60 min) |
| 5 | Real prediction | Cells tracked with tobac every 15 min; probabilities + motion + ETA per district centroid |
| 6 | Real evaluation | Train 2019–2023, validate 2024, **test 2025–2026**; object-based CSI/POD/FAR; Brier/BSS; reliability; ETA MAE + conformal coverage |
| 7 | Real GIS | MapLibre + district polygons; cell polygons from segmentation (GeoJSON); radar coverage rings |
| 8 | Real replay | 6–8 events (Part 12) with frozen "as-of" inputs |
| 9 | Confidence | Isotonic-calibrated probabilities; conformal ETA intervals; data-availability tier |
| 10 | Explainability | SHAP per prediction (TreeExplainer), top-4 reasons with percentiles; permutation importance by feature group |

## 10.1 Exact implementation steps [P]

1. **Accounts (Day 1):** EUMETSAT (instant), NASA Earthdata (instant), Copernicus CDS (instant), MOSDAC SSO (can take days — apply now), JAXA GSMaP (hours–days), NCMRWF RDS (IMDAA). Email NRSC for LDSN lightning access and IITM for ILLN (long shot; mention it in the PPT as "requested").
2. **Download scripts:** `pipelines/ingest/eumetsat_seviri.py` (eumdac, bbox, 15-min, native format), `pipelines/ingest/mosdac_insat.py` (wraps `mdapi.py`), `era5.py`, `imerg.py`, `isslis.py`, `gpm_dpr.py`.
3. **Grid & QC:** one India equal-area 2 km grid (`gis/grid.py`); satpy `resample(..., resampler="nearest"/"bilinear")`; flag missing slots; write Zarr by day.
4. **Tracking:** tobac `feature_detection_multithreshold` on −BT with thresholds [273, 253, 235, 221, 208 K]; `segmentation_2D` watershed at 245 K; `linking_trackpy` with the velocity predictor; `merge_split_MEST`. Store cells/tracks in PostGIS.
5. **Labels:**
   - CI: a feature first seen at BT < 273 K whose track reaches BT < 235 K within 60 min → positive; tracks that never do → negative.
   - Phase: rule table in §9.2.
   - Lightning: ISS-LIS flashes within the cell polygon ±5 min during overpass windows (only cells observed by LIS enter the lightning dataset).
   - Heavy rain: IMERG max rate within polygon in next 30/60 min.
   - Hail (event-level): IMD report stations within 25 km of a cell track on that date → positive; other tracked mature cells that day in the same region with no report → unlabelled (don't call them negative).
6. **Features:** per-cell time series stats (last 30/60 min), environment at centroid, genealogy counts, local time, DEM stats.
7. **Train:** LightGBM with `class_weight` / focal-like scale; time-blocked CV by season; calibrate with isotonic on validation.
8. **Baselines:** compute the same metrics for persistence, pysteps extrapolation and Mecikalski rules.
9. **ETA:** extrapolate the cell polygon along its motion (Kalman-smoothed) → first-touch time for each district polygon; build a residual set on validation → split-conformal 80/90 % intervals.
10. **Serve:** FastAPI endpoints; precompute replay bundles; React UI.
11. **Report:** `evaluation/report.ipynb` → HTML with every table and figure used in the PPT (reproducible numbers).

---

# PART 11 — BASELINE VS OUR MODEL: SCIENTIFIC COMPARISON

## 11.1 Tasks, baselines, metrics [P]

| Prediction task | Truth / label | Baselines | Our model | Metrics (why) |
|---|---|---|---|---|
| **CI detection** (will young cloud become deep convection in ≤ 60 min) | Future BT < 235 K on same track | Mecikalski rules; persistence (no CI) | LightGBM on interest fields + env | **POD, FAR, CSI, bias** on a performance diagram (Roebber 2009); **lead time gained** (min before first 235 K) — events are rare, so avoid accuracy |
| **Gridded deep-convection probability** (0–6 h) | BT < 235 K mask | Persistence; pysteps extrapolation; Lagrangian persistence | U-Net (B) | **FSS at 10/20/40 km** (handles displacement); CSI at p ≥ 0.5; **Brier/BSS**, reliability curve per lead |
| **Cell motion / position** | Observed centroid at t+Δ | Persistence of last vector; pysteps field motion | Kalman-smoothed track | **Centroid position MAE (km)** by lead; **IoU** of predicted vs observed polygon |
| **ETA to district/town** | First observed touch time | Constant-velocity ETA | Tracked ETA + conformal interval | **ETA MAE (min)**, **interval coverage** vs nominal (80/90 %), mean interval width |
| **Lifecycle transition** | Rule-based phase at t+30/60 | "Stay in current phase"; climatological transition matrix | LightGBM/survival | **Brier score** per horizon, **reliability**, **C-index** for time-to-decay; macro-F1 for next-phase class |
| **Lightning in 60 min** | ISS-LIS flash in cell (overpass-restricted) | BT < 235 K rule; zero-shot LightningCast | Fine-tuned LightningCast / LightGBM | **POD/FAR/CSI** at the optimal threshold, **AUPRC** (imbalanced), **BSS**, reliability |
| **Heavy rain ≥ 20 mm/h** | IMERG/GSMaP | Persistence; extrapolated IMERG | LightGBM / U-Net | CSI at 10/20 mm/h thresholds; FSS; **RMSE/MAE only for rain rate magnitude** (not for yes/no) |
| **Hail potential (event-level)** | IMD hail reports; DPR ice flags | CAPE-only rule; OT-only rule | LightGBM hail-potential | POD at report locations; **FAR not fully measurable** (reports are incomplete) → state this; ROC on DPR-overpass subset |
| **Downburst potential** | No labels | DCAPE + rapid collapse rule | — (heuristic only) | Case-study only; say explicitly that it is not verified |

## 11.2 Protocol rules [P]

- **Split by time, not by pixel** (e.g., test = 2025 + 2026 seasons). Random pixel splits leak neighbouring information.
- Report **skill score vs baseline** (e.g., CSI_model − CSI_extrapolation) with **bootstrap 95 % CIs over event days**.
- One **fixed** evaluation script produces every number in the PPT; commit its hash.
- Show a **skill-vs-lead-time curve** (0–6 h) for every method. Expect every curve, including yours, to decay.

---

# PART 12 — HISTORICAL EVENT REPLAY

## 12.1 Candidate events

| # | Date (IST) | Location | Hazard | Data available (verified dataset coverage for that date) | Source | Why useful |
|---|---|---|---|---|---|---|
| E1 | **1–31 May 2018** (pick 2–3 storm days) | Thiruvananthapuram / S. Kerala | Pre-monsoon thunderstorms | **TERLS 3D DWR (1 km)** ✓, INSAT-3D/3DR ✓, Meteosat-8 IODC ✓, ERA5 ✓, IMERG ✓, ISS-LIS ✓ | [MOSDAC TERLS](https://www.mosdac.gov.in/3d-volumetric-terls-dwrproduct) | **Only open 3D radar case** → satellite vs radar comparison, hail/lightning radar proxies |
| E2 | **25 June 2020** | Bihar (Gopalganj, Darbhanga, Siwan...) & UP | **Lightning** (83 deaths in Bihar) | Meteosat-8 IODC ✓, INSAT-3D/3DR ✓, ERA5 ✓, IMERG ✓, **ISS-LIS ✓ (if an overpass hit)** | [Tribune](https://www.tribuneindia.com/news/nation/thunderstorm-lightning-kill-110-people-in-bihar-up-pm-modi-rahul-condole-deaths-104383), [Gulf News](https://gulfnews.com/world/asia/india/india-lightning-kills-83-villagers-in-bihar-in-single-day-1.72252592) | Lightning-safety narrative; tests the lightning head |
| E3 | **13 May 2024**, afternoon | Mumbai (Ghatkopar) / Thane | Dust storm + thunderstorm squall; hoarding collapse (16–17 deaths) | Meteosat-9 ✓, INSAT-3DR ✓, ERA5 ✓, IMERG ✓ (ISS-LIS ✗, ended 2023) | [NDRF](https://ndrf.gov.in/en/operations/ndrf-responds-billboard-collapse-ghatkopar-mumbai), [CBS](https://www.cbsnews.com/news/mumbai-billboard-collapse-india-deaths-injured-dust-storm) | Downburst/squall ETA case for a megacity |
| E4 | **2 May 2025**, ~05:15–08:30 | Delhi-NCR | Severe thunderstorm, 77 mm in ~3 h at Safdarjung, gusts 80 km/h | Meteosat-9 ✓, INSAT-3DR/3DS ✓, ERA5 ✓, IMERG ✓ | [DownToEarth](https://www.downtoearth.org.in/climate-change/delhi-rainstorm-likely-caused-by-multitude-of-global-and-local-factors) | Night/early-morning CI (no VIS) → tests IR-only path; station gusts give downburst anecdote |
| E5 | **30 Jun–1 Jul 2025** (night) | Mandi, Himachal Pradesh | ~12 cloudburst incidents, 14 deaths | Meteosat-9 ✓, INSAT-3DS ✓, ERA5 ✓, IMERG/GSMaP ✓ | [Springer Landslides 2026](https://link.springer.com/article/10.1007/s10346-026-02703-2), [AIR](https://www.newsonair.gov.in/monsoon-fury-continues-in-himachal-pradesh-with-two-more-cloudbursts-reported-from-mandi-and-chamba) | Orographic, quasi-stationary cells → cloudburst-potential module |
| E6 | **5 Aug 2025**, ~13:45 | Dharali, Uttarkashi (Uttarakhand) | Cloudburst / flash flood (IMD did not immediately confirm "cloudburst") | Meteosat-9 ✓, INSAT-3DS ✓, ERA5 ✓, IMERG ✓ | [ThePrint](https://theprint.in/environment/flash-floods-due-to-heavy-rainfall-in-uttarkashis-dharali-but-imd-yet-to-confirm-cloudburst/2715087/), [Springer Landslides](https://link.springer.com/article/10.1007/s10346-026-02719-8), [Wikipedia](https://en.wikipedia.org/wiki/2025_Uttarakhand_flash_flood) | Teaches the "cloudburst verification problem" honestly |
| E7 | **14 Aug 2025**, ~11:30 | Chasoti, Kishtwar (J&K) | Cloudburst / debris flow (≥ 68 deaths) | Meteosat-9 ✓, INSAT-3DS ✓, ERA5 ✓, IMERG ✓ | [Wikipedia](https://en.wikipedia.org/wiki/2025_Kishtwar_district_flash_flood), [AIR](https://www.newsonair.gov.in/jk-cloud-burst-in-kishtwar-10-feared-dead) | Daytime Himalayan cloudburst (VIS available) |
| E8 | **1 May 2026** & **14 May 2026** | Haryana (Ambala, Karnal, Kurukshetra), Delhi-NCR, W. UP (Agra, Bareilly), Uttarakhand | **Hail** at many stations | Meteosat-9 ✓, INSAT-3DS ✓, ERA5 ✓, IMERG ✓, GPM DPR (check overpass) | [IMD NW-India hail report](https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf) | **Real multi-station hail labels on the same day** → hail-potential verification |
| E9 | **Mar–Apr 2026** (pick dates from the IMD report: 21 Mar, 5 Apr, 9 Apr) | UP, Haryana, Rajasthan, Uttarakhand | Hail + crop damage (6.27 lakh ha affected nationally) | Same as E8 | [DownToEarth](https://www.downtoearth.org.in/climate-change/pre-monsoon-season-emerging-as-new-high-risk-period-for-crops-analysis-shows), [IMD report](https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf) | Farmer-impact story + more hail labels |

**Rule [P]:** keep E3–E9 **out of training** (test only). Say so on the replay screen.

## 12.2 Replay design [P]

**Timeline (per event):** T−60, T−45, T−30, T−15, T0 (first reported impact), then T+15 … T+6 h, all in 15-minute steps.

**Freezing "what the system knew":** for each step `t`, the replay bundle contains **only inputs with timestamp ≤ t**, with realistic latency applied:
- Meteosat: available at t+10 min
- INSAT L1B: in operational mode not available for 3 days → shown greyed as "not available operationally (general-user latency)"
- GFS: last cycle available at t
- IMERG Early: t−4 h

`pipelines/replay/build_bundle.py` writes `replay/{event}/{t}.json` with cells, forecasts, the data manifest and a hash.

**Three synchronized panes:**
1. **"System knew"** — observed BT/radar at t, tracked cells, data-health badges.
2. **"System predicted"** — forecast cells at t+Δ, probability fields, ETA countdowns with intervals, alerts it *would* have issued (and when).
3. **"What happened"** — observed cells at t+Δ, IMERG rain, ISS-LIS flashes / IMD hail reports, news-reported impact time.

**Scorecard strip:** for this event — alert lead time (min), hits/misses/false alarms per district, ETA error.

**Controls:** scrubber, play/pause, lead-time selector, "show baseline instead" toggle, so judges can compare optical flow vs your model on the same frame.

---

# PART 13 — PRODUCT / UI (forecaster-grade)

| # | Screen | Exact components |
|---|---|---|
| 1 | **Live Situation** | MapLibre base (dark/light), IR BT layer (colour-enhanced 200–300 K), cell polygons coloured by phase, motion arrows, district choropleth of max P(hazard) in next 60 min; data-health bar (per source: last timestamp, latency, status); UTC/IST clock; "operational vs replay" banner |
| 2 | **Storm Cell Tracker** | Sortable cell table (ID, phase, age, min BT, cooling rate, speed/dir, P(lightning/heavy rain), hail potential, ETA to nearest town); click → cell card (§9.3); **lifecycle sparkline** (min BT, area, P(decay)); **genealogy tree** (merge/split, D3 tree) |
| 3 | **0–6 h Forecast Timeline** | Lead-time slider (0–360 min), probability fields per hazard, **skill-by-lead ribbon** (validated CSI/BSS at each lead, so users see confidence fall), NWP-vs-nowcast blend weight indicator |
| 4 | **Historical Replay** | Event picker (E1–E9), three synced panes (knew / predicted / happened), scrubber, baseline toggle, event scorecard |
| 5 | **Hazard Map** | Toggle lightning / heavy rain / hail potential / cloudburst potential / downburst potential; threshold slider; district & tehsil polygons; DEM hillshade for orographic context; radar coverage rings (IMD network metadata) |
| 6 | **Explainability Panel** | Per-cell SHAP waterfall with raw values + climatological percentile; feature-group importance (satellite vs environment vs genealogy); for the U-Net: occlusion/IG map overlay; physics checklist (CAPE, shear, freezing level) |
| 7 | **Confidence / Uncertainty** | Reliability diagram per hazard (from test set); ETA conformal-interval "cone" on map; spread of deep ensemble (B); data-availability tier and its measured skill penalty |
| 8 | **Alert Center** | Alert queue (draft → forecaster approve → issued), CAP 1.2 XML preview/download, affected districts, lead time, **auto-expiry** when a cell decays, audit log |
| 9 | **Model Performance** | Test-set tables: our model vs persistence vs extrapolation vs rules; performance diagram; FSS vs scale; ETA coverage; per-season/per-region breakdown; model card (training period, labels, known failure modes) |
| 10 | **Data Health** | Per-source ingestion timeline (gaps highlighted), latency histograms, QC flags (striping, missing lines), licence/terms of each source, "what we would add with IMD DWR/lightning access" |

**Design principles [P]:** forecaster-first (dense tables, keyboard shortcuts, UTC toggle), every number traceable to a model version and data timestamp, and no animation that doesn't carry information.

---

# PART 14 — TEN TECHNICAL DIFFERENTIATORS (with public-prior-art check)

| # | Feature | What's technically real about it | Already in public student/SIH repos? | Already in research/operations? |
|---|---|---|---|---|
| 1 | **Object-based verification dashboard** (cell CSI, ETA error, coverage) | Matching algorithm + bootstrap CIs | **No** (none found) | Yes (ProbSevere, TRT verification) |
| 2 | **Lifecycle transition probabilities + remaining-lifetime survival curve** | Discrete-time hazard model per cell | **No** | Rare in products [I]; RDT gives phase only |
| 3 | **Merge/split genealogy tree used as predictor** | tobac `merge_split` + feature ablation test | **No** | tobac supports tracking; its predictive use is less common [I] |
| 4 | **Conformal ETA intervals with measured coverage** | Split conformal on validation residuals | **No** (countdowns exist, intervals don't) | Conformal is established in ML; rare in nowcast products [I] |
| 5 | **Calibrated probabilities with reliability diagrams** | Isotonic calibration, BSS | **No** (MC-dropout bands exist, e.g., STORMTRACE) | Standard in operations |
| 6 | **LightningCast transfer to INSAT/SEVIRI evaluated on ISS-LIS** | Zero-shot vs fine-tuned comparison | **No** | lc_br did Brazil; not India [V searched] |
| 7 | **Self-supervised CI labels from future satellite frames** | Label generation from tracks | **No** | Common in research (CI literature) |
| 8 | **"What the system knew" replay with latency-faithful data manifests** | Time-sliced bundles + hashes | Partial (ThunderWatch has replay; not latency-faithful) | Standard in verification practice |
| 9 | **Satellite-vs-radar ablation on the TERLS case** ("value of radar") | Same cells, two pipelines | **No** | Similar to c4dl-multi source ablation |
| 10 | **False-alarm suppression via tri-spectral / VIS texture gating + measured FAR drop** | Ablation: FAR with/without the gate | **No** | CIUnet (2024) reports a FAR reduction from tri-spectral BTD |

Other ideas you listed, checked:
- **Uncertainty cone:** common in cyclone products; not seen in student nowcasting repos. Build it from conformal residuals, not by hand.
- **Multi-model disagreement:** STORMTRACE-style repos mention multimodal fallback, not disagreement metrics. Keep it for Architecture C.
- **Explainable alert:** "feature importance" is already common (VARSHANET, DevshreevasAI). Differentiate with per-prediction SHAP + percentiles.
- **Hazard transition prediction:** not found in student repos.

---

# PART 15 — DO NOT BUILD

| ❌ Don't build | Why |
|---|---|
| Synthetic-data-trained models with reported metrics | VARSHANET-style R² on `np.random.uniform` data will be exposed by one question |
| Random/rule-generated "probabilities" shown as AI output | Violates your own goal; judges test it by asking for the training set |
| ConvLSTM as the headline novelty | It's the most common choice in the competitor repos |
| Training DGMR/NowcastNet/MetNet/diffusion from scratch as the core | Compute and data you don't have; unfinished risk |
| Custom NWP or WRF runs | Weeks of compute/tuning; NCMRWF already runs NCUM-R 1.5 km |
| Hardware/IoT sensors, LoRa nodes, sirens | Software PS; no evaluation benefit |
| Mobile app, 13-language UI, chatbots, LLM "forecaster" | Cosmetic for this PS; one Hindi/English toggle is enough |
| Blockchain/"cryptographic audit" | No problem solved |
| Scraping IMD radar PNGs as model input | Not calibrated data; terms unclear; judges from MoES will notice |
| Using Blitzortung data | Its terms prohibit storm-warning use |
| Claiming 1 km resolution from interpolation | Say "2 km grid, ~4 km effective IR resolution" |
| Plain "accuracy" on rare events | Use CSI/POD/FAR/BSS |
| Kubernetes/microservices sprawl | Docker Compose is enough |
| Global coverage | Pick NW India + IGP (+ Kerala radar case) |
| Copying any competitor repo or unlicensed research code | Plagiarism risk; the SIH "must be new" clause |

---

# PART 16 — REPOSITORY STRUCTURE

```
sih26084-storm-lifecycle/
├── README.md                 # What's real / proxied / future; how to reproduce every number
├── LICENSE                   # Your licence choice (see Part Q on GPL dependencies)
├── docker-compose.yml
├── Makefile                  # make data, make train, make eval, make replay, make up
├── configs/                  # YAML: domain, grid, thresholds, event list, model hyper-params
├── data/                     # (git-ignored) raw/ interim/ processed/ + README with provenance
│   ├── raw/{seviri,insat,era5,imerg,isslis,gpm_dpr,terls,hail_reports}/
│   ├── interim/zarr/         # regridded 2 km daily cubes
│   └── processed/            # cell tables (parquet), labels, splits
├── pipelines/
│   ├── ingest/               # eumetsat_seviri.py, mosdac_insat.py (mdapi wrapper), era5.py, imerg.py, isslis.py, gpm_dpr.py, terls.py, gfs_live.py
│   ├── preprocess/           # calibrate_bt.py, regrid.py, qc.py, parallax.py, env_features.py
│   ├── tracking/             # tobac_run.py, genealogy.py, phases.py
│   ├── labels/               # ci_labels.py, lightning_labels.py, rain_labels.py, hail_labels.py
│   └── replay/               # build_bundle.py (latency-faithful as-of snapshots)
├── ml/
│   ├── features/             # cell_features.py, interest_fields.py
│   ├── models/               # lgbm_ci.py, lgbm_hazards.py, survival.py, unet_advect.py (B), lightningcast_transfer.py (B)
│   ├── calibration/          # isotonic.py, conformal_eta.py
│   ├── explain/              # shap_cells.py, permutation_groups.py, saliency.py
│   └── train.py / predict.py
├── baselines/                # persistence.py, pysteps_extrapolation.py, mecikalski_rules.py
├── evaluation/               # object_matching.py, scores.py (CSI/POD/FAR/FSS/BSS), reliability.py, bootstrap.py, report.ipynb
├── models/                   # (git-ignored or LFS) versioned model artifacts + model_card.md
├── gis/                      # grid.py, districts.geojson loader, radar_coverage.py, dem.py, tiles/
├── backend/                  # FastAPI app: api/, services/, db/ (PostGIS schema, migrations), cap/ (CAP 1.2 builder)
├── frontend/                 # React + MapLibre + deck.gl: pages/ (10 screens), components/, hooks/
├── notebooks/                # 01_explore_seviri.ipynb … 09_terls_case.ipynb (exploration only; not the source of reported numbers)
├── scripts/                  # one-off utilities: download_events.sh, make_figures.py
├── tests/                    # unit tests (features, labels, metrics), golden-file tests for replay bundles, API tests
└── docs/                     # architecture.md, data_reality.md, verification_protocol.md, ppt_assets/
```

| Directory | Purpose |
|---|---|
| `configs/` | Everything tunable lives here, so results are reproducible and diffable |
| `data/` | Never committed; `README` records source, licence and download date per dataset |
| `pipelines/` | Deterministic, re-runnable ETL; each step reads/writes versioned artifacts |
| `ml/` | Feature engineering, models, calibration, explainability |
| `baselines/` | Kept separate so nobody "accidentally" tunes baselines worse |
| `evaluation/` | The **single source** of every reported number |
| `models/` | Trained artifacts + model cards (training window, labels, known failures) |
| `gis/` | Grid definition, boundaries, DEM, coverage layers |
| `backend/` | API, DB schema, alert/CAP generation |
| `frontend/` | The 10 screens |
| `notebooks/` | Exploration only |
| `scripts/` | Glue and one-offs |
| `tests/` | Metric correctness (e.g., CSI on toy grids), label leakage checks, API contract |
| `docs/` | Architecture, data reality, verification protocol, PPT sources |

---

# PART 17 — FINAL RESEARCH REPORT

### A. Problem understanding
NCMRWF asks for a 0–6 h, 1–3 km, multi-source nowcasting system that detects convective initiation early and forecasts lightning, hail, downburst and cloudburst hazards, shown on a GIS dashboard with storm-arrival countdowns [V]. No data is provided [V]. The real challenge is building something **scientifically verifiable** with the Indian data that is actually open [I].

### B. Current state of existing solutions
Operationally, IMD runs WDSS-II nowcasts (0–2 h, 156 radar cities) [V] and NCMRWF runs NCUM-R 1.5 km hourly rapid-refresh NWP [V]. Abroad, NWCSAF RDT-CW (satellite lifecycle), MeteoSwiss TRT (radar severity rank) and NOAA ProbSevere v3 (per-cell hazard ML, operational 2025) set the bar [V].

### C. GitHub landscape
Mature, permissively licensed building blocks exist: pysteps, tobac, TINT, tathu, satpy, MetPy, xskillscore [V]. The multi-hazard reference design is MeteoSwiss c4dl-multi (BSD-3) [V]. LightningCast is public under GPL-3.0 [V]. Several popular DL repos have **no licence** (SmaAt-UNet, ml4convection, goes16ci) → re-implement from the papers [V].

### D. Student/SIH landscape
At least 4 public SIH26084 repos and 6+ SIH26072 repos [V]. Dominant pattern: polished dashboards, ConvLSTM/XGBoost, **simulated or foreign data**, accuracy-style metrics [V from inspected repos]. The most careful competitors (ThunderWatch, Avenger2007, nowcasting_sih) are honest about synthetic labels [V]. Nobody inspected had object-based verification on real Indian labels [V].

### E. Research landscape
The trend is towards satellite + NWP fusion for sparse-radar regions (Global MetNet 2025), advection-informed CNNs for > 2 h (Metzl 2025), generative models to 4–6 h (DDMS 2025, Stormscope 2026), and object-based GBDT hazard models (ProbSevere v3) [V]. Indian satellite-lightning precursor work exists (Goenka et al. 2025, NRSC) [V].

### F. Data availability
- **Available:** Meteosat-9 IODC (2017→, 15 min, free), INSAT-3DR/3DS L1B (MOSDAC; general users 3-day latency), ERA5, IMDAA (1979–2020), GFS/ECMWF open data, IMERG, GSMaP_NOW (realtime over India), GPM DPR, ISS-LIS (2017–2023), IMD NW-India hail report (2026), MOSDAC TERLS 3D radar (May 2018) [V].
- **Not openly available:** IMD DWR volumes, IMD AWS (locked May 2025), IITM ILLN, NRSC LDSN (access unclear) [V]. Blitzortung is off-limits by its terms [V].

### G. Technical gaps
Ranked table in Part 7. The cheapest high-value gaps are real-label verification, calibration and conformal ETA. The most distinctive are lifecycle-transition forecasting, genealogy-as-predictor and LightningCast transfer [I].

### H. Three architectures
Part 8: A (satellite + tabular ML, CPU), B (+ advection-informed U-Net, LightningCast transfer, radar case), C (+ generative ensembles).

### I. Recommended direction (trade-offs, not a selection guarantee)
Build **A end-to-end first**, with B elements as stretch goals, framed as **"Satellite-first Storm Lifecycle Intelligence for India — verified on real Indian events, radar- and lightning-ready."**
- **Trade-offs:** it gives up headline "deep learning" glamour for verifiability, and gives up 1 km claims for honesty.
- **Risk:** judges may prefer radar-centric work. Mitigate with the TERLS radar case and a DWR plug-in interface.

### J. MVP specification
Part 10 (10 components, 11 steps). Domain: NW India + IGP, Mar–Jun; test on 2025–2026 events.

### K. Differentiation strategy
1. **Proof over polish:** a verification table against baselines.
2. **Lifecycle *transitions* + genealogy**, not just phase labels.
3. **Calibrated uncertainty** (reliability + conformal ETA coverage).
4. **Real Indian labels** (ISS-LIS, IMD hail reports, GPM DPR, IMERG).
5. **Honest data-reality framing**, with a plug-in path to IMD/NCMRWF data.

### L. Evaluation methodology
Part 11. Time-blocked splits; object-based and neighbourhood metrics; bootstrap CIs; one reproducible evaluation script.

### M. 30-day roadmap (starting 25 Sep 2026)

| Days | Goal | Deliverables |
|---|---|---|
| **1–5 (→ 30 Sep)** | **Idea submission** via SPOC | Accounts opened (EUMETSAT, Earthdata, CDS, MOSDAC, JAXA, NCMRWF RDS); download **one event** (E4 Delhi 2 May 2025 or E8 hail 14 May 2026) from Meteosat-9 + ERA5; run tobac on it; produce 2–3 real figures (tracked cells + cooling-rate map + one cell's lifecycle curve); fill the official Idea PPT with: problem, data-reality table, architecture A/B, differentiation vs RDT/TRT/ProbSevere, verification plan, real figures. **Submit before 30 Sep; confirm your SPOC has nominated the team.** |
| 6–10 | Data at scale | Meteosat-9 Mar–Jun 2021–2026 (cropped), ERA5, IMERG, ISS-LIS 2019–2023; the 2 km grid; QC report |
| 11–14 | Tracking + labels + baselines | tobac tracks for all days; CI/phase/lightning/rain labels; persistence, pysteps and Mecikalski baselines scored → **first verification table** |
| 15–18 | ML v1 | LightGBM CI + transition + lightning + heavy rain; isotonic calibration; SHAP; conformal ETA |
| 19–21 | Backend + DB + replay bundles | FastAPI, PostGIS, `build_bundle.py` for E2–E9 |
| 22–25 | Frontend | Screens 1, 2, 4, 7, 9 first (the judge-critical ones), then 3, 5, 6, 8, 10 |
| 26–27 | Stretch (B) | LightningCast zero-shot vs fine-tuned on ISS-LIS **or** advection-informed U-Net for 0–3 h **or** TERLS radar case — pick one |
| 28–29 | Hardening | Tests, model cards, `docs/data_reality.md`, freeze evaluation hash |
| 30 | Rehearsal | 5-min demo script, Q&A drill (Part R), fallback offline demo |

*(The finale is proposed for December 2026 [V], so if you are shortlisted you'll have more time after Day 30 for the stretch goals.)*

### N. GitHub repositories to study (priority order)
1. [pySTEPS/pysteps](https://github.com/pySTEPS/pysteps) — `motion/`, `extrapolation/`, `tracking/tdating.py`, `verification/`
2. [tobac-project/tobac](https://github.com/tobac-project/tobac) — `feature_detection.py`, `segmentation/`, `tracking.py`, `merge_split.py`
3. [MeteoSwiss/c4dl-multi](https://github.com/MeteoSwiss/c4dl-multi) — `analysis/calibration.py`, `shapley.py`, `lagrangian.py`
4. [jlc248/ProbSevere_v3_paper_2024](https://github.com/jlc248/ProbSevere_v3_paper_2024) + [Zenodo data](https://zenodo.org/records/10891478) — per-storm feature schema
5. [LightningCast (SSEC GitLab)](https://gitlab.ssec.wisc.edu/jcintineo/lightningcast) — model I/O, preprocessing
6. [uba/tathu](https://github.com/uba/tathu) — lifecycle descriptors
7. [pytroll/satpy](https://github.com/pytroll/satpy) — SEVIRI reader & resampling
8. [openradar/TINT](https://github.com/openradar/TINT) + [ARM-DOE/pyart](https://github.com/ARM-DOE/pyart) — TERLS case
9. [chengtan9907/OpenSTL](https://github.com/chengtan9907/OpenSTL) — if you try gridded DL
10. [xskillscore](https://github.com/xarray-contrib/xskillscore) — metrics
11. Competitors to know (not copy): [VARSHANET](https://github.com/adarshsisodiya2007-web/sih86), [Solvix](https://github.com/RushilAmreliya/Solvix), [nowcasting_sih](https://github.com/Avizanzane44/nowcasting_sih), [ThunderWatch AI](https://github.com/nachiket-mr360/AIML_Thunderstorm_nowcasting_by_ThunderWatch_AI), [Avenger2007](https://github.com/Avenger2007/SIH-Nowcasting-), [STORMTRACE](https://github.com/targaryenv2/STORMTRACE)

### O. Datasets to obtain (with priority)
| Priority | Dataset | Action |
|---|---|---|
| P0 | Meteosat-9 IODC SEVIRI L1.5 | EUMETSAT account → `pip install eumdac` |
| P0 | ERA5 single + pressure levels | CDS account → `cdsapi` |
| P0 | IMD NW-India hail report | Download the PDF now (it may be overwritten later) |
| P1 | INSAT-3DR/3DS L1B | MOSDAC SSO → `mdapi` (apply today) |
| P1 | GPM IMERG V07 (Early/Final) | Earthdata |
| P1 | ISS-LIS V2/V3 | Earthdata (GHRC) |
| P1 | MOSDAC TERLS 3D DWR (May 2018) | MOSDAC Open Data |
| P2 | GPM DPR 2A | Earthdata |
| P2 | IMDAA | NCMRWF RDS registration |
| P2 | GSMaP NRT/NOW | JAXA registration |
| P2 | GFS / ECMWF open data | Open (live screen) |
| P3 | NRSC LDSN / IITM ILLN lightning | Formal email request via faculty mentor |

### P. Research papers to read (in this order)
1. Mecikalski & Bedka 2006 (MWR) — IR CI interest fields
2. [CIUnet, MWR 152(1) 2024](https://journals.ametsoc.org/view/journals/mwre/152/1/MWR-D-22-0216.1.xml)
3. [ProbSevere v3, WAF 2024](https://journals.ametsoc.org/view/journals/wefo/39/12/WAF-D-24-0076.1.pdf)
4. [Leinonen et al. 2023, c4dl-multi (GRL)](https://arxiv.org/abs/2211.01001)
5. [Metzl et al. 2025, Physical Scales Matter](https://arxiv.org/abs/2504.09994)
6. [Goenka et al. 2025, INSAT-3D lightning (GRL)](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2024GL112764)
7. [tobac v1.5 (GMD 2024)](https://gmd.copernicus.org/articles/17/5309/2024/) and [pysteps (GMD 2019)](https://gmd.copernicus.org/articles/12/4185/2019/)
8. [NWCSAF RDT description](https://www.nwcsaf.org/rdt_description_2025)
9. [Global MetNet 2025](https://arxiv.org/abs/2510.13050) — motivation for satellite-first
10. [DDMS 2025](https://arxiv.org/abs/2404.10512), [Stormscope 2026](https://arxiv.org/abs/2601.17268) — to discuss 4–6 h honestly
11. Haynes et al. 2023 (AIES, uncertainty) and McGovern et al. 2019 (BAMS, XAI)
12. [Iguchi et al. 2018 (JTECH) DPR heavy ice](https://journals.ametsoc.org/view/journals/atot/35/3/jtech-d-17-0120.1.xml)

### Q. Risks & fallback plans

| Risk | Likelihood [I] | Impact | Fallback |
|---|---|---|---|
| Idea deadline missed (30 Sep) | Medium (5 days) | Fatal | Submit PPT by 28 Sep; confirm SPOC nomination today |
| MOSDAC account slow / INSAT L1B limited | Medium | Medium | Meteosat-9 IODC as primary; INSAT for event days only |
| ISS-LIS overpasses too sparse for lightning training | High | Medium | Use LIS for **evaluation only**; train lightning on a BT/OT proxy and label it "proxy"; keep requesting NRSC/IITM access |
| Hail labels too few | High | Medium | Event-level evaluation only; state "potential" not "probability" |
| tobac tuning on 3–4 km IR is fiddly | Medium | Medium | Start with pysteps T-DaTing on −BT; multithreshold with fewer levels |
| Meteosat-9 end of life (EOL listed April 2027 in [WMO OSCAR](https://space.oscar.wmo.int/satellites/view/meteosat_9_iodc)) | Low before finale | Medium (sustainability question) | Architecture is sensor-agnostic; INSAT-3DS is the long-term operational input |
| GPL-3.0 contamination (LightningCast, DiffCast, ThunderCast, ProbSevere scripts) | Medium | Medium (IP split with ministry) | Keep GPL components in a separate optional module/service, or re-implement from papers; get a mentor's view on the SIH IP clause |
| Overclaiming by a teammate in the PPT | Medium | High | "Every number has a script" rule; data-reality slide |
| Judges expect radar | Medium | Medium | TERLS case + PyScanCf-ready IMD DWR adapter + quantified "value of radar" ablation |
| 2–6 h skill is weak | High | Medium | Show the skill curve honestly; blend with NWP; frame 2–6 h as probabilistic *area* guidance |

### R. What to demonstrate to SIH evaluators (5-minute script) [P]
1. **(30 s) Data reality slide** — what's open, what's not, what you did about it.
2. **(60 s) Replay E8 (hail, 14 May 2026)** — T−60 → T+2 h: CI detected at T−45; cell #n matures; hail-potential HIGH; ETA countdown to Ambala with its interval; then the "what happened" pane shows IMD hail reports.
3. **(45 s) Cell card + genealogy + SHAP** — why this cell, with percentiles.
4. **(60 s) Model Performance screen** — CSI/POD/FAR vs persistence, extrapolation and rules on 2025–2026 test events; reliability diagram; ETA coverage 88 % vs 90 % nominal (whatever you actually get).
5. **(30 s) Skill vs lead time 0–6 h** — where you're useful and where you're not.
6. **(30 s) Radar-ready** — TERLS case: satellite-only vs radar-added skill; the IMD DWR adapter.
7. **(15 s) Future work** — NCUM-R blending, IMD DWR, NRSC/IITM lightning, generative ensembles.

**Q&A you must be ready for:**
- "What are your labels?"
- "Why not radar?"
- "Isn't this just RDT?"
- "How do you verify cloudbursts at 10 km rainfall resolution?"
- "What's your FAR at operational base rates?"
- "What happens when INSAT data is 3 days late?"
- "What licence are your dependencies under?"

---

## Appendix — Source index (primary sources used)

- SIH official PS list: https://sih.gov.in/sih2026PS · SIH 2026 Guidelines: https://sih.gov.in/letters/2026/SIH%202026%20Guidelines.pdf · Idea PPT format: https://sih.gov.in/letters/2026/SIH2026-IDEA-Presentation-Format.pptx
- MOSDAC: INSAT-3DR https://mosdac.gov.in/insat-3dr · INSAT-3DS https://mosdac.gov.in/insat-3ds · API manual https://www.mosdac.gov.in/downloadapi-manual · Data access policy https://www.mosdac.gov.in/data-access-policy · TERLS DWR https://www.mosdac.gov.in/3d-volumetric-terls-dwrproduct · INSAT-3D products doc https://www.mosdac.gov.in/docs/INSAT3D_Products.pdf
- EUMETSAT IODC SEVIRI: https://data.eumetsat.int/product/EO:EUM:DAT:MSG:HRSEVIRI-IODC · WMO OSCAR Meteosat-9 IODC: https://space.oscar.wmo.int/satellites/view/meteosat_9_iodc
- NASA: IMERG Early https://www.earthdata.nasa.gov/data/catalog/ges-disc-gpm-3imerghhe-07 · ISS-LIS https://www.earthdata.nasa.gov/data/catalog/ghrc-daac-isslis-v2-fin-2
- JAXA GSMaP guide: https://sharaku.eorc.jaxa.jp/GSMaP/guide.html
- NCMRWF data portal: https://www.ncmrwf.gov.in/data/ · IMDAA RDS: https://rds.ncmrwf.gov.in/
- IMD: WDSS-II https://nwp.imd.gov.in/WDSSII_website.pdf · NW India hail report https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf · AWS portal lock (DTE) https://www.downtoearth.org.in/climate-change/imd-locking-up-its-awsarg-data-portal-hampers-public-weather-alerts-experts
- NRSC lightning: https://bhuvan-app1.nrsc.gov.in/lightning/ · https://link.springer.com/article/10.1007/s11069-021-05042-8
- Blitzortung: https://www.blitzortung.org/ · RainViewer API: https://www.rainviewer.com/api.html
- NWCSAF RDT: https://www.nwcsaf.org/rdt_description_2025 · MeteoSwiss TRT: https://www.meteoswiss.admin.ch/about-us/research-and-cooperation/projects/en/2002/trt.html · ProbSevere v3: https://journals.ametsoc.org/view/journals/wefo/39/12/WAF-D-24-0076.1.pdf
