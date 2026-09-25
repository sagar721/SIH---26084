"""Phase-7 evidence freeze (provenance only: computes nothing scientific, changes no result).

  python -m scripts.freeze_evidence

Writes docs/FREEZE_ml-v0.json with SHA-256 of every config, code file, raw-data manifest, cube, processed output,
model artifact, figure and document that the final claims rest on, plus the environment and a test-suite run.
tests/test_phase7_freeze.py re-hashes everything and fails if any frozen file changes.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

OUT = Path("docs/FREEZE_ml-v0.json")
MODEL_DIR = Path("data/models/ml-v0")
EXCLUDE = {"tests/test_phase7_freeze.py", "data/PROVENANCE.md", str(OUT)}   # self-referential / append-only log
GLOBS = ["config/*.yaml", "ml/**/*.py", "pipelines/**/*.py", "scripts/*.py", "scripts/*.sh", "tests/*.py",
         "requirements.txt", "pytest.ini", "SIH26084_Research_Report.md", "docs/*.md",
         "data/raw/cpc_merged_ir/manifest.json", "data/raw/hail_reports/*", "data/interim/grid2km/*.nc",
         "data/processed/**/*", "data/models/ml-v0/*", "data/figures/*.png"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_files() -> list[Path]:
    files = set()
    for g in GLOBS:
        files |= {p for p in Path(".").glob(g) if p.is_file()}
    return sorted(p for p in files if str(p) not in EXCLUDE and p.suffix != ".log" and "__pycache__" not in p.parts)


def run_tests() -> dict:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "--ignore=tests/test_phase7_freeze.py"], capture_output=True, text=True)
    last = [ln for ln in r.stdout.strip().splitlines() if "passed" in ln or "failed" in ln][-1]
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (passed|failed|skipped|errors?)", last)}
    return {"command": "pytest -q --ignore=tests/test_phase7_freeze.py", "summary": last.strip(), **counts,
            "exit_code": r.returncode}


def main() -> None:
    card = json.loads((MODEL_DIR / "model_card.json").read_text())
    ev_prov = json.loads(Path("data/processed/ml_eval/ml-v0/evaluation_provenance.json").read_text())
    for n, d in card["artifacts"].items():                       # the frozen model must be the evaluated one
        if sha256(MODEL_DIR / n) != d or ev_prov["model_card"][n] != d:
            raise SystemExit(f"{n}: model artifact does not match model card / evaluation provenance")
    tests = run_tests()
    if tests["exit_code"] != 0:
        raise SystemExit(f"test suite not green: {tests['summary']}")
    files = {str(p): sha256(p) for p in frozen_files()}
    man = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "FROZEN - Phases 1-6 evidence for SIH submission; do not modify listed files",
        "model": {"version": card["version"], "kind": "sklearn.ensemble.HistGradientBoostingClassifier + isotonic per lead bin",
                  "artifacts": card["artifacts"], "model_card_sha256": files[str(MODEL_DIR / "model_card.json")],
                  "n_iter": card["n_iter_selected"], "params": card["params_final"], "features": card["features"],
                  "train_days": card["train_days"], "validation_days": card["validation_days"],
                  "test_events": card["test_events_never_read"], "deterministic_threshold_p": 0.5,
                  "config_ml_dataset_sha256": card["config_sha256"],
                  "dataset_manifest_sha256": card["dataset_manifest_sha256"]},
        "evaluation": {"provenance_sha256": files["data/processed/ml_eval/ml-v0/evaluation_provenance.json"],
                       "outputs": ev_prov["outputs"]},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        **{p: version(p) for p in ("numpy", "scipy", "pandas", "xarray", "scikit-learn", "pysteps",
                                                   "tobac", "trackpy", "opencv-python-headless", "joblib")}},
        "tests": tests,
        "n_files": len(files), "files": files,
    }
    OUT.write_text(json.dumps(man, indent=2))
    print(f"frozen {len(files)} files; tests: {tests['summary']}; manifest {OUT} sha256 {sha256(OUT)}")


if __name__ == "__main__":
    main()
