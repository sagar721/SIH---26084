# Phase 5 — Decay-Aware Forecast: Error Decomposition and Stop Decision

**Status:** Phase 5 finished under the stop clause. No decay-aware model was built.

**Question:** does modelling storm growth/decay improve the pySTEPS baseline?

**Answer on E8, E10 and E11:**
- **Cell lifecycle features:** the existing ones are too unreliable to drive a decay model (§3), so the stop clause was applied instead of forcing one.
- **Maximum possible benefit:** the decomposition (§2) bounds what *any* uniform intensity/area correction could gain. It is small pooled over the day, and concentrated in the afternoon/evening decay and the growth transitions.

**Protocol and scope:**
- Phase 4 protocol and scoring mask; `config/baseline.yaml` is unchanged (hash in provenance); grid metrics are primary.
- Nothing is fitted.
- No claim beyond these 3 events.

---

## 1. Reproduce

```bash
.venv/bin/python -m scripts.decompose_advection_error   # task 1, ~2.5 min -> data/processed/multi_event/phase5/decomposition_*
.venv/bin/python -m scripts.lifecycle_reliability       # task 2 gate      -> lifecycle_reliability.csv, lifecycle_decision.json
.venv/bin/python -m scripts.make_phase5_figures         # figs 14-16
.venv/bin/python -m pytest -q                           # 54 tests (53 pass, 1 skipped: excluded event E8a)
```

**Checks:**
- The decomposition re-scores pySTEPS from scratch. Its per-issue contingency tables equal the Phase-4 files exactly (tested).
- A rerun of the reliability gate is byte-identical.

## 2. Task 1 — edge exclusion vs unchanged intensity

### Method

For each issue time k and lead L (event BT < 235 K), define:

| Symbol | Meaning |
|---|---|
| V | the Phase-2/4 scoring mask |
| D | domain pixels with a valid observation. Includes the inflow edge, where the advected forecast is NaN. |
| A0 | observed event area at issue time |
| Af, AfV | advected event area in the domain, and inside V |
| AoD, AoV | observed event area at k+L in D, and inside V |

Pooled over issue times per lead, the frequency bias factorises exactly (tested):

```
bias_V = AfV/AoV = E × C × G
E = (AfV/Af)/(AoV/AoD)   edge exclusion: > 1 when observed events sit disproportionately in the unscored edge
C = Af/A0                advected cold area change (outflow / interpolation)
G = A0/AoD               unchanged-intensity error: > 1 when the real cold area decayed, < 1 when it grew
```

bias_D = C × G is the bias if the edge were scored as "no forecast event".

**Two CSI diagnostics:**
- **CSI_Dedge:** CSI with the edge scored.
- **CSI_oracle (ORACLE — uses the observation):** the advection forecast with its threshold set per (issue, lead) so that its area on V equals the observed area. This bounds what a perfect uniform growth/decay correction of the advected field could achieve.

### Results (`decomposition_by_lead.csv`)

| Event | Lead | bias_V | E edge | C advected | G intensity | bias_D | Obs events in edge | CSI P | CSI pySTEPS | CSI edge scored | CSI ORACLE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E8 | 60 | 1.28 | 1.14 | 1.12 | 1.00 | 1.12 | 17 % | 0.352 | 0.428 | 0.384 | 0.463 |
| E8 | 120 | 1.44 | 1.33 | 1.08 | 1.00 | 1.09 | 30 % | 0.191 | 0.245 | 0.206 | 0.269 |
| E8 | 180 | 1.60 | 1.57 | 1.01 | 1.00 | 1.01 | 42 % | 0.106 | 0.156 | 0.121 | 0.161 |
| E8 | 360 | 2.61 | 3.76 | 0.73 | 0.96 | 0.70 | 76 % | 0.038 | 0.043 | 0.023 | 0.048 |
| E10 | 60 | 1.18 | 1.07 | 1.05 | 1.05 | 1.10 | 11 % | 0.336 | 0.428 | 0.409 | 0.455 |
| E10 | 120 | 1.21 | 1.11 | 1.03 | 1.06 | 1.09 | 17 % | 0.169 | 0.263 | 0.247 | 0.283 |
| E10 | 180 | 1.15 | 1.12 | 0.97 | 1.07 | 1.03 | 19 % | 0.089 | 0.178 | 0.165 | 0.197 |
| E10 | 360 | 0.98 | 1.17 | 0.72 | 1.16 | 0.84 | 21 % | 0.019 | 0.054 | 0.047 | 0.071 |
| E11 | 60 | 1.23 | 1.05 | 1.18 | 0.99 | 1.17 | 7 % | 0.341 | 0.441 | 0.425 | 0.498 |
| E11 | 120 | 1.40 | 1.19 | 1.22 | 0.97 | 1.18 | 19 % | 0.160 | 0.283 | 0.256 | 0.337 |
| E11 | 180 | 1.56 | 1.50 | 1.24 | 0.84 | 1.04 | 37 % | 0.025 | 0.213 | 0.173 | 0.281 |
| E11 | 360 | 1.53 | 4.80 | 1.25 | 0.26 | 0.32 | 80 % | 0.000 | 0.002 | 0.001 | 0.010 |

**Findings:**
1. **The bias growth reported in Phases 2/4 is mainly an edge/sampling effect.**
   - On E8, E carries most of the log-bias at every lead from 90 min on. At 6 h, 76 % of observed cold pixels lie in the unscored inflow edge.
   - Scored over the whole domain, E8's bias is 0.70 at 6 h, not 2.61. The same pattern holds on E11.
   - What E measures: new and entering convection upstream is excluded from scoring, while the advected shields that decay downstream remain in V.
2. **Pooled over each day, the unchanged-intensity term is small on E8 and E10** (G = 0.96–1.16). On E11, observed cold area grows (G = 0.26 at 6 h), so extrapolation under-forecasts domain-wide.
3. **Pooled G hides opposite errors at different times of day** (`decomposition_by_issue_block.csv`; fig. 15):
   - **Growth (G < 1):** morning issues (00–12 UTC) on E8/E10, and 12–18 UTC on E11.
   - **Decay (G > 1):** afternoon/evening issues, 12–24 UTC. At +180 min, G = 2.1 (E8, 12–18 UTC issues) and 16.9 (E8, 18–24 UTC).
4. **Upper bound on the benefit of any perfect uniform growth/decay correction:** +0.004 to +0.035 CSI (E8), +0.014 to +0.026 (E10), +0.008 to +0.083 (E11).
   - Larger in 6-h issue blocks: up to +0.08 for E10 12–18 UTC issues, +0.16 for E11 12–18 UTC.
   - It is **negative** in some blocks: −0.02 for E8 00–06 UTC at 60 min, −0.01 for E10 06–12 UTC.
   - Fig. 16 shows why. Matching the area also removes correctly forecast cold pixels, because positions are wrong: on E8, 9,540 correct vs 4,294 wrong removals.
   - After a perfect area correction, CSI still falls to ~0.27–0.34 at 2 h. **Placement error and new development, not intensity, dominate the remaining error.**

## 3. Task 2 gate — are the existing lifecycle features reliable enough?

**Candidate model** (the simplest deterministic extension):
- At issue time, take each Phase-3 v2 cell's current Lagrangian tendency (existing columns).
- Extrapolate it with AR(1) damping and apply it to the cell's pixels.
- Advect with the unchanged pySTEPS motion.
- Its only parameter is φ, the lag-1 autocorrelation of the tendency, to be estimated on E8 only. E10/E11 would be held out.

**Rule** (set before the E8 numbers were computed; written into the script, not to a file beforehand): build only if some tendency on E8 has φ > 0 with a 95 % cell-bootstrap CI excluding 0.

| Tendency (E8 = development) | Steps | n pairs | φ | 95 % CI |
|---|---|---|---|---|
| min-BT change | all | 152 | −0.03 | [−0.22, 0.15] |
| min-BT change | no merge/split | 31 | 0.05 | [−0.52, 0.66] |
| log area (< 245 K) | all | 152 | 0.16 | [−0.01, 0.31] |
| log area | no merge/split | 31 | 0.37 | [−0.11, 1.09] |
| log(1 + cold-core area) | all | 152 | −0.25 | [−0.53, 0.03] |

**Decision: STOP.** No tendency passes.

**Supporting evidence** (`lifecycle_reliability.csv`, `lifecycle_phase_outcomes.csv`):
- **Min-BT does not persist; cold-core mean-reverts.** The min-BT tendency has no persistence on any event (φ from −0.20 to 0.21). The cold-core tendency is negative, which is the signature of the tracking/segmentation jitter found in Phase 3.
- **Merges/splits dominate.** 86 % of E8's cold pixels at issue time are in cells whose current step includes a merge or split. Only 14 % (E10 14 %, E11 44 %) have a clean tendency.
- **Phase labels don't predict.**
  - The next-step dissipation rate is 25–29 % in every E8 phase except Mature (n = 6).
  - Developing cells do not grow on average (−0.02 in log area).
  - Next-step log-area SD is 0.57–0.82, far larger than differences between phase means.
- **Held-out QA — borderline for log-area only.** On E10/E11 the log-area φ is 0.13–0.25 and its CI excludes 0. Even there, AR(1) implies a forecastable change of only φ/(1−φ) ≈ 0.15–0.33 × the last step's change.
  - Combined with the §2 bound, the expected effect is well under +0.03 CSI.
  - This did not change the decision, which uses E8 only.

**Consequence:**
- Tasks 3–6 (build, freeze, evaluate and compare a decay-aware forecast) were **not executed**.
- The comparison available is **persistence vs pySTEPS vs the ORACLE bound** (§2). The oracle is not a forecast.

## 4. Where and when growth/decay modelling could help or hurt (from the bound; 3 events only)

| When (issue time, UTC) | What happens | Could help? |
|---|---|---|
| 12–18 on E8/E10; 18–24 on E11 | Afternoon/evening decay: advected shields persist while the real ones warm | Yes, most: bound +0.03 to +0.09 |
| 12–18 on E11 | Explosive growth (area ×4–6) | Yes, bound up to +0.16. This needs *growth/initiation*, which no decay term supplies. |
| 00–12 on E8/E10 | Morning growth / small systems | Little: bound −0.02 to +0.05, can be negative |
| 18–24 on E8 | Near-total dissipation | No: bias up to 22, but CSI ≈ 0 for every method |

| Where | Effect |
|---|---|
| Downstream of the motion (east, inside V) | Area correction mostly removes false alarms at shield edges |
| Upstream inflow edge (west) | Not scored at all; the dominant source of long-lead misses. No decay model can address it. |

## 5. Figures

| # | File | Content |
|---|---|---|
| 14 | `data/figures/phase5_fig14_bias_decomposition.png` | log bias = log E + log C + log G vs lead per event; CSI of persistence / pySTEPS / edge-scored / ORACLE |
| 15 | `data/figures/phase5_fig15_area_evolution_and_lifecycle_persistence.png` | Observed cold-area evolution vs pySTEPS +120 min area (inside V and domain); E8 tendency scatter (t vs t+30 min) with AR(1) fits |
| 16 | `data/figures/phase5_fig16_forecast_differences.png` | pySTEPS +120 min contingency maps with unscored edge; pixels a perfect area correction would flip (correct / wrong) |

## 6. Outputs (`data/processed/multi_event/phase5/`)

| File | Content |
|---|---|
| `decomposition_per_issue.csv` | Per event × issue × lead: A0, Af, AfV, AoD, AoV, scored counts, contingency on V / D-edge / ORACLE |
| `decomposition_by_lead.csv` | Pooled E, C, G, bias, CSI variants |
| `decomposition_by_issue_block.csv` | Same by 6-h issue-time block |
| `decomposition_provenance.json` | Config and cube hashes, output hashes |
| `lifecycle_reliability.csv` | φ with 95 % cell-bootstrap CI per event, tendency and step type; coverage |
| `lifecycle_phase_outcomes.csv` | Next-step area / min-BT change and dissipation rate by phase |
| `lifecycle_decision.json` | Rule, decision, bootstrap settings, input/output hashes |

## 7. NEEDS VERIFICATION

1. **The decision rule** was fixed in the script before the E8 numbers were computed, but not archived beforehand. The log-area feature is borderline: it passes on E10/E11 but not on E8.
2. **The ORACLE bound covers uniform corrections only.** A cell-local correction could in principle exceed it. With cell tendencies this unreliable, that is not demonstrable here.
3. **Diurnal growth/decay is the clearest intensity signal**, but a time-of-day model needs many event days to estimate; three days cannot support it. It also lies outside the "existing lifecycle features only" constraint.
4. **The edge term depends on the pySTEPS inflow rule** (outval = NaN) and on the domain size. A larger motion/advection domain than the scoring domain would reduce it. Not tested.
5. **Only 3 events, from May 2026 in NW India.** Tracking-truth and hail-report caveats carry over from Phases 3–4.
