"""Deterministic verification scores (VALIDATION_PLAN.md §2): contingency table and pooled FSS.

Only pixels valid in BOTH forecast and observation (and inside the domain) are scored; the excluded
fraction is reported by the caller. FSS follows Roberts & Lean (2008), with neighbourhood fractions from
``scipy.ndimage.uniform_filter(mode="constant", cval=0)``, the same convention as pySTEPS
``verification.spatialscores.fss`` (a test checks equality on NaN-free fields).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import uniform_filter


def contingency(fc_event: np.ndarray, obs_event: np.ndarray, valid: np.ndarray) -> dict[str, int]:
    f, o = fc_event[valid], obs_event[valid]
    return {"H": int(np.sum(f & o)), "M": int(np.sum(~f & o)), "F": int(np.sum(f & ~o)), "CN": int(np.sum(~f & ~o))}


def cat_scores(H: int, M: int, F: int, CN: int) -> dict[str, float]:
    nan = float("nan")
    return {
        "POD": H / (H + M) if H + M else nan,
        "FAR": F / (H + F) if H + F else nan,
        "CSI": H / (H + M + F) if H + M + F else nan,
        "bias": (H + F) / (H + M) if H + M else nan,
        "base_rate": (H + M) / (H + M + F + CN) if H + M + F + CN else nan,
    }


def fractions(event: np.ndarray, scale: int) -> np.ndarray:
    return uniform_filter(event.astype(np.float64), size=scale, mode="constant", cval=0.0)


@dataclass
class FSSAccumulator:
    """Pools FSS over many (forecast, observation) pairs: FSS = 1 - sum(MSE) / sum(MSE_ref)."""
    scale: int
    num: float = 0.0
    den: float = 0.0
    n_pairs: int = 0
    obs_events: float = 0.0
    n_valid: float = 0.0

    def add(self, fc_event: np.ndarray, obs_event: np.ndarray, valid: np.ndarray) -> None:
        # Invalid pixels contribute no events to the neighbourhood fractions and are not scored.
        pf = fractions(fc_event & valid, self.scale)[valid]
        po = fractions(obs_event & valid, self.scale)[valid]
        self.num += float(np.sum((pf - po) ** 2))
        self.den += float(np.sum(pf ** 2) + np.sum(po ** 2))
        self.obs_events += float(np.sum(obs_event[valid]))
        self.n_valid += float(valid.sum())
        self.n_pairs += 1

    def fss(self) -> float:
        return 1.0 - self.num / self.den if self.den > 0 else float("nan")

    def uniform_target(self) -> float:
        """Roberts & Lean 'useful' threshold 0.5 + f0/2, with f0 the observed base rate."""
        return 0.5 + (self.obs_events / self.n_valid) / 2.0 if self.n_valid else float("nan")
