"""Slide-2 storyboard panels, rendered from the FROZEN E8 replay bundle only (no new data, no invented fields).

  .venv/bin/python docs/ppt/make_slide2_storyboard.py      (from the repository root)

Anchor: storm cell #108, E8 14 May 2026, issue 14:00 UTC (frame 28, issue index 26).
Panels: today (observed IR) | 1 IR | 2 detect | 3 track | 4 forecast (pySTEPS +2 h) | 5 ML probability +2 h | 6 replay.
Colour scales match apps/web/src/colors.ts.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "apps/web/public/bundles/E8_20260514"
OUT = ROOT / "docs/ppt/assets"
FRAME, ISSUE, LEAD, CELL = 28, 26, 120, 108
BG = (237, 231, 220)
SCALE = 3
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

man = json.loads((B / "manifest.json").read_text())
g = man["grid"]; bb = g["bounds"]; W, H = g["width"], g["height"]
merc = lambda la: np.log(np.tan(np.pi / 4 + np.radians(la) / 2))


def px(lon, lat):
    return ((lon - bb["west"]) / (bb["east"] - bb["west"]) * W,
            (merc(bb["north"]) - merc(lat)) / (merc(bb["north"]) - merc(bb["south"])) * H)


IR = [(310, (120, 120, 120, 0)), (290, (150, 150, 150, 50)), (273, (205, 205, 205, 120)), (253, (70, 130, 200, 190)),
      (235, (40, 170, 90, 215)), (221, (240, 210, 40, 230)), (208, (215, 50, 40, 240)), (200, (190, 40, 190, 245))]
P_BINS = [0.1, 0.3, 0.5, 0.7, 0.9]
P_COL = [(218, 218, 235, 170), (188, 189, 220, 195), (158, 154, 200, 215), (117, 107, 177, 230), (84, 39, 143, 240)]


def ir_rgba(bt):
    out = np.zeros(bt.shape + (4,), float)
    for i in range(len(IR) - 1):
        (t1, c1), (t2, c2) = IR[i], IR[i + 1]
        m = (bt <= t1) & (bt > t2)
        f = ((t1 - bt[m]) / (t1 - t2))[:, None]
        out[m] = np.array(c1) + f * (np.array(c2) - np.array(c1))
    out[bt <= IR[-1][0]] = IR[-1][1]
    out[bt > IR[0][0]] = IR[0][1]
    return out


def tile(name):
    return np.array(Image.open(B / name))


def blend(rgba, alpha_scale=1.0):
    a = rgba[..., 3:4] / 255.0 * alpha_scale
    rgb = np.array(BG, float) * (1 - a) + rgba[..., :3] * a
    return rgb.astype(np.uint8)


def render_ir(code, faint=1.0):
    bt = code.astype(float) + 160.0
    rgba = ir_rgba(bt)
    rgba[code == 255] = (150, 150, 150, 70)
    return blend(rgba, faint)


def render_p(code):
    p = code.astype(float) / 250.0
    rgba = np.zeros(code.shape + (4,), float)
    for lo, col in zip(P_BINS, P_COL):
        rgba[(p >= lo) & (code != 255)] = col
    return blend(rgba)


def crop_up(rgb, box):
    x0, y0, x1, y1 = box
    im = Image.fromarray(rgb[y0:y1, x0:x1])
    return im.resize(((x1 - x0) * SCALE, (y1 - y0) * SCALE), Image.NEAREST)


def to_img(lonlat, box):
    x, y = px(*lonlat)
    return ((x - box[0]) * SCALE, (y - box[1]) * SCALE)


def cell_rings(frame, cell):
    fc = json.loads((B / f"cells/f{frame:02d}.geojson").read_text())
    f = [f for f in fc["features"] if f["properties"]["cell"] == cell]
    return [ring for poly in f[0]["geometry"]["coordinates"] for ring in poly] if f else []


def draw_rings(d, rings, box, color, width):
    for ring in rings:
        pts = [to_img(p, box) for p in ring]
        d.line(pts + [pts[0]], fill=color, width=width, joint="curve")


def label(d, xy, text, size=26, fill=(28, 36, 51), bg=(251, 248, 243)):
    f = ImageFont.truetype(FONT, size)
    x, y = xy
    l, t, r, b = d.textbbox((x, y), text, font=f)
    d.rounded_rectangle((l - 6, t - 4, r + 6, b + 4), radius=6, fill=bg)
    d.text((x, y), text, font=f, fill=fill)


def main():
    obs = tile(f"obs/f{FRAME:02d}.png")
    fcl = tile(f"fc/pysteps_i{ISSUE:02d}_l{LEAD:03d}.png")
    mlp = tile(f"fc/ml_i{ISSUE:02d}_l{LEAD:03d}.png")
    now = cell_rings(FRAME, CELL)
    track = [p for p in json.loads((B / "tracks.json").read_text())[str(CELL)] if p["frame"] <= FRAME]
    fc = json.loads((B / f"cellfc/i{ISSUE:02d}.json").read_text())[str(CELL)]["by_lead"]
    path = [(track[-1]["lon"], track[-1]["lat"])] + [(fc[str(L)]["field_advection"]["lon"], fc[str(L)]["field_advection"]["lat"])
                                                      for L in (30, 60, 120)]
    places = json.loads((B / "places.json").read_text())

    # ---- "today" panel: wider observed IR view with real report places
    today_box = (0, 0, 360, 180)
    im = crop_up(render_ir(obs), today_box); d = ImageDraw.Draw(im)
    for p in places:
        x, y = to_img((p["lon"], p["lat"]), today_box)
        if 40 <= x < im.width - 200 and 90 <= y < im.height - 60:        # skip markers clipped at the edges
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 255, 255), outline=(31, 42, 68), width=3)
            label(d, (x + 12, y - 14), p["name"], size=22)
    cx, cy = to_img((track[-1]["lon"], track[-1]["lat"]), today_box)       # centroid of cell #108 (frozen track)
    d.line((cx, cy, cx + 150, cy - 95), fill=(31, 42, 68), width=4)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(31, 42, 68))
    label(d, (cx + 150, cy - 125), "developing storm (cell #108)", size=26)
    label(d, (14, im.height - 44), "Observed IR · 14 May 2026 · 14:00 UTC", size=24)
    im.save(OUT / "story_today.png")

    box = (0, 0, 280, 200)  # common crop for the six stage panels (cell #108 and its +2 h path)
    # 1 satellite IR
    im = crop_up(render_ir(obs), box); im.save(OUT / "story_1_ir.png")
    # 2 detect: cell outline on the IR frame
    im = crop_up(render_ir(obs), box); d = ImageDraw.Draw(im)
    draw_rings(d, now, box, (31, 42, 68), 7); draw_rings(d, now, box, (233, 162, 59), 3)
    label(d, (14, 14), "cell #108", size=30)
    im.save(OUT / "story_2_detect.png")
    # 3 track: outlines 60 and 30 min earlier (thin) + now (thick), centroids joined
    im = crop_up(render_ir(obs, faint=0.55), box); d = ImageDraw.Draw(im)
    for fr, col, w in ((FRAME - 2, (150, 160, 175), 3), (FRAME - 1, (90, 105, 130), 3)):
        draw_rings(d, cell_rings(fr, CELL), box, col, w)
    draw_rings(d, now, box, (31, 42, 68), 7)
    label(d, (14, 14), "cell #108: −60 min · −30 min · now", size=26)
    im.save(OUT / "story_3_track.png")
    # 4 forecast: frozen pySTEPS BT at +2 h + frozen advected path of cell #108
    im = crop_up(render_ir(fcl), box); d = ImageDraw.Draw(im)
    draw_rings(d, now, box, (31, 42, 68), 3)
    ppts = [to_img(p, box) for p in path]
    d.line(ppts, fill=(178, 58, 46), width=6)
    for (x, y), t, dy in zip(ppts[1:], ("+30m", "+1h", "+2h"), (-52, 18, 18)):
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(251, 248, 243), outline=(178, 58, 46), width=5)
        label(d, (x - 24, y + dy), t, size=24, fill=(178, 58, 46))
    label(d, (14, 14), "pySTEPS +2 h", size=26)
    im.save(OUT / "story_4_forecast.png")
    # 5 ML probability at +2 h (frozen calibrated probability)
    im = crop_up(render_p(mlp), box); d = ImageDraw.Draw(im)
    draw_rings(d, now, box, (31, 42, 68), 3)
    x, y = ppts[3]
    d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(251, 248, 243), outline=(178, 58, 46), width=5)
    label(d, (14, 14), "P(cloud top < 235 K), +2 h", size=26)
    im.save(OUT / "story_5_prob.png")
    # 6 replay: crop of the real replay screenshot (three panes)
    rp = Image.open(ROOT / "apps/web/e2e-shots/verify/5_replay.png").crop((232, 48, 1440, 900))   # whole replay screen, 1.42:1
    rp.save(OUT / "story_6_replay.png")
    print("panels written to", OUT)


if __name__ == "__main__":
    main()
