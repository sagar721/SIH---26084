"""Fill small, isolated missing-pixel gaps in the source field; leave larger gaps missing.

On 14 May 2026 the CPC merged-IR field over the domain had 2-7 % missing pixels per frame, mostly
isolated single pixels (median gap size 1 px). Gaps of <= MAX_GAP_PX connected native pixels
(<= ~64 km^2) are filled with the mean of their valid 8-neighbours (iterated until the gap is
closed); every filled pixel is flagged so downstream QC and figures can report it.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

MAX_GAP_PX = 4
_KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=float)


def fill_small_gaps(field: np.ndarray, max_gap_px: int = MAX_GAP_PX) -> tuple[np.ndarray, np.ndarray]:
    """Return (filled_field, filled_mask). Only connected NaN regions with <= max_gap_px pixels are filled."""
    missing = ~np.isfinite(field)
    if not missing.any():
        return field, np.zeros_like(missing)
    labels, n = ndimage.label(missing, structure=np.ones((3, 3)))
    sizes = ndimage.sum(missing, labels, index=np.arange(1, n + 1))
    small_ids = np.flatnonzero(sizes <= max_gap_px) + 1
    to_fill = np.isin(labels, small_ids)
    out = field.copy()
    remaining = to_fill.copy()
    for _ in range(max_gap_px):  # each pass closes gaps from their edges inward
        if not remaining.any():
            break
        valid = np.isfinite(out)
        s = ndimage.convolve(np.where(valid, out, 0.0), _KERNEL, mode="constant")
        c = ndimage.convolve(valid.astype(float), _KERNEL, mode="constant")
        can = remaining & (c > 0)
        out[can] = s[can] / c[can]
        remaining &= ~can
    return out, to_fill & np.isfinite(out)
