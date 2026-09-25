# Historical Replay Specification

**Purpose:** let evaluators step through real Indian events and see three things, side by side:
- **WHAT THE SYSTEM KNEW** — inputs available at time t, with realistic latency
- **WHAT IT PREDICTED** — forecasts issued at t, for each valid time t+Δ
- **WHAT ACTUALLY HAPPENED** — observations and ground truth at t+Δ

A baseline comparison is available on every frame.

---

## 1. Events (from research Part 12)

| Code | Date (IST) | Place | Hazard | Year's split role | Key truth layers |
|---|---|---|---|---|---|
| E1 | May 2018 (2–3 storm days; pick in Phase 8) | S. Kerala | Pre-monsoon thunderstorms | Train year → **excluded from fitting** | TERLS 3D radar, ISS-LIS, IMERG |
| E2 | 25 Jun 2020 | Bihar / UP | Lightning (83 deaths, Bihar) | Train year → excluded | ISS-LIS (if overpass), IMERG, news |
| E3 | 13 May 2024, afternoon | Mumbai / Thane | Squall / dust storm | Validation year → **excluded from calibration** | IMERG, news (Ghatkopar) |
| E4 | 2 May 2025, ~05:15–08:30 | Delhi-NCR | Severe thunderstorm, 80 km/h gust | Test | IMERG; IMD station values quoted from press |
| E5 | 30 Jun–1 Jul 2025, night | Mandi (HP) | Cloudburst cluster | Test | IMERG/GSMaP, reports |
| E6 | 5 Aug 2025, ~13:45 | Dharali (UK) | Cloudburst / flash flood | Test | IMERG, reports ("cloudburst" unconfirmed by IMD) |
| E7 | 14 Aug 2025, ~11:30 | Chasoti, Kishtwar (J&K) | Cloudburst / debris flow | Test | IMERG, reports |
| E8 | 1 May & 14 May 2026 | Haryana / Delhi-NCR / W. UP / UK | Hail (multi-station) | Test | **IMD hail report**, IMERG, DPR if overpass |
| E9 | 21 Mar, 5 Apr, 9 Apr 2026 | UP / Haryana / Rajasthan / UK | Hail + crop damage | Test | IMD hail report, IMERG |

**Notes:**
- E1 falls outside the NW-India domain. It is a separate Kerala sub-domain used only for the radar case (stretch B).
- Every event's T0 carries its source citation (`config/events.yaml`).

## 2. Timeline

- **Steps:** T−60, T−45, T−30, T−15, **T0**, T+15, T+30 … T+360 (15-min steps; 29 issue times).
- **T0** = first reported impact time from the cited source. If only a date is known (E8/E9), T0 = time of first IMERG ≥ 10 mm/h within 25 km of the first reporting station, labelled "T0 (proxy)".
- At each **issue time t**, the predicted pane lets the user choose a lead **Δ ∈ {15, 30, 60, 120, 180, 240, 360}**. The observed pane then shows t+Δ.

## 3. Latency model (`config/latency.yaml`) — the "what the system knew" rule

| Source | Available at | Rationale |
|---|---|---|
| SEVIRI IODC slot (nominal time s) | s + 15 min | Scan + dissemination (PROPOSED; LIVE hourly NRT is coarser) |
| INSAT-3DR/3DS L1B | s + 3 days for general users → **not available operationally** in replay; shown greyed with "general-user latency 3 days" | MOSDAC policy (VERIFIED) |
| GFS cycle c | c + 5 h | Typical NOMADS availability (NEEDS VERIFICATION; measure) |
| ERA5 | Not used as a replay input (5-day latency); GFS substitutes for the environment | VERIFIED latency |
| IMERG Early | s + 4 h | VERIFIED |
| GSMaP_NOW | s + 0.5 h | VERIFIED |
| ISS-LIS, DPR, IMD hail report, news | Truth only — never inputs | — |

**Rule:** a replay bundle at issue time t contains input i only if `obs_time(i) + latency(i) ≤ t`. The bundle builder enforces this, and `leakage_check.py` re-verifies it independently.

**Model consistency:** replay uses the **same frozen model version** as the Phase 11 report. The environment in replay is GFS (as in LIVE), not ERA5. If the model was trained on ERA5, the GFS-vs-ERA5 skill gap is reported (validation ablation A2 variant).

## 4. Bundle format

`data/replay/{event}/{issue_time}.json` + tiles in `data/replay/{event}/tiles/`

```json
{
  "event": "E8",
  "issue_time": "2026-05-14T08:30:00Z",
  "t_rel_min": -30,
  "envelope": {"mode": "REPLAY", "model": {"name": "suite", "version": "0.5.0", "git_sha": "…"}, "data_tier": "SAT+NWP"},
  "knew": {
    "inputs": [{"source": "SEVIRI_IODC", "obs_time": "2026-05-14T08:15:00Z", "status": "OK"},
               {"source": "INSAT-3DS_L1B", "status": "NOT_AVAILABLE_OPERATIONALLY"},
               {"source": "GFS_0p25", "cycle": "2026-05-14T00:00Z", "status": "OK"},
               {"source": "DWR", "status": "UNAVAILABLE"}],
    "layers": {"bt_108": "tiles/0815_bt108.png"},
    "cells": "cells_0815.geojson"
  },
  "predicted": {
    "by_lead": {
      "60": {"cells": "fc_0930_model.geojson", "hazard_tiles": {"lightning": "…", "rain20": "…", "hail_potential": "…"},
             "eta": [{"place": "Ambala", "eta_min": 52, "lo90": 38, "hi90": 71, "p_arrival": 0.72}],
             "alerts_would_issue": [{"place": "Ambala", "hazard": "hail_potential", "level": "HIGH"}]}
    },
    "baselines": {"persistence": {"60": {"cells": "…"}}, "pysteps": {"60": {"cells": "…"}}, "rules": {"60": {"…": "…"}}}
  },
  "happened": {
    "by_lead": {"60": {"cells": "obs_0930.geojson", "imerg": "tiles/0930_imerg.png",
                       "hail_reports": [{"place": "Ambala", "date": "2026-05-14", "source": "IMD NW-India report"}]}}
  },
  "hash": "sha256:…"
}
```

## 5. UI behaviour (see UI_UX_SPEC §4.4)

- **Three synced map panes** (pan/zoom locked). Titles are fixed: **WHAT THE SYSTEM KNEW · WHAT IT PREDICTED · WHAT ACTUALLY HAPPENED**.
- **Timeline:** issue-time scrubber from T−60 to T+6 h; lead selector; ▶ play at 1×/2×/5× (1× = one issue step per 2 s).
- **BASELINE toggle:** the predicted pane switches to persistence / pySTEPS / rules for the same issue time and lead, so comparisons are like-for-like.
- **Data availability row:** per source for this issue time (OK / LATE / NOT AVAILABLE OPERATIONALLY / UNAVAILABLE).
- **"Would-have-issued" alerts:** shown at the issue time they would fire, with lead time relative to T0.
- **Banner:** "Replay of observed data. This event was excluded from model training and calibration." (E1–E9.)

## 6. Event scorecard (computed by `ml/verification`, not in the UI)

| Metric | Definition |
|---|---|
| First alert lead time | T0 − earliest issue time at which the model would have issued an alert for an affected place (min); same for each baseline |
| Hits / misses / false alarms | Per affected place in the window, at the chosen threshold |
| CI lead | Minutes between the first CI flag and the first BT < 235 K on the event's main track |
| ETA error | Predicted − observed arrival at each affected place, per lead |
| Interval hit | Whether the observed arrival fell inside the 80/90 % interval |

Scorecards also go into `evaluation/metrics.json` under `replay/{event}`. Pooled numbers are **not** mixed with test-set metrics.

## 7. Build process

1. `pipelines/replay/build_bundle.py --event E8`:
   - Loads the frozen model.
   - Iterates issue times.
   - Assembles only latency-eligible inputs.
   - Runs the full pipeline (tracking online mode → features → heads → calibration → ETA).
   - Runs the baselines.
   - Writes bundles + tiles.
2. `pipelines/replay/leakage_check.py --event E8` independently recomputes eligibility from the manifests and fails on any violation.
3. Bundles are precomputed and shipped for the offline demo.

## 8. Acceptance criteria

- `leakage_check` passes for all events (zero violations).
- Every event is confirmed absent from train/validation manifests (automated test).
- Frame switch < 300 ms with bundles preloaded; the full event (29 issue times × 7 leads) plays offline.
- The baseline toggle is available for every issue time and lead.
- Every "happened" layer shows its source and citation.
- The scorecard matches `metrics.json` exactly.
- Missing inputs are shown as gaps, never interpolated silently.
