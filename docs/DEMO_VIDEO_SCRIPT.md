# Prototype Demo Video Script — SIH26084 (target 4:40, range 3–5 min)

**What is recorded:** the verified E8 (14 May 2026) browser flow on the local production build. Every value spoken below appeared on screen in the verification run.

**Do not say:**
- "ML beats pySTEPS" (only true for *probability* skill; not as a yes/no forecast beyond 1 h);
- "6-hour skill";
- hail, lightning or rain forecasts;
- "live" or "real-time".

## Before recording (setup, not in the video)

1. From the repository root: `cd apps/web && npm run build && npm run preview` → open **http://localhost:4173/**
2. Use a **fresh private/incognito window**. The Alert Center keeps approvals in browser storage, so a used browser may already show "APPROVED".
3. Window **1440×900 or larger**, browser zoom 100 %. Hide bookmarks and extensions.
4. Internet on for the basemap (Esri light grey). If offline, untick **Basemap (online tiles)**; every data layer still works.
5. Screen recorder at 1920×1080 or 1440×900, 30 fps, microphone checked. Record in one take per section; cut between sections.
6. Speak slowly. Pause ~1 s after each click so the map finishes drawing.

---

## 0:00–0:20 · Opening

| | |
|---|---|
| **UI action** | Show the Event selection screen, untouched. |
| **Screen** | Title "Select an event"; event cards E1–E11; E8 marked "★ main demo". |
| **Narration** | "This is StormLife Nowcast, our research prototype for SIH26084: nowcasting deep convection over India from satellite, zero to six hours ahead. Everything you'll see is a replay of real satellite data from a held-out storm day, one the model never saw during training." |

## 0:20–0:40 · Event selection

| | |
|---|---|
| **UI action** | Hover over **E9** (greyed, "NOT AVAILABLE"), then click the **E8 · 14 May 2026** card. |
| **Screen** | Greyed cards show their reason, e.g. "April 2026 missing from the NOAA archive". After the click, the Situation screen opens. |
| **Narration** | "Events we could not process honestly are shown with the reason instead of being hidden. We'll open the 14th of May 2026, a day with hail reports from sixteen places across north-west India." |

## 0:40–1:10 · Situation at 14:00 UTC

| | |
|---|---|
| **UI action** | No click needed; the timeline opens at **14:00 UTC**. Point the cursor at the REPLAY badge, then at the KPI strip, then at the Sources card. |
| **Screen** | IR satellite map with coloured cloud tops; phase-styled cell outlines; motion arrows. KPIs: **Active cells 9**. Place markers from the IMD hail report, with Amritsar highlighted. Sources: CPC merged IR AVAILABLE (FALLBACK); radar and lightning UNAVAILABLE. |
| **Narration** | "It's 14:00 UTC, 7:30 in the evening IST. The system sees nine active storm cells in the satellite image. The arrows show where each cell is moving over the next half hour. Note the honest labels: this is REPLAY, the only input is one infrared satellite channel, and radar and lightning are marked unavailable." |

## 1:10–1:45 · Select cell #108

| | |
|---|---|
| **UI action** | Click **cell #108** in the "Top 5 cells by ML risk" list (first row), or click the large cell that covers Amritsar and the area to its west. |
| **Screen** | Storm Cells screen with the cell card: "Cell #108 · Phase now: Developing", min BT **216.1 K**. Solid navy past track, dashed red forecast track with T+30m … T+6h labels, ML probability chart by lead. |
| **Narration** | "Cell 108 is developing, with a cloud top of 216 kelvin: deep convection. The solid line is where it has been, the dashed line is where the motion field takes it over the next six hours, and the chart is the model's probability of deep convection near that path. The phase labels come from proposed rules, and cell-position skill is only verified as a diagnostic at 30 minutes. The screen says so." |

## 1:45–2:25 · 0–6 h Forecast → ML probability

| | |
|---|---|
| **UI action** | Click **4. 0–6 h Forecast** → **pySTEPS** → lead **T+2h**, and pause 2 s. Then click **ML probability** and tick **show what happened (replay)**. |
| **Screen** | pySTEPS map (hatched strip = no forecast at the inflow edge). Then the purple ML probability map with black observed outlines. Skill ribbon: **CSI 0.243 · BSS 0.27 · FSS40 0.53**, plus "ML CSI is at p ≥ 0.5; as a yes/no forecast ML does not beat pySTEPS beyond 60 min." |
| **Narration** | "Here is the forecast two hours ahead. First, pySTEPS: it moves the clouds along the observed motion. Now the ML probability: darker purple means more likely. The ribbon shows the skill measured on held-out days at this lead: a Brier skill score of 0.27, so better than climatology. It is honest about its limits: as a simple yes/no map, ML is not better than pySTEPS beyond one hour. The black outlines are what actually happened." |

## 2:25–3:05 · Historical Replay

| | |
|---|---|
| **UI action** | Click **6. Historical Replay**. Press **B** once (the prediction switches from ML to pySTEPS). Press **▶** for ~4 s, then pause. |
| **Screen** | Three synced maps titled WHAT THE SYSTEM KNEW · WHAT IT PREDICTED · WHAT ACTUALLY HAPPENED. Data-availability row, per-issue scorecard, would-have-issued advisories. The timeline advances 14:00 → 15:00 UTC. |
| **Narration** | "Replay puts three things side by side: what the system knew at the issue time, what it predicted, and what actually happened. I can switch the prediction between ML, pySTEPS and persistence, and play the day forward. Each forecast uses only data up to its issue time." |

## 3:05–3:40 · Model Performance

| | |
|---|---|
| **UI action** | Press **8** (Model Performance). Point at the red banner, then at the BSS chart, then at the table's first rows. |
| **Screen** | Banner: "ML's advantage is in probability skill (BSS). As a yes/no forecast (p ≥ 0.5) ML does not beat pySTEPS beyond 60 min." BSS vs lead chart; the final comparison table (BSS at 30 min: persistence 0.32, pySTEPS 0.44, neighbourhood pySTEPS 0.63, ML 0.67). |
| **Narration** | "This is the evidence, pooled over three held-out storm days. Motion extrapolation beats persistence at every lead on all three days, and useful skill lasts about two hours. The ML model gives the best probability forecasts up to about four hours. At six hours no method has skill, and we show that too." |

## 3:40–4:05 · Data Health

| | |
|---|---|
| **UI action** | Press **9** (Data Health). Point at the sources table, then the red bars in the QC strip, then the model card and limitations. |
| **Screen** | Source statuses; QC strip with **6 red frames (10:00–12:30 UTC)**; model card ml-v0 (train 18–31 May, validation 6–12 May, test E8/E10/E11); limitations list. |
| **Narration** | "Data health shows where the data came from and where it was weak: six frames on this day failed quality checks and are flagged, not hidden. The model card shows the training and test days, and the limitations are listed: three test days, one satellite channel, thirty-minute frames, and no radar or lightning validation yet." |

## 4:05–4:30 · Optional: Alert Center

| | |
|---|---|
| **UI action** | Click **5. Alert Center**. Click the timeline segment at **08:00 UTC**; the hover tooltip shows the time. On **Shopian**, click **Approve**, then **CAP**. |
| **Screen** | "Draft advisories at 08:00 UTC" with an EXERCISE badge: Shopian P 0.57 at +60 min, Kulgam P 0.69 at +30 min. After approval, the CAP 1.2 preview shows `<status>Exercise</status>`. The audit log records the action. |
| **Narration** | "The alert center turns probabilities into draft advisories, but a forecaster must approve each one. The output is a standard CAP message, marked as an exercise, and it is not an official warning." |

## 4:30–4:40 · Close

| | |
|---|---|
| **UI action** | Return to **2. Situation** (press 2). Hold on the map. |
| **Screen** | Situation map; footer "Research prototype — not an official IMD warning". |
| **Narration** | "Real data, strict baselines, stated limits. Next we want a forward-in-time test on new storm days, INSAT-3DS multi-channel input, and radar or lightning truth where access allows. Thank you." |

---

**Timing:** 4:40 total (4:05 without the optional Alert Center section, trimmed at the close).

**If you must cut to about 3 minutes:**
- drop the Alert Center section;
- shorten Replay to 25 s and Data Health to 15 s.

**Backup:** keep the verified screenshots (`apps/web/e2e-shots/verify/*.png`) ready as a slideshow fallback if the live recording fails.
