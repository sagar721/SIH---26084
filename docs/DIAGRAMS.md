# SIH26084 — System Diagrams

**Convention:** solid boxes are implemented and used. Dashed grey boxes are planned or reference only, and are **not** implemented.

**Sources for every label:**
- `docs/FIRST_EVENT.md`, `docs/BASELINE_EVAL.md`, `docs/TRACKING_AUDIT.md`, `docs/MULTI_EVENT.md`
- `docs/ML_PROTOTYPE.md`, `docs/PRODUCT_DEMO.md`, `docs/FREEZE_ml-v0.json`

---

## Diagram 1 — End-to-end system flowchart

```mermaid
flowchart TB
  subgraph A1["1 · Data sources, ingestion and quality control"]
    direction LR
    S["DATA SOURCES<br/>NOAA/NCEP/CPC Globally Merged IR<br/>(4 km, 30 min) · IMD hail report<br/>(event selection only)"] --> I["Data ingestion<br/>HTTPS download, resume,<br/>SHA-256 manifest"] --> Q["Quality control /<br/>missing-data detection<br/>BT 170–330 K · fail if &gt; 5 % missing<br/>gaps ≤ 4 px filled + flagged"]
  end
  subgraph A2["2 · Satellite IR preprocessing and common grid"]
    direction LR
    P["Satellite IR preprocessing<br/>decode 1-byte BT,<br/>crop to domain"] --> G["Common 2 km grid<br/>LAEA 453 × 603 px<br/>NW India 26–34° N, 72–84° E"]
  end
  subgraph A3["3 · Objects: detection, tracking, lifecycle"]
    direction LR
    D["Cloud / convective<br/>object detection<br/>tobac 273…208 K · segments &lt; 245 K"] --> T["Storm cell tracking<br/>v2 overlap linking (≥ 0.2)<br/>coldness-weighted centroid"] --> L["Lifecycle / motion<br/>diagnostics<br/>min BT · area · ΔBT · phase v0"]
  end
  subgraph A4["4 · Forecast generation, 30–360 min (reads the 2 km gridded BT)"]
    direction LR
    F1["Persistence"]
    F2["pySTEPS advection<br/>Lucas–Kanade +<br/>semi-Lagrangian"]
    F3["ML probability model<br/>HistGradientBoosting"] --> C["Calibration /<br/>probability generation<br/>isotonic per lead bin"]
    F1 ~~~ F2 ~~~ F3
  end
  subgraph A5["5 · Validation, freeze and delivery"]
    direction LR
    V["Validation &amp; metrics<br/>CSI · POD · FAR · bias<br/>FSS · BSS · reliability"] --> Z["Evidence freeze<br/>386 files SHA-256"] --> R["Replay bundle<br/>tiles · GeoJSON · JSON"] --> W["React + MapLibre<br/>dashboard (9 screens)"] --> H["Human decision support<br/>exercise advisory<br/>CAP 1.2 status=Exercise"]
  end
  A1 --> A2 --> A3 --> A4 --> A5
```

*Figure D1.* End-to-end workflow as implemented, read top to bottom and left to right within each stage. The grid forecasts (persistence, pySTEPS, ML) read the 2 km gridded BT fields. Cells and lifecycle diagnostics feed the object diagnostics and the dashboard.

---

## Diagram 2 — Layered system architecture

```mermaid
flowchart TB
  subgraph DATA["DATA LAYER"]
    direction LR
    d1["NOAA/NCEP/CPC merged IR<br/>600 hourly files · 25 days<br/>SHA-256 manifest"]
    d2["Real event days<br/>E8 · E10 · E11<br/>(E8a excluded)"]
    d3["IMD hail-report PDF<br/>(archived) + geocoded places"]
    d4["Processed 2 km NetCDF cubes<br/>Parquet ML dataset<br/>CSV / JSON outputs"]
    d1 ~~~ d2 ~~~ d3 ~~~ d4
  end
  subgraph PROC["PROCESSING LAYER"]
    direction LR
    p1["Python 3.11<br/>NumPy · pandas · SciPy"]
    p2["xarray · netCDF4<br/>pyarrow · pyproj"]
    p3["scikit-image<br/>Pillow"]
    p4["tobac 1.6.2 + trackpy + numba<br/>v2 overlap tracker + audit"]
    p5["pySTEPS 1.21.5<br/>+ OpenCV"]
    p1 ~~~ p2 ~~~ p3 ~~~ p4 ~~~ p5
  end
  subgraph MODEL["MODEL LAYER"]
    direction LR
    m1["Persistence<br/>baseline"]
    m2["pySTEPS<br/>advection"]
    m3["Neighbourhood pySTEPS<br/>(no-fit reference)"]
    m4["HistGradientBoosting<br/>+ isotonic calibration"]
    m5["Frozen model<br/>ml-v0"]
    m1 ~~~ m2 ~~~ m3 ~~~ m4 ~~~ m5
  end
  subgraph VAL["VALIDATION LAYER"]
    direction LR
    v1["CSI · POD<br/>FAR · bias"]
    v2["FSS<br/>10 / 20 / 40 km"]
    v3["BSS · reliability<br/>ECE"]
    v4["Block bootstrap<br/>event-day bootstrap"]
    v5["Leakage + reproducibility<br/>tests · freeze guard"]
    v1 ~~~ v2 ~~~ v3 ~~~ v4 ~~~ v5
  end
  subgraph PROD["PRODUCT LAYER"]
    direction LR
    r1["Replay bundle<br/>builder (Python)"]
    r2["React 18 · TypeScript 5<br/>Vite 5"]
    r3["MapLibre GL 4 · plain CSS<br/>Esri basemap (display)"]
    r4["Static replay bundles<br/>(no backend)"]
    r5["Vitest<br/>Playwright"]
    r1 ~~~ r2 ~~~ r3 ~~~ r4 ~~~ r5
  end
  subgraph OUT["OUTPUT LAYER"]
    direction LR
    o1["Situation<br/>Dashboard"]
    o2["Storm Cell Tracker<br/>+ details"]
    o3["0–6 h<br/>Forecast"]
    o4["Historical<br/>Replay"]
    o5["Model<br/>Performance"]
    o6["Confidence ·<br/>Data Health"]
    o7["Alert Center<br/>(exercise)"]
    o1 ~~~ o2 ~~~ o3 ~~~ o4 ~~~ o5 ~~~ o6 ~~~ o7
  end
  subgraph NU["NOT USED in Phases 1–9 — reference / future only"]
    direction LR
    n1["SatPy · rasterio<br/>MetPy"]
    n2["Tailwind CSS<br/>deck.gl"]
    n3["LightGBM · FastAPI<br/>PostGIS"]
    n4["Meteosat-9 / INSAT-3DS<br/>radar · lightning"]
    n1 ~~~ n2 ~~~ n3 ~~~ n4
  end
  DATA --> PROC --> MODEL --> VAL --> PROD --> OUT
  OUT ~~~ NU
  classDef future fill:#f2f2f2,stroke:#999,stroke-dasharray: 5 5,color:#666;
  class NU,n1,n2,n3,n4 future;
```

*Figure D2.* Layered architecture. Only the technologies in the solid layers were used. The dashed box lists items named in the PRD/ARCHITECTURE that were **not** used in Phases 1–9.

---

## Diagram 3 — Data / ML pipeline

```mermaid
flowchart TB
  subgraph B1["1 · Build the dataset (per calendar day)"]
    direction LR
    A["NOAA CPC raw<br/>hourly files"] --> B["Daily 2 km cube<br/>48 frames · QC flags"] --> C["Issue times<br/>01:00–23:00 UTC (45)"] --> F["17 features per pixel &amp; lead<br/>pySTEPS BT + neighbourhood<br/>fractions · BT(t) · tendency<br/>motion · hour · lead"] --> H["Stratified pixel sampling<br/>150 event · 150 near-cold · 60 far<br/>inverse-probability weights<br/>target: BT(t+L) &lt; 235 K"]
  end
  subgraph B2["2 · Calendar-day split (event days ± 1 day excluded)"]
    direction LR
    TRd["TRAIN<br/>18–31 May 2026<br/>14 days · 1,467,318 rows"]
    VAd["VALIDATION<br/>6–12 May 2026<br/>7 days · 856,830 rows"]
    TEd["TEST (held out)<br/>E8 14 May · E10 4 May<br/>E11 16 May · never read"]
    TRd ~~~ VAd ~~~ TEd
  end
  subgraph B3["3 · Train, select, calibrate, freeze"]
    direction LR
    GATE["Sufficiency gate<br/>≥ 7 convective train days<br/>≥ 3 validation → 7 and 5: PROCEED"] --> TR["Fit HistGradientBoosting<br/>(fixed settings)"] --> NI["n_iter by validation<br/>log-loss → 216"] --> ISO["Isotonic calibration<br/>per lead bin (validation)"] --> FZ["ml-v0 frozen<br/>SHA-256"]
  end
  subgraph B4["4 · Held-out evaluation (run once)"]
    direction LR
    EV["Frozen model on E8 · E10 · E11"] --> M["CSI · FSS · bias · BSS · reliability<br/>identical pixels vs persistence,<br/>pySTEPS, neighbourhood pySTEPS"]
  end
  B1 --> B2 --> B3 --> B4
```

*Figure D3.* ML data pipeline and time-blocked splits. The test events were scored once with the frozen model.

---

## Diagram 4 — Historical replay workflow

```mermaid
flowchart LR
  TL["Timeline<br/>issue time t · lead Δ<br/>▶ 1× / 2× / 5×"] --> K
  TL --> P
  TL --> H
  subgraph REPLAY["Three synced map panes (pan / zoom locked)"]
    K["WHAT THE SYSTEM KNEW<br/>observed IR at t · cells at t<br/>(frames ≤ t)"]
    P["WHAT IT PREDICTED<br/>ML probability · pySTEPS · persistence<br/>for t + Δ  (key B switches)"]
    H["WHAT ACTUALLY HAPPENED<br/>observed IR at t + Δ<br/>BT &lt; 235 K outline · IMD report places"]
  end
  K --> SC
  P --> SC["Scorecard for this issue and lead<br/>frozen per-issue CSI · POD · bias · Brier"]
  H --> SC
  P --> AL["Would-have-issued draft advisories<br/>(EXERCISE)"]
  AV["Data availability row<br/>CPC IR QC · INSAT / Meteosat not connected<br/>radar · lightning unavailable"] --> K
```

*Figure D4.* Replay workflow. It uses saved outputs only; it is not a live feed, and product latency is not modelled.

---

## Diagram 5 — Prototype / dashboard information architecture

```mermaid
flowchart LR
  NAV["App shell<br/>sidebar navigation · top bar<br/>(REPLAY · valid UTC/IST · data tier<br/>model ml-v0 · frame QC)<br/>timeline · disclaimer footer"]
  NAV --> ST["START"] & OP["OPERATE"] & IN["INVESTIGATE"] & EV["EVIDENCE"]
  ST --> s1["1 · Event selection<br/><i>index.json</i>"]
  OP --> s2["2 · Situation<br/><i>obs tiles · cells · cellfc · alerts</i>"]
  OP --> s3["3 · Storm Cells + details / ML probability<br/><i>cells · tracks · cellfc</i>"]
  OP --> s4["4 · 0–6 h Forecast<br/><i>fc tiles · skill · scores</i>"]
  OP --> s5["5 · Alert Center + CAP preview<br/><i>alerts · places</i>"]
  IN --> s6["6 · Historical Replay<br/><i>obs + fc tiles · contours · scores · alerts</i>"]
  IN --> s7["7 · Confidence<br/><i>skill: reliability · bootstrap</i>"]
  EV --> s8["8 · Model Performance<br/><i>skill: pooled · per event · Phase 4–5</i>"]
  EV --> s9["9 · Data Health<br/><i>health · manifest (hashes)</i>"]
  BUN[("Static replay bundle per event<br/>apps/web/public/bundles/{event}/<br/>built from frozen files only")]
  BUN -. "read by every screen" .-> NAV
```

*Figure D5.* Dashboard information architecture: navigation groups, screens, and the bundle files each screen reads (italics). Keyboard keys 1–9 open the screens in this order.
