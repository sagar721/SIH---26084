# Final Results (for the SIH PPT) — evidence frozen at ml-v0

**Research prototype.**
- Real satellite data only: NOAA/NCEP/CPC merged IR, 4 km, 30 min.
- NW India, 26–34° N, 72–84° E.
- Target: deep-convective cloud (cloud top < 235 K) forecast 30 min–6 h ahead on a 2 km grid.
- All numbers come from 3 held-out event days (E8 14 May, E10 4 May, E11 16 May 2026) and are traceable to frozen files ([`FINAL_CLAIMS.md`](FINAL_CLAIMS.md), hashes in [`FREEZE_ml-v0.json`](FREEZE_ml-v0.json)).

---

## One-line result

> **Our calibrated ML model gives the best probability forecast of deep convection up to ~4 h on three held-out storm days. Motion extrapolation (pySTEPS) consistently beats persistence, and useful skill ends at about 2 h.**

## Slide 1 — Final comparison (held-out events pooled; identical pixels for all methods)

**Probability skill** — BSS vs training climatology, higher is better, 0 = no skill:

| Lead | Persistence | pySTEPS | Neighbourhood pySTEPS (no fit) | **ML (ml-v0)** |
|---|---|---|---|---|
| 30 min | 0.32 | 0.44 | 0.63 | **0.67** |
| 1 h | −0.04 | 0.10 | 0.41 | **0.51** |
| 2 h | −0.47 | −0.38 | 0.02 | **0.27** |
| 3 h | −0.69 | −0.67 | −0.23 | **0.13** |
| 4 h | −0.78 | −0.82 | −0.37 | **0.06** |
| 6 h | −0.84 | −1.11 | −0.59 | −0.03 |

**Yes/no skill** — CSI at p ≥ 0.5, higher is better:

| Lead | Persistence | pySTEPS | Neighbourhood pySTEPS | ML |
|---|---|---|---|---|
| 30 min | 0.511 | 0.586 | **0.596** | 0.583 |
| 1 h | 0.342 | 0.429 | 0.444 | **0.452** |
| 2 h | 0.176 | 0.258 | **0.264** | 0.243 |
| 3 h | 0.092 | **0.172** | **0.172** | 0.000* |

*From 2.5 h the calibrated ML probability stays below 0.5, so as a yes/no forecast it predicts no event there. It is useful there only as a probability.

## Slide 2 — What is consistent across all three storm days

- **pySTEPS beats persistence** on CSI and FSS (40 km) at **every lead, on 3 of 3 days**.
- **Useful skill horizon:** FSS 40 km stays above the useful line to **90 min for persistence and 120 min for pySTEPS on every day**.
- **ML beats the no-fit neighbourhood reference in probability skill** on 14 May and 4 May at every lead from 30 min to 3 h (95 % intervals exclude 0). On the weak 16 May event the gain is not significant.
- **Calibration:** ML probabilities are well calibrated, with calibration error 0.002–0.004 in every lead bin (reliability diagram).

## Slide 3 — Why forecasts fail after ~2 h (diagnosis, not a new model)

- **Most of the apparent over-forecasting of pySTEPS is a scoring-edge effect.** New storms enter from the unforecastable western inflow edge.
  - 14 May at 6 h: bias 2.61 on the scored region, but 0.70 over the whole domain.
- **Ignoring storm growth/decay is a smaller error.** Even a perfect area correction adds at most +0.04 CSI (14 May, 4 May).
- **Cell lifecycle trends from the satellite do not persist** from one 30-min step to the next. We therefore **did not** build a decay model; the pre-declared rule said stop.
- **Tracking quality was audited before any cell-level result was used.** Overlap-based tracking cut ID switches from 21 % to 0.4 %.

## Figures to use (all in `data/figures/`)

| Slide use | File |
|---|---|
| Real data + detected cells | `E8_20260514_fig1_satellite_frame.png`, `E8_20260514_fig2_detected_cells.png`, `E8_20260514_fig3_trajectories.png` |
| Baseline skill across events | `multi_event_fig11_skill_by_event.png`, `multi_event_fig12_csi_difference_ci.png` |
| Final comparison | `phase6_fig17_skill_vs_lead.png` |
| ML vs references with CIs | `phase6_fig18_ml_minus_pysteps_ci.png` |
| Calibration | `phase6_fig19_reliability.png` |
| Example forecast map | `phase6_fig20_example_probabilities.png` |
| Why skill is lost | `phase5_fig14_bias_decomposition.png`, `phase5_fig15_area_evolution_and_lifecycle_persistence.png` |
| Tracking audit | `E8_20260514_fig8_tracking_audit.png` |

## Honest limits (put on the results slide)

- **Only 3 held-out storm days**, all May 2026, NW India. No claim beyond them.
- **Trained on later days** (18–31 May) than the test days: a backward-in-time test.
- **Thin training data:** 14 days, 7 of them convective.
- **Satellite limits:** a single infrared channel, 30-min cadence, no radar or lightning validation.
- **Probability, not yes/no:** the ML advantage is in probability skill, not in yes/no forecasts beyond 1 h. Storm-initiation skill is not shown.

## What we do NOT claim

We do **not** claim:
- 6-h skill;
- hail, lightning or rain forecasts;
- storm-initiation prediction;
- cell-tracking accuracy;
- operational or real-time use;
- deep learning;
- generalisation to other seasons or regions.

See [`FINAL_CLAIMS.md`](FINAL_CLAIMS.md) §C.

## Next steps (not yet done; no results implied)

1. Forward-in-time test on new storm days after 31 May, or on pre-2026 archives.
2. Multi-channel INSAT-3D/3DS or Meteosat-9 inputs (water vapour, 15-min cadence).
3. Independent truth: IMD radar or lightning, where access allows.
4. An initiation-specific score, as in VALIDATION_PLAN §2.
