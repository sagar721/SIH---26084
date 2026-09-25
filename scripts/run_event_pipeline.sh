#!/usr/bin/env bash
# Phase 4: run the unchanged Phase 1-3 pipeline on one event (download must be done first).
#   bash scripts/run_event_pipeline.sh E8a_20260501
set -euo pipefail
EV="$1"
PY="${PY:-.venv/bin/python}"
$PY -m scripts.run_first_event --event "$EV"          # cube -> tobac tracking -> lifecycle -> figs 1-4
$PY -m scripts.run_baseline --event "$EV"             # Phase-2 persistence + pySTEPS, config/baseline.yaml
$PY -m scripts.make_baseline_figures --event "$EV"    # figs 5-7
$PY -m scripts.run_tracking_v2 --event "$EV" --mode none   # Phase-3 v2 tracks (object diagnostics only)
$PY -m scripts.run_tracking_v2 --event "$EV" --mode flow
for v in v1 v2_none v2_flow; do $PY -m scripts.audit_tracking --event "$EV" --version "$v" > /dev/null; done
