"""Phase-3 overlap-based linking of cold segments (< segmentation threshold), with explicit merge/split events.

Why (docs/TRACKING_AUDIT.md §2): the Phase-1 nearest-feature linker produced direction reversals in 47 % of
step pairs, 21 % of cold-segment links had another segment overlapping the parent more than the linked child,
and merge_split_MEST families spanned up to 221 km. Linking by area overlap (TITAN-style) uses the objects'
shapes instead of jittery point positions.

Rule for frame t -> t+1 (online: uses frames t and t+1 and, for mode "flow", the pySTEPS motion at t, which is
estimated from frames <= t):
  * shift each parent segment (none, or by its mean flow), count overlap with every child segment;
  * an edge exists if overlap / min(area_parent, area_child) >= min_overlap_frac;
  * continuation = parent's largest-overlap child AND that child's largest-overlap parent -> child inherits the id;
  * other edges are genealogy events: a child with several parents = MERGE (non-continuing parents end);
    a parent with several children = SPLIT (non-continuing children start new ids with split_from);
  * children without a continuation start a new id.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ml.tracking.audit import _shift


@dataclass(frozen=True)
class LinkConfig:
    mode: str = "none"            # "none" | "flow"
    min_overlap_frac: float = 0.2


def _overlaps(par_mask: np.ndarray, child_labels: np.ndarray) -> dict[int, int]:
    lab = child_labels[par_mask]
    lab = lab[lab > 0]
    if lab.size == 0:
        return {}
    ids, counts = np.unique(lab, return_counts=True)
    return dict(zip(ids.tolist(), counts.tolist()))


def link_frames(mask_t: np.ndarray, mask_t1: np.ndarray, flow_t: np.ndarray | None, cfg: LinkConfig) -> list[dict]:
    """Candidate edges (parent_feature, child_feature, overlap_px, frac) between two labelled frames."""
    par_ids = [int(i) for i in np.unique(mask_t) if i > 0]
    child_area = dict(zip(*np.unique(mask_t1[mask_t1 > 0], return_counts=True))) if (mask_t1 > 0).any() else {}
    edges = []
    for p in par_ids:
        pm = mask_t == p
        if cfg.mode == "flow" and flow_t is not None:
            pm = _shift(pm, int(round(flow_t[1][mask_t == p].mean())), int(round(flow_t[0][mask_t == p].mean())))
        a_p = int((mask_t == p).sum())
        for c, n in _overlaps(pm, mask_t1).items():
            frac = n / min(a_p, int(child_area[c]))
            if frac >= cfg.min_overlap_frac:
                edges.append({"parent": p, "child": int(c), "overlap_px": int(n), "frac": float(frac)})
    return edges


def track(mask: np.ndarray, frames_features: dict[int, list[int]], vel: dict[int, np.ndarray], cfg: LinkConfig):
    """Link all frames. Returns (assign: DataFrame feature->cell per frame, events: DataFrame of MERGE/SPLIT)."""
    next_id = 1
    cell_of: dict[int, int] = {}          # feature id -> cell id
    assign, events = [], []
    frames = sorted(frames_features)
    for f0 in frames[:1]:
        for feat in frames_features[f0]:
            cell_of[feat] = next_id; assign.append({"frame": f0, "feature": feat, "cell": next_id}); next_id += 1
    for t, t1 in zip(frames[:-1], frames[1:]):
        children = frames_features[t1]
        if t1 != t + 1:
            edges = []
        else:
            edges = link_frames(mask[t], mask[t1], vel.get(t), cfg)
        by_par: dict[int, list[dict]] = {}
        by_chi: dict[int, list[dict]] = {}
        for e in edges:
            by_par.setdefault(e["parent"], []).append(e)
            by_chi.setdefault(e["child"], []).append(e)
        best_child = {p: max(es, key=lambda e: (e["overlap_px"], -e["child"]))["child"] for p, es in by_par.items()}
        best_par = {c: max(es, key=lambda e: (e["overlap_px"], -e["parent"]))["parent"] for c, es in by_chi.items()}
        for c in children:
            p = best_par.get(c)
            if p is not None and best_child.get(p) == c and p in cell_of:
                cid = cell_of[p]
            else:
                cid = next_id; next_id += 1
            cell_of[c] = cid
            assign.append({"frame": t1, "feature": c, "cell": cid})
        # Each non-continuation edge is classified once:
        #   MERGE  - the parent's best child is c, but c continues another parent -> parent's cell ends into c;
        #   SPLIT  - the child's best parent is p, but p continues into another child -> c starts from p;
        #   edges that are neither parent's nor child's best overlap are weak cross-overlaps and are ignored.
        for e in edges:
            p, c = e["parent"], e["child"]
            if p not in cell_of or cell_of[p] == cell_of[c]:
                continue
            if best_child[p] == c:
                events.append({"frame": t1, "type": "MERGE", "from_cell": cell_of[p], "into_cell": cell_of[c],
                               "overlap_frac": e["frac"]})
            elif best_par[c] == p:
                events.append({"frame": t1, "type": "SPLIT", "from_cell": cell_of[p], "into_cell": cell_of[c],
                               "overlap_frac": e["frac"]})
    return pd.DataFrame(assign), pd.DataFrame(events, columns=["frame", "type", "from_cell", "into_cell", "overlap_frac"])


def coldness_centroid(seg: np.ndarray, bt: np.ndarray, ref_K: float) -> tuple[float, float]:
    """Centroid weighted by (ref_K - BT) over the segment (row, col index). Falls back to the plain centroid."""
    ii, jj = np.nonzero(seg)
    w = np.clip(ref_K - bt[ii, jj], 0.0, None)
    w = np.where(np.isfinite(w), w, 0.0)
    if w.sum() <= 0:
        return float(ii.mean()), float(jj.mean())
    return float((ii * w).sum() / w.sum()), float((jj * w).sum() / w.sum())


def families(events: pd.DataFrame, cells: list[int]) -> dict[int, int]:
    """Connected components of the merge/split graph -> family id (smallest cell id in the component)."""
    parent = {c: c for c in cells}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for r in events.itertuples(index=False):
        a, b = find(int(r.from_cell)), find(int(r.into_cell))
        if a != b:
            parent[max(a, b)] = min(a, b)
    return {c: find(c) for c in cells}
