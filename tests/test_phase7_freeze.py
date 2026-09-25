"""Phase-7 freeze guard: every file recorded in docs/FREEZE_ml-v0.json must still exist with the same SHA-256.
If this test fails, frozen evidence (code, config, data, model, figures or docs) was changed after the freeze."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

MAN = Path("docs/FREEZE_ml-v0.json")
needs = pytest.mark.skipif(not MAN.exists(), reason="evidence not frozen yet")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@needs
def test_all_frozen_files_unchanged():
    man = json.loads(MAN.read_text())
    changed = [p for p, d in man["files"].items() if not Path(p).exists() or _sha(Path(p)) != d]
    assert not changed, f"frozen files changed or missing: {changed[:10]}"


@needs
def test_frozen_model_is_the_evaluated_model():
    man = json.loads(MAN.read_text())
    card = json.loads(Path("data/models/ml-v0/model_card.json").read_text())
    prov = json.loads(Path("data/processed/ml_eval/ml-v0/evaluation_provenance.json").read_text())
    assert man["model"]["version"] == card["version"] == prov["model_version"] == "ml-v0"
    assert man["model"]["artifacts"] == card["artifacts"] == prov["model_card"]
    assert man["tests"]["exit_code"] == 0 and man["tests"].get("failed", 0) == 0
