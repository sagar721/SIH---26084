# UI/UX Specification — Forecaster Decision Support

**Version:** 0.1 · **Reference:** `WhatsApp Image 2026-09-24 at 19.43.10 (1).jpeg` (flood dashboard). Used for **visual and layout language only**. No flood functionality is ported.

---

## 1. Design language taken from the reference

| Reference element | What we keep | Our version |
|---|---|---|
| Left sidebar, "DECISION FLOW" + "REFERENCE" groups with icons, count badge (e.g., "Impact 203") | Grouped navigation with small uppercase eyebrow labels and count badges | **OPERATE:** Live Situation, Storm Cells (badge = active cells), 0–6 h Forecast, Hazard Map, Alert Center (badge = drafts). **INVESTIGATE:** Historical Replay, Explainability, Confidence. **EVIDENCE:** Model Performance, Data Health |
| Warm off-white panels, thin borders, rounded cards | Calm, paper-like panels so the map carries the colour | Tokens in §2 |
| Controls column with slider cards + preset cards | Contextual panel of dense cards | Context panel: cell card, hazard controls, event presets (real events only) |
| Info callout explaining the mode | Always explain what the user is looking at | "About this view" callout per screen (data used, evidence level) |
| "SIMULATED" pill badges | Explicit provenance badges | **LIVE**, **REPLAY**, **BASELINE**, **PROBABILITY / POTENTIAL / INDICATOR**, **STALE**, **UNAVAILABLE**. There is **no SIMULATED** badge, because there is no simulated mode. |
| Large satellite map | Map is the hero (≥ 55 % viewport) | Regional map, NW India + IGP; IR brightness temperature is the imagery layer |
| Floating legend card, bottom-left | Same | Legend per active layer with units and evidence level |
| Bottom timeline: segmented bar, T+0 … T+180 (now), play, reset, 1×/2×/5× | Same interaction model | Observed frames (left of NOW) + forecast leads (right of NOW) to +6 h; replay adds T−60 … T+6 h |
| Monospace for numbers ("1.8x", "T+180min") | Monospace for all numeric readouts | Times, probabilities, ETAs, BT |

### Flood → weather translation (required)

| Flood reference | Our equivalent |
|---|---|
| Flood depth layer | Hazard probability / potential layer (lightning, heavy rain, hail potential, cloudburst indicator, downburst indicator) |
| Drainage blockage slider | Forecast & data controls: probability threshold, layer toggles, source include/exclude (for ablation view), parallax on/off |
| Flood simulation / what-if presets | Storm replay of **real** events E1–E9 (preset cards) |
| Rainfall multiplier | Forecast horizon selector (0–360 min) |
| Safe route / routing | Alert & impact intelligence: affected districts/towns, ETA countdowns with intervals, draft alerts |
| Critical-infrastructure status | Places at risk: towns/districts coloured by max P within the horizon |

## 2. Design tokens (PROPOSED; sampled visually from the reference)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#F4EFE7` | App background |
| `--panel` | `#FBF8F3` | Cards, panels |
| `--border` | `#E4DBCE` | 1 px borders |
| `--ink` | `#1C2433` | Primary text |
| `--ink-muted` | `#6B6457` | Secondary text, eyebrow labels |
| `--accent` | `#1F2A44` | Active nav, active timeline segment, play button |
| `--danger` | `#B23A2E` | Severe/red states |
| `--warn` | `#C9822B` | Watch/amber |
| `--ok` | `#2F6B4F` | Data OK |
| `--info-bg` | `#EEF1F6` | Info callouts |

- **Dark theme:** same hues, inverted luminance (`--bg #12161F`, `--panel #1A202B`). Forecasters often work in dim rooms.
- **Type:** IBM Plex Sans (UI) + IBM Plex Mono (numbers, times). Both are OFL, Google Fonts. Eyebrow labels are 11 px uppercase, +0.08 em tracking. Body 13–14 px. Card titles 14 px semibold. Numbers use `font-variant-numeric: tabular-nums`.
- **Density:** 8 px grid; cards 12 px padding; tables 28 px rows.

### Colour scales
- **IR BT:** standard enhanced IR (warm grey above 273 K; blue → green → yellow → red → magenta for 273 → 200 K). The legend states K.
- **Probabilities:** single-hue sequential, 5 bins (0.1/0.3/0.5/0.7/0.9), colour-blind-safe. Bins below the user threshold are transparent.
- **Potential/indicator:** 3-level categorical (Low/Med/High) with **hatching** so it can't be confused with probability.
- **Lifecycle phases:**

  | Phase | Colour | Outline |
  |---|---|---|
  | Initiation | Teal `#2A9D8F` | Dotted |
  | Developing | Amber `#E9A23B` | Dashed |
  | Mature | Red `#C0392B` | Solid, thick |
  | Decaying | Slate violet `#7D6B91` | Thin |

  Phase is encoded by **both colour and outline style**, for colour-blind users.

## 3. App shell (all screens)

```
┌──────────┬───────────────────────────────────────────────────────┬──────────────────┐
│ SIDEBAR  │ TOP BAR: mode badge · valid time UTC | IST · data tier · model vX · ⚠ stale │
│ 232 px   ├───────────────────────────────────────────────┬───────┴──────────────────┤
│ OPERATE  │                                               │ CONTEXT PANEL 380 px     │
│ INVESTIG.│                 MAP (MapLibre + deck.gl)      │ (screen-specific cards)  │
│ EVIDENCE │   legend card (bottom-left, collapsible)      │                          │
│          │   map controls (top-right): layers, zoom      │                          │
├──────────┴───────────────────────────────────────────────┴──────────────────────────┤
│ TIMELINE 96 px: ACTIVE VIEW label · segmented frames · NOW marker · leads → +6h ·   │
│ ▶ ⟲ 1× 2× 5× · lead readout (mono)                                                   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

- **Top bar is persistent.** Mode badge (LIVE green / REPLAY navy); `Valid 08:45 UTC · 14:15 IST`; data tier chip (e.g., `SAT+NWP · Radar ✗ · Lightning ✗`); `model v0.3.1`; red **STALE** chip if the newest frame is older than its expected latency + 15 min.
- **Disclaimer (footer strip, always):** "Research prototype — not an official IMD warning."
- **Keyboard:** `←/→` frame, `Space` play, `1–9` switch screen, `L` layers, `B` baseline toggle (replay).
- **Responsiveness:**
  - ≥ 1280 px: full layout (target).
  - 1024–1279 px: context panel collapses to a drawer.
  - < 1024 px: read-only map + cards stacked (not a design target).

### Map base
- **Basemap:** neutral light/dark vector basemap (OSM-derived; provider **NEEDS VERIFICATION** of terms, decision D6). District boundaries, rivers, major towns.
- **Imagery:** IR BT (default); VIS by day as an optional layer.
- **Overlays (deck.gl):**
  - cell polygons (GeoJsonLayer)
  - motion arrows (IconLayer / LineLayer)
  - forecast polygons (dashed)
  - ETA cones (PolygonLayer from conformal intervals)
  - hazard rasters (BitmapLayer)
  - places (ScatterplotLayer + labels)
  - radar coverage rings (IMD network metadata, informational)
- **Default view:** domain 26–34°N, 72–84°E. Zoom-to-district on search.

## 4. Screens

Each screen lists its map layers, context-panel content, timeline behaviour and acceptance criteria. Every number on a screen shows or links to its **envelope** (valid time, model version, data tier, evidence level).

### 4.1 Live Situation
- **Map:** IR BT + cell polygons (phase-styled) + motion arrows + district choropleth of max hazard P in the next 60 min (threshold-filtered).
- **Context panel:**
  - (1) KPI strip: active cells, cells in Mature, districts with P ≥ threshold, latest frame age.
  - (2) "Top 5 cells by risk" list.
  - (3) Data-health mini bar per source.
  - (4) "About this view" callout.
- **Timeline:** last 3 h observed + leads to +6 h; NOW marker.
- **Acceptance:**
  - Loads in < 2 s from cache.
  - STALE state is shown when data is late.
  - Clicking a cell opens the Cell Tracker at that cell.

### 4.2 Storm Cell Tracker
- **Map:** selected cell highlighted; its past track (solid) and forecast track (dashed with ETA cone); related cells (parents/children) outlined.
- **Context panel:**
  1. **Cell card**, per report §9.3: phase now, P(decay ≤ 60), remaining life, motion ± CI, growth, hazards with evidence badges, ETA to top places.
  2. **Lifecycle sparkline:** min BT, area, P(→Mature) and P(decay) over time, with phase bands.
  3. **Genealogy tree:** D3; nodes = tracks; edges labelled MERGE/SPLIT with time.
  4. Sortable **cell table:** ID, phase, age, min BT, ΔBT 15 min, speed/dir, P(ltg), P(rain20), hail potential, nearest-place ETA.
- **Acceptance:**
  - The card shows model version + data tier.
  - The genealogy tree renders ≥ 20 nodes without overlap.
  - Table sorting < 100 ms for 500 rows.

### 4.3 0–6 h Forecast
- **Map:** hazard raster at the selected lead; forecast cell polygons at that lead.
- **Context panel:**
  - Hazard selector.
  - **Lead-time selector** (replaces "rainfall multiplier"): 0, 15, 30, 60, 120, 180, 240, 360 min.
  - **Skill-at-this-lead ribbon:** validated CSI/BSS for this hazard and lead, from `/metrics`, with CI. If a lead has no validated skill, show "not validated".
  - Method note: extrapolation vs ML (vs U-Net if B).
- **Timeline:** scrubs lead time.
- **Acceptance:**
  - The skill ribbon is always visible and matches the report.
  - Leads beyond validated skill are visibly de-emphasised.

### 4.4 Historical Replay (details: [REPLAY_SPEC.md](REPLAY_SPEC.md))
- **Layout:** the map splits into **three synced panes**:
  - **WHAT THE SYSTEM KNEW** (observed inputs at t)
  - **WHAT IT PREDICTED** (for t+Δ)
  - **WHAT ACTUALLY HAPPENED** (observed at t+Δ + ground truth)

  A toggle collapses the view to one pane with a swipe comparator.
- **Context panel:**
  - **Event preset cards** (replaces the "extreme event presets"): E1–E9 with date, place, hazard and a data-availability icon row.
  - Event scorecard: alert lead time, hits/misses/false alarms, ETA error.
  - **BASELINE toggle:** persistence / pySTEPS / rules vs model.
- **Timeline:** T−60 … T0 … T+6 h in 15-min steps. T0 is marked with the event's reported impact time and source.
- **Acceptance:** REPLAY_SPEC §8.

### 4.5 Hazard Map
- **Map:** one hazard at a time, with a threshold slider. Hatched style for POTENTIAL/INDICATOR. Places layer; DEM hillshade toggle (orographic context for cloudburst).
- **Context panel:**
  - Hazard definitions: label source, evidence level, known limits.
  - Places at risk list: place, hazard, max P/level, window, ETA.
- **Acceptance:**
  - Evidence badge shown for every hazard.
  - Cloudburst/downburst carry an "Indicator — not verified" banner.

### 4.6 Explainability
- **Map:** selected cell. Optional saliency overlay (B only).
- **Context panel:**
  - SHAP waterfall (top-4 contributors + "other"). Each entry shows the raw value, unit and climatological percentile.
  - Feature-group bars: satellite / environment / genealogy / time.
  - Physics checklist: CAPE, CIN, shear, freezing level, PWAT, each with a percentile.
- **Acceptance:**
  - Values add up to the model output (tooltip shows margin → probability).
  - The percentile reference period is stated.

### 4.7 Confidence / Uncertainty
- **Map:** ETA cones (80 %/90 %) for the selected place or cell.
- **Context panel:**
  - Reliability diagram per hazard (test split).
  - Conformal coverage table (nominal vs empirical per lead bin).
  - Data-tier skill penalty (e.g., metrics with vs without NWP).
  - Plain-language "how to read this" note.
- **Acceptance:**
  - Every chart shows split + n + report hash.
  - Coverage shortfalls are highlighted, not hidden.

### 4.8 Alert Center
- **Map:** districts with draft/issued alerts; outline colour = severity.
- **Context panel:**
  - Alert queue (Draft → Approved → Issued → Expired) with the trigger rule, source prediction IDs, lead time and ETA interval.
  - Approve/Reject buttons (token-protected).
  - CAP XML preview/download (`status=Exercise`).
  - Audit log.
- **Acceptance:**
  - No alert issues without approval.
  - Auto-expiry on cell decay is visible in the log.
  - Disclaimer on every CAP.

### 4.9 Model Performance
- **Map:** optional per-region skill choropleth.
- **Context panel / full-width option:**
  - Comparison table: persistence vs pySTEPS vs rules vs model, per task, with CIs.
  - Performance diagram (POD/SR/CSI/bias).
  - FSS vs scale.
  - Skill vs lead (0–6 h).
  - Model cards.
  - Link to `evaluation/report.html`.
- **Acceptance:**
  - Numbers are byte-identical to the report JSON (hash shown).
  - Nothing is computed client-side.

### 4.10 Data Health
- **Map:** coverage footprints (satellite disk, radar rings marked "not connected", DPR swaths for the selected day).
- **Context panel:**
  - Per source: status (AVAILABLE / PARTIAL / UNAVAILABLE / FALLBACK), last obs time, latency histogram, gaps timeline, licence/attribution, access route.
  - "What we'd add with IMD DWR / lightning access".
- **Acceptance:**
  - Statuses match [DATA_REALITY.md](DATA_REALITY.md).
  - Gaps are rendered from `ingest_files` / `frames` (real, not illustrative).

## 5. States & messaging

| State | Treatment |
|---|---|
| Loading | Skeleton cards; map keeps the last frame, with "updating" chip |
| Stale data | Red STALE chip + banner with the source name and age |
| Source unavailable | Grey UNAVAILABLE badge; affected outputs show a lower data tier |
| No cells | Empty state: "No convective cells above 273 K threshold in domain" |
| Not validated lead/hazard | Muted rendering + "not validated" tag |
| Error | Inline error card with retry; never a blank map |

## 6. Accessibility
- WCAG AA contrast for text on panels.
- Phase and severity are never encoded by colour alone.
- All controls are keyboard-reachable; focus rings visible.
- Map legend text ≥ 12 px.

## 7. Explicitly excluded (from the reference or common student builds)
- Hypothetical scenario sliders, drainage what-ifs, routing engine.
- Chat/LLM assistant avatar (the reference shows one in the corner).
- Consumer weather widgets (temperature, "feels like", icons).
- 3D globe, glassmorphism, decorative animation.
