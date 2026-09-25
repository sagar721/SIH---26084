# Phase 3 — Tracking Audit (E8, 14 May 2026)

**Status:** Phase 3 complete · **Inputs:** Phase-1 features/mask/cube, Phase-2 pySTEPS motion fields (read-only) · **Phase 1–2 outputs and grid metrics are unchanged** (byte-identical; tested).

**Bottom line:**
- The Phase-1 tobac tracks were not usable as object truth.
- The evidence-backed fixes remove the clear linking errors.
- Residual centroid jitter and truth-definition sensitivity remain. **Object-level skill is supported only for a narrow claim** (§6): on this one event, at 30–60 min, field advection has lower centroid error than persistence for most cold cells, under both linking definitions. Nothing beyond 60 min is claimed.

---

## 1. What was audited (before any change)

**Audit metrics** (`ml/tracking/audit.py`) are applied identically to every track version:
- **Direction reversals:** fraction of consecutive step pairs turning > 90°, both steps ≥ 4 km. Random direction gives 0.5.
- **Flow consistency:** correlation between each step's displacement and the mean pySTEPS flow over the parent segment. The flow comes from frames ≤ t and is used only as an independent reference.
- **Cold-segment link checks:**
  - zero-overlap links (parent and child segments disjoint with and without a flow shift);
  - **ID-switch candidates** (another segment overlaps the parent more than the linked child does);
  - area jumps (child/parent area > 2 or < 0.5).
- **merge_split_MEST family spread:** distance between members present at the same time.
- **Suspicious-track ranking:** reversals + ID-switch candidates + zero-overlap links per cell (`audit/suspicious_tracks_v1.csv`).

## 2. Findings on the Phase-1 (v1) tracks

| # | Finding | Evidence (`audit/audit_v1.json`) |
|---|---|---|
| T1 | **Motion is essentially noise.** Direction reversals occur in **47 %** of step pairs (random = 50 %). Correlation of step displacement with the flow is **0.12 (x) / 0.06 (y)**. Median deviation from the flow is 21.8 km per 30 min, larger than the flow step itself (17.8 km). | all cells, 1,880 steps |
| T2 | **Most tracked objects are not storms.** **81 %** of tracked rows are warm features without a < 245 K segment; 1,421 of 1,880 steps are warm→warm. | `v1_causes.step_kinds` |
| T3 | **Threshold-level switching moves the position.** 15.5 % of steps change the feature's detection threshold level; their median step is 28.5 km vs 19.9 km otherwise. | `v1_causes` |
| T4 | **Wrong links between cold segments.** Of 282 cold→cold links: **20.6 %** ID-switch candidates, **5.7 %** zero overlap, **40.1 %** area jumps. | `segmented_rows_only` |
| T5 | **merge_split_MEST families are not credible genealogy.** 103 multi-cell families; members present at the same time are a median **68 km** apart (p90 123 km, max **221 km**). | `v1_causes` |
| T6 | **Worst tracks, inspected.** The top-ranked cell #153 (17 frames) has 7 reversals, 2 ID-switch candidates and 3 zero-overlap links. Fig. 9 shows it hopping between separate cold segments. | `suspicious_tracks_v1.csv`, fig. 9 |

**Implication for Phase 2:** nearest-feature linking plus jitter also **biases object truth toward persistence** (the "observed" successor is simply the nearest feature). That is consistent with persistence scoring best in `BASELINE_EVAL.md` §4.

## 3. Fixes (declared before measuring their effect; `config/tracking_v2.yaml`)

| Fix | Addresses | What changed | Code |
|---|---|---|---|
| F1 Object definition | T2 | Object-level work uses only features with a < 245 K segment. Warm features remain in `features.parquet` (for future CI work) but are not storm objects. | `scripts/run_tracking_v2.py` |
| F2 Overlap linking | T1, T4, T5 | TITAN-style: link segments t→t+1 when overlap / min(area) ≥ 0.2.<br>• Continuation = mutual best overlap.<br>• Other edges are classified **once** as MERGE (parent's best child continues another parent) or SPLIT (child's best parent continues elsewhere).<br>• Families are connected components of these events, replacing merge_split_MEST.<br>• Online: frame t+1 links use only frames t, t+1 (and, in "flow" mode, the motion at t from frames ≤ t). | `ml/tracking/overlap_link.py` |
| F3 Position | T3 | Centroid weighted by (245 K − BT) over the segment, replacing the jumpy multithreshold feature position. | `overlap_link.coldness_centroid`, `lifecycle.py` (`centroid="coldness"`; default unchanged) |

**Not changed:**
- detection thresholds;
- segmentation (watershed < 245 K);
- phase rules v0;
- Phase-2 baselines and their settings.

**Truth-definition sensitivity (design choice).** Any linking rule favours some predictor:
- Eulerian overlap ("none") favours persistence.
- Flow-shifted overlap ("flow") favours field advection.

Both are run. **Primary lifecycle output = `tracking_v2_none`.** `tracking_v2_flow` is a sensitivity variant. Overlap thresholds 0.1 and 0.3 were also run as a sensitivity check, not as a selection.

## 4. Before / after tracking diagnostics

| Metric | v1 all | v1 cold rows | **v2 overlap (primary)** | v2 flow-overlap |
|---|---|---|---|---|
| Cells (≥ 2 frames) | 613 | 174 | 88 | 95 |
| Cells ≥ 2 h | 181 | — | 23 | 22 |
| Direction reversals (random = 0.5) | 0.468 | 0.384 | **0.345** | 0.268 |
| ID-switch candidates (cold links) | 0.206 | 0.206 | **0.004** | 0.127 |
| Zero-overlap links | 0.057 | 0.057 | 0.000 (*by construction*) | 0.000 (*by construction*) |
| Area jumps > 2× | 0.401 | 0.401 | **0.279** | 0.292 |
| corr(step, flow) x / y | 0.12 / 0.06 | 0.07 / 0.13 | 0.10 / 0.16 | 0.28 / 0.28 (*partly circular*) |
| Median deviation from flow (km / 30 min) | 21.8 | 21.8 | 20.4 | 16.5 |

**Sensitivity to the overlap threshold** (v2 overlap, 0.1 / 0.2 / 0.3):
- cells: 90 / 88 / 87
- reversals: 0.322 / 0.345 / 0.348
- area jumps: 0.281 / 0.279 / 0.272

The results are insensitive to the threshold.

**Residual problems, not fixed:**
- **Reversals are still 27–35 %.** Real storms rarely reverse at this rate, so centroid jitter remains.
- **Area jumps (28 %) are not explained by merges/splits.** Jump steps coincide with a merge/split event 48 % of the time, non-jump steps 50 %. They come from the **watershed segmentation**: segments re-partition as features appear or vanish. Changing segmentation (e.g., connected components, cold-core objects) is not yet evidence-backed and is NEEDS VERIFICATION.
- **Derived motion depends on the truth definition.** Deep cells living ≥ 2 h (21 / 20 cells) have a median net speed of **32.6 km/h** (IQR 22–40, heading 102°) under Eulerian overlap and **53.5 km/h** (IQR 42–59, heading 94°) under flow overlap.

## 5. Regenerated lifecycle outputs (`data/processed/E8_20260514/tracking_v2_<mode>/`)

| File | Content |
|---|---|
| `cells_per_frame.csv` | Per cell-frame: coldness centroid, area, cold core, min BT, motion, rates, phase (rules v0), `touches_missing` |
| `cells_summary.csv` | Per cell: lifetime, net motion, extremes, phases, family |
| `genealogy_events.csv` | Explicit MERGE/SPLIT events: frame, from/into cell, overlap fraction. v2 overlap: **151 merges, 123 splits** |
| `object_predictions.csv`, `object_metrics_by_lead.csv`, `object_paired_comparison.csv` | Recomputed object diagnostics |
| `run_summary.json` | Config, counts, input/output SHA-256 |

**Phase labels (v2 overlap):** Unclassified 152 · Developing 139 · Decaying 31 · **Mature 6** (was 0 in v1). Overlap tracks keep areas stable often enough for the v0 "Mature" rule to fire occasionally. The rules are still unvalidated (D7).

## 6. Object diagnostics after the fixes (same Phase-2 baseline definitions; cold cells only)

Median centroid error (km). *n* = scored (cell, issue) pairs / distinct cells.

| Lead | Tracks | Persistence | Constant velocity | Field advection | n | Paired: field better than persistence |
|---|---|---|---|---|---|---|
| 30 min | v1 (Phase 2, all objects) | 20.3 | 24.3 | 21.0 | 1,248 / — | — |
| 30 min | **v2 overlap** | 27.0 | 25.6 | **20.3** | 151 / 43 | **0.59** (median diff −5.4 km) |
| 30 min | v2 flow-overlap | 27.4 | 22.7 | 17.2 | 164 / 45 | 0.71 (−12.4 km) |
| 60 min | v1 | 28.5 | 40.8 | 31.9 | 868 / — | — |
| 60 min | **v2 overlap** | 44.8 | 44.6 | **34.0** | 108 / 28 | **0.60** (−9.0 km) |
| 60 min | v2 flow-overlap | 51.7 | 44.6 | 31.7 | 119 / 28 | 0.72 (−22.6 km) |
| 120 min | **v2 overlap** | 71.5 | 72.8 | 64.1 | 58 / 14 | **0.50** (+0.3 km) |
| 120 min | v2 flow-overlap | 94.3 | 90.4 | 60.9 | 70 / 15 | 0.71 (−52.1 km) |

**What the audit supports:**
- **Supported (narrow):**
  - On E8, at **30 and 60 min**, pySTEPS field advection places cold cells closer than persistence in the majority of paired cases under **both** truth definitions and all overlap thresholds (0.59–0.62 Eulerian; 0.71–0.74 flow).
  - This reverses the Phase-2 v1 ranking, which was an artefact of nearest-feature truth (§2).
- **Not supported:**
  - **Beyond 60 min:** the Eulerian-overlap truth shows no difference (≈ 0.50), while flow-overlap shows large gains. The conclusion depends on the truth definition, so none is drawn.
  - **Constant velocity:** it is no better than persistence under Eulerian overlap (0.52 at 30 min, then < 0.5), so no claim is made.
  - **Magnitudes:** 20–27 km median error at 30 min is comparable to one step of real motion. Absolute object accuracy is poor.
- **Caveats:**
  - Sample sizes are small: 43 cells at 30 min, 28 at 60 min, 14 at 120 min.
  - Pairs from the same cell are not independent.
  - There is one event, so no confidence intervals are possible.

**Grid metrics (Phase 2) remain the primary evaluation** and are unchanged.

## 7. Figures

| # | File | Content |
|---|---|---|
| 8 | [`data/figures/E8_20260514_fig8_tracking_audit.png`](../data/figures/E8_20260514_fig8_tracking_audit.png) | Before/after audit metrics |
| 9 | [`data/figures/E8_20260514_fig9_worst_v1_track.png`](../data/figures/E8_20260514_fig9_worst_v1_track.png) | Most suspicious v1 track (#153) vs the v2 tracks of the same features |
| 10 | [`data/figures/E8_20260514_fig10_object_diagnostics_v2.png`](../data/figures/E8_20260514_fig10_object_diagnostics_v2.png) | v2 object diagnostics, both truth definitions, with paired fractions and distinct-cell counts |

## 8. Reproduce

```bash
.venv/bin/python -m scripts.audit_tracking --event E8_20260514 --version v1
for m in none flow; do .venv/bin/python -m scripts.run_tracking_v2 --event E8_20260514 --mode $m; \
  .venv/bin/python -m scripts.audit_tracking --event E8_20260514 --version v2_$m; done
for ov in 0.1 0.3; do for m in none flow; do .venv/bin/python -m scripts.run_tracking_v2 --mode $m --min-overlap $ov; \
  .venv/bin/python -m scripts.audit_tracking --version v2_${m}_ov$ov; done; done   # sensitivity only
.venv/bin/python -m scripts.make_audit_figures --event E8_20260514
.venv/bin/python -m pytest -q
```

Two consecutive v2 runs produced byte-identical CSVs.

## 9. Tests (`tests/test_phase3.py`, 13 new; 30 total pass)

**F2 overlap linking:**
- continuation keeps the id;
- no overlap → new cell;
- merge and split each classified exactly once, and form one family;
- overlap threshold enforced;
- flow mode shifts the parent;
- **causality** (past links unaffected by a different future);
- real data: every Eulerian continuation satisfies overlap ≥ 0.2.

**F1:** real v2 rows are all cold segments.

**F3:**
- the coldness centroid is pulled to cold pixels and falls back to the plain centroid;
- all real v2 rows use it.

**Audit metric:** a zig-zag test on hand paths.

**Integrity:**
- Phase-1 lifecycle tables and Phase-2 grid metrics are byte-identical to their recorded hashes;
- v2 outputs match their run hashes.

## 10. NEEDS VERIFICATION

1. **Segmentation-driven area jumps (28 %).** Needs a segmentation study (connected components / cold-core objects / multi-threshold hierarchy) before object areas or growth rates are used as evidence.
2. **Which truth definition is "right"** can't be settled from satellite IR alone. An independent reference (radar or lightning-cell tracks) or manual labelling is needed. **No manual audit sheet exists yet** (PRD F4's ≥ 90 % criterion is still unmet and not claimed).
3. **Overlap threshold 0.2** is PROPOSED. Results are insensitive over 0.1–0.3, but it is not validated against manual tracks.
4. **Single event**, so no CIs; the object claim in §6 is event-specific.
5. **Carried over:** parallax, satellite ID, phase-rule validation (D7), the 30-min cadence.
