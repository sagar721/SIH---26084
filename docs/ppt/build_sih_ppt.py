"""Build the SIH26084 idea deck on the OFFICIAL SIH 2026 template (docs/ppt/SIH2026-IDEA-Presentation-Format.pptx).

Keeps the template's structure: 6 slides (title + 5 fixed sections), fixed section titles, the template's pointer
phrases as section labels, team-name oval, SIH logo, blue footer bar and page numbers. Deletes the instruction slide 7.
All numbers come from frozen project files (see docs/FINAL_SIH_PPT.md, number audit).

  python docs/ppt/build_sih_ppt.py        (needs python-pptx; run from the repository root)
"""
from __future__ import annotations

import copy
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "docs/ppt/SIH2026-IDEA-Presentation-Format.pptx"
OUT = ROOT / "docs/ppt/FINAL_SIH26084_PRESENTATION.pptx"
A = ROOT / "docs/ppt/assets"
TEAM = "THE FEVICONS"
TEAM_ID = "167858"
FOOTER = "SIH26084 - StormLife Nowcast"

NAVY = RGBColor(0x1F, 0x2A, 0x44); BLUE = RGBColor(0x00, 0x70, 0xC0); TEAL = RGBColor(0x13, 0x80, 0x86)
RED = RGBColor(0xB2, 0x3A, 0x2E); AMBER = RGBColor(0xC9, 0x82, 0x2B); GREEN = RGBColor(0x2F, 0x6B, 0x4F)
INK = RGBColor(0x1C, 0x24, 0x33); MUTED = RGBColor(0x55, 0x5E, 0x6B); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PANEL = RGBColor(0xF3, 0xF5, 0xF8); LINE = RGBColor(0xC9, 0xCE, 0xD8); PSTEPS = RGBColor(0x1F, 0x6F, 0xB2)
PINK = RGBColor(0xFB, 0xED, 0xEA); MINT = RGBColor(0xE6, 0xF3, 0xF3); SAND = RGBColor(0xFB, 0xF3, 0xE6)
FONT = "Arial"


# ---------------------------------------------------------------- helpers
def shape(sl, x, y, w, h, fill=None, line=None, lw=0.75, kind=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.07):
    s = sl.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(lw)
    s.shadow.inherit = False
    return s


def write(target, paras, size=10.5, color=INK, anchor=MSO_ANCHOR.TOP, margin=0.06, align=PP_ALIGN.LEFT):
    """paras: list of paragraphs; each paragraph is a str or a list of (text, {bold, color, size, italic}) runs."""
    tf = target.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(margin))
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.space_after = Pt(2)
        runs = [(p, {})] if isinstance(p, str) else p
        for text, st in runs:
            r = para.add_run()
            r.text = text
            f = r.font
            f.name = FONT
            f.size = Pt(st.get("size", size))
            f.bold = st.get("bold", False)
            f.italic = st.get("italic", False)
            f.color.rgb = st.get("color", color)
    return target


def textbox(sl, x, y, w, h, paras, **kw):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    return write(tb, paras, **kw)


def label(sl, x, y, w, text, color=TEAL, size=10.5):
    return textbox(sl, x, y, w, 0.3, [[("▸ " + text.upper(), {"bold": True, "color": color, "size": size})]], margin=0.02)


def card(sl, x, y, w, h, head, body, head_fill=NAVY, fill=PANEL, line=LINE, size=10, head_size=10.5):
    shape(sl, x, y, w, h, fill=fill, line=line)
    hb = shape(sl, x, y, w, 0.3, fill=head_fill, kind=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
    write(hb, [[(head, {"bold": True, "color": WHITE, "size": head_size})]], anchor=MSO_ANCHOR.MIDDLE, margin=0.07)
    textbox(sl, x + 0.04, y + 0.32, w - 0.08, h - 0.34, body, size=size)


def picture(sl, path, x, y, w=None, h=None, border=LINE):
    p = sl.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)
    p.line.color.rgb = border; p.line.width = Pt(0.75)
    return p


def bullet(text_runs, size=10.5, mark="•"):
    runs = [(text_runs, {})] if isinstance(text_runs, str) else text_runs
    return [(f"{mark} ", {"bold": True, "color": TEAL, "size": size})] + [(t, {**st, "size": st.get("size", size)}) for t, st in runs]


def remove(shape_obj):
    el = shape_obj._element
    el.getparent().remove(el)


def set_title(sl, text, size=None, x=None, w=None):
    t = sl.shapes.title
    tf = t.text_frame
    runs = [r for p in tf.paragraphs for r in p.runs]
    keep = next((r for r in runs if r.text.strip()), runs[0])
    for r in runs:
        r.text = ""
    keep.text = text
    if size:
        for r in runs:
            r.font.size = Pt(size)
    if x is not None:
        t.left = Inches(x)
    if w is not None:
        t.width = Inches(w)


def team_oval(sl):
    for sh in sl.shapes:
        if sh.name.startswith("Oval") and sh.has_text_frame:
            runs = [r for p in sh.text_frame.paragraphs for r in p.runs]
            runs[0].text = TEAM
            for r in runs[1:]:
                r.text = ""
            for r in runs:
                r.font.size = Pt(11)


def drop_template_pointer_box(sl):
    for sh in list(sl.shapes):
        if sh.name.startswith("TextBox 8"):
            remove(sh)


def notes(sl, text):
    sl.notes_slide.notes_text_frame.text = text


def delete_slide(prs, index):
    sld = prs.slides._sldIdLst[index]
    prs.part.drop_rel(sld.rId)
    prs.slides._sldIdLst.remove(sld)


# ---------------------------------------------------------------- build
prs = Presentation(str(TEMPLATE))
S = list(prs.slides)

# ---------- Slide 1: title page (mandatory fields) ----------
s1 = S[0]
for sh in s1.shapes:
    if sh.name == "Subtitle 3":
        runs = [r for p in sh.text_frame.paragraphs for r in p.runs]
        for r in runs:
            if r.text.strip() == "TITLE PAGE":
                r.text = "StormLife Nowcast"
    if sh.name == "TextBox 9":
        sh.top = Inches(1.95); sh.height = Inches(5.0)
        for para in sh.text_frame.paragraphs:
            para.space_before = Pt(0); para.space_after = Pt(2); para.line_spacing = 1.0
        values = {"Problem Statement ID –": " SIH26084",
                  "Problem Statement Title-": " Convective Scale Nowcasting for Thunderstorms, Hail & Cloudbursts (0–6 hr)",
                  "Theme-": " Disaster Management",
                  "PS Category- Software/Hardware": None,
                  "Team ID-": " " + TEAM_ID,
                  "Team Name (Registered on portal)": " – " + TEAM}
        for para in sh.text_frame.paragraphs:
            if not para.runs:
                continue
            key = "".join(r.text for r in para.runs).strip()
            if key == "PS Category- Software/Hardware":
                para.runs[0].text = "PS Category- "
                for r in para.runs[1:]:
                    r.text = ""
                val = " Software"
            elif key in values:
                val = values[key]
            else:
                continue
            if key == "Team Name (Registered on portal)":
                para.runs[0].text = "Team Name"      # drop "(Registered on portal)" from the label
            base = para.runs[0]
            r = para.add_run()
            r.text = val
            r.font.bold = False
            r.font.name = base.font.name or FONT
            r.font.size = Pt(16) if key.startswith("Problem Statement Title") else base.font.size
notes(s1, "StormLife Nowcast: satellite-first nowcasting of deep convection for SIH26084. Research prototype, validated on "
          "real, held-out storm days. Fill Team ID and registered Team Name before export.")


# ---------- Slide 2: IDEA TITLE / Proposed Solution (storyboard anchored on real storm cell #108, E8) ----------
s2 = S[1]
drop_template_pointer_box(s2)
set_title(s2, "IDEA TITLE", x=1.85, w=8.8)   # official section title kept; the idea title is the line below
team_oval(s2)
textbox(s2, 0.35, 1.1, 12.6, 0.36, [[("StormLife Nowcast: ", {"bold": True, "color": TEAL, "size": 12.5}),
        ("satellite → storm cell → a forecast you can check. Convective-scale nowcasting, 0–6 h: how far can it be trusted?", {"bold": True, "color": NAVY, "size": 12.5})]],
        align=PP_ALIGN.CENTER)
label(s2, 0.35, 1.5, 5.4, "How it addresses the problem")
label(s2, 5.95, 1.5, 7.05, "Detailed explanation of the proposed solution")
# LEFT: what we see today (real observed IR, 14 May 2026 14:00 UTC)
shape(s2, 0.35, 1.8, 4.3, 3.42, fill=PINK, line=RGBColor(0xE8, 0xC4, 0xBE))
hl = shape(s2, 0.35, 1.8, 4.3, 0.3, fill=RED, radius=0.25)
write(hl, [[("WHAT WE SEE TODAY", {"bold": True, "color": WHITE, "size": 10.5})]], anchor=MSO_ANCHOR.MIDDLE, margin=0.08)
picture(s2, A / "story_today.png", 0.43, 2.16, w=4.14)
for i, q in enumerate(["Where will it move?", "Will it intensify?", "How far can we trust the forecast?"]):
    x = 0.43 + i * 1.4
    c = shape(s2, x, 4.3, 1.33, 0.5, fill=WHITE, line=RED, lw=1.0)
    write(c, [[("? ", {"bold": True, "color": RED, "size": 11}), (q, {"bold": True, "color": INK, "size": 9.3})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.04)
textbox(s2, 0.43, 4.83, 4.14, 0.38, [[("Thunderstorms, hail and cloudbursts grow from deep convection within hours · no open, live radar or lightning feed in India",
        {"size": 9, "color": INK})]], align=PP_ALIGN.CENTER, margin=0.02)
# CENTER: 30 min -> 6 h
ar = shape(s2, 4.72, 2.55, 1.16, 0.95, fill=NAVY, kind=MSO_SHAPE.RIGHT_ARROW)
write(ar, [[("30 min", {"bold": True, "color": WHITE, "size": 11.5})], [("→ 6 h", {"bold": True, "color": WHITE, "size": 11.5})]],
      anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
textbox(s2, 4.62, 3.55, 1.36, 1.2, [[("2 km grid", {"bold": True, "color": NAVY, "size": 9.5})],
                                    [("target: deep", {"bold": True, "color": NAVY, "size": 9.5})],
                                    [("convection,", {"bold": True, "color": NAVY, "size": 9.5})],
                                    [("cloud top < 235 K", {"bold": True, "color": NAVY, "size": 9.5})]], align=PP_ALIGN.CENTER, margin=0.02)
# RIGHT: what StormLife adds -- one storm cell through the pipeline
shape(s2, 5.95, 1.8, 7.05, 3.42, fill=MINT, line=RGBColor(0xB9, 0xDC, 0xDC))
hr = shape(s2, 5.95, 1.8, 7.05, 0.3, fill=TEAL, radius=0.25)
write(hr, [[("WHAT STORMLIFE ADDS", {"bold": True, "color": WHITE, "size": 10.5}),
            ("   satellite nowcasting of one real storm cell (#108, 14 May 2026)", {"color": WHITE, "size": 9.5})]],
      anchor=MSO_ANCHOR.MIDDLE, margin=0.08)
stages = [("story_1_ir.png", "1 SATELLITE IR", "every 30 min"),
          ("story_2_detect.png", "2 DETECT", "cold cell < 245 K"),
          ("story_3_track.png", "3 TRACK", "same cell, by area overlap"),
          ("story_4_forecast.png", "4 FORECAST", "storm movement, 30 min – 6 h"),
          ("story_5_prob.png", "5 PROBABILITY + SKILL", "calibrated, validated"),
          ("story_6_replay.png", "6 REPLAY / DECIDE", "knew · predicted · happened")]
tw, gap = 1.04, 0.132
for i, (img, head, body) in enumerate(stages):
    x = 6.03 + i * (tw + gap)
    picture(s2, A / img, x, 2.18, w=tw, h=0.74)
    textbox(s2, x - 0.04, 2.95, tw + 0.08, 0.36, [[(head, {"bold": True, "color": TEAL if i < 5 else RED, "size": 9})]], margin=0.01)
    textbox(s2, x - 0.04, 3.32, tw + 0.08, 0.46, [[(body, {"size": 9, "color": INK})]], margin=0.01)
    if i < 5:
        shape(s2, x + tw + 0.012, 2.46, 0.11, 0.18, fill=NAVY, kind=MSO_SHAPE.RIGHT_ARROW)
bd = shape(s2, 6.03, 3.82, 2.4, 1.3, fill=NAVY, radius=0.1)
write(bd, [[("VALIDATED SKILL SHOWN BESIDE EVERY FORECAST", {"bold": True, "color": WHITE, "size": 10.5})],
           [("3 held-out storm days, pooled", {"color": WHITE, "size": 9})]], anchor=MSO_ANCHOR.MIDDLE, margin=0.1)
stats = [("BSS 0.27", "ML probability skill at +2 h (no-fit ref. 0.02)"),
         ("to ≈ 4 h", "best probability skill of the 4 methods tested"),
         ("1 h", "yes/no maps: no gain over pySTEPS beyond 1 h")]
for i, (big, small) in enumerate(stats):
    x = 8.51 + i * 1.5
    k = shape(s2, x, 3.82, 1.42, 1.3, fill=WHITE, line=TEAL, lw=1.0)
    write(k, [[(big, {"bold": True, "color": TEAL if i < 2 else RED, "size": 15})], [(small, {"size": 9, "color": INK})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.05)
# BOTTOM: innovation and uniqueness (template pointer)
label(s2, 0.35, 5.28, 12.6, "Innovation and uniqueness of the solution")
cards = [("Real storm days only", "No simulated radar, lightning or metrics; days fixed before scoring"),
         ("Baseline-first", "Every result vs persistence and pySTEPS; negative results reported"),
         ("Calibrated probability", "Reliability and validated skill shown with each forecast"),
         ("Audited and frozen", "Tracking audited before use; 386 evidence files hash-locked")]
for i, (head, body) in enumerate(cards):
    x = 0.35 + i * 3.19
    shape(s2, x, 5.57, 3.08, 0.82, fill=WHITE, line=TEAL, lw=1.0)
    num = shape(s2, x + 0.08, 5.7, 0.3, 0.3, fill=TEAL, kind=MSO_SHAPE.OVAL)
    write(num, [[(str(i + 1), {"bold": True, "color": WHITE, "size": 10})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0)
    textbox(s2, x + 0.44, 5.6, 2.6, 0.78, [[(head, {"bold": True, "color": NAVY, "size": 10})], [(body, {"size": 9.2})]], margin=0.03)
banner = shape(s2, 0.35, 6.47, 12.65, 0.4, fill=NAVY, radius=0.3)
write(banner, [[("RESEARCH PROTOTYPE", {"bold": True, "color": WHITE, "size": 10.5}),
                ("  ·  real satellite data, held-out storm days  ·  hazard-specific (hail, lightning, rain) skill not claimed  ·  not live  ·  not an official IMD warning",
                 {"color": WHITE, "size": 10})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
notes(s2, "Left: this is what a forecaster sees today, the real satellite IR image of 14 May 2026 at 14:00 UTC. It shows where "
          "the storm is, but not where it will go, whether it will grow, or how far to trust a forecast. Right: StormLife takes "
          "that same storm cell (#108) through the pipeline: detect it, track it, forecast it 30 min to 6 h ahead, give a "
          "calibrated probability of deep convection, and show the validated skill beside it. Every panel is rendered from "
          "our frozen replay data. The skill numbers come from 3 held-out storm days. As a yes/no map, ML is not better than "
          "pySTEPS beyond 1 h, and we say so. This is a replay prototype, not a live system.")

# ---------- Slide 3: TECHNICAL APPROACH (tech stack | how StormLife works | what it produces) ----------
s3 = S[2]
drop_template_pointer_box(s3)
team_oval(s3)
DATA_C, TRACK_C, FC_C, VAL_C, PROD_C = NAVY, TEAL, PSTEPS, GREEN, RED
# column headers (template pointers kept)
label(s3, 0.35, 1.2, 3.0, "Technologies & tools")
label(s3, 3.6, 1.2, 5.4, "Methodology and process: how StormLife works")
label(s3, 9.45, 1.2, 3.55, "Working prototype: what it produces")

# LEFT: capability-based technology grid (2 x 2), same visual language as the methodology cards
tech = [("1", "DATA &|SCIENCE", DATA_C, ["Python", "NumPy", "pandas", "xarray", "SciPy"],
         "Satellite processing & numerical analysis"),
        ("2", "STORM|INTELLIGENCE", TRACK_C, ["OpenCV", "scikit-image", "custom overlap tracking", "optical flow"],
         "Detect, track & characterize storm cells"),
        ("3", "FORECAST &|VALIDATION", FC_C, ["pySTEPS", "scikit-learn", "isotonic calibration", "pytest"],
         "Forecast, calibrate & verify"),
        ("4", "PRODUCT", PROD_C, ["React", "TypeScript", "Vite", "MapLibre GL"],
         "Interactive replay & decision-support dashboard")]
TGX, TGY, TGW, TGH, TGG = 0.35, 1.52, 3.0, 4.62, 0.1
tbw, tbh = (TGW - TGG) / 2, (TGH - TGG) / 2
for i, (num, cat, col, names, purpose) in enumerate(tech):
    r_, c_ = divmod(i, 2)
    x, y = TGX + c_ * (tbw + TGG), TGY + r_ * (tbh + TGG)
    shape(s3, x, y, tbw, tbh, fill=WHITE, line=col, lw=1.25, radius=0.08)
    circ = shape(s3, x + 0.08, y + 0.12, 0.3, 0.3, fill=col, kind=MSO_SHAPE.OVAL)
    write(circ, [[(num, {"bold": True, "color": WHITE, "size": 10.5})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0)
    textbox(s3, x + 0.42, y + 0.06, tbw - 0.46, 0.44, [[(ln, {"bold": True, "color": col, "size": 9})] for ln in cat.split("|")],
            anchor=MSO_ANCHOR.MIDDLE, margin=0.01)
    textbox(s3, x + 0.1, y + 0.56, tbw - 0.2, tbh - 1.2, [[(n, {"bold": True, "color": INK, "size": 10})] for n in names],
            anchor=MSO_ANCHOR.TOP, margin=0.01)
    pb = shape(s3, x + 0.06, y + tbh - 0.62, tbw - 0.12, 0.56, fill=PANEL, radius=0.15)
    write(pb, [[(purpose, {"italic": True, "color": INK, "size": 8.8})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.03)
# connector: stack powers the process
shape(s3, 3.38, 3.72, 0.19, 0.24, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW)

# CENTER: how StormLife works (largest element)
stages = [("1", "REAL SATELLITE DATA", DATA_C, "What goes in: pictures of cloud-top temperature",
           "NOAA/NCEP/CPC merged IR · 4 km · 30-minute frames · 3 held-out storm days"),
          ("2", "QC + PREPROCESSING", DATA_C, "Clean every frame and put it on one map",
           "Decode · quality control · cloud-top temperature (BT) · 2 km grid"),
          ("3", "STORM INTELLIGENCE", TRACK_C, "Find the storms and follow them",
           "Cold cells < 245 K (deep convection) · area-overlap tracking · optical-flow motion")]
cy = 1.55
CX, CW = 3.6, 5.4
def stage_card(num, title, col, human, tech, y, h):
    circ = shape(s3, CX, y + 0.11, 0.42, 0.42, fill=col, kind=MSO_SHAPE.OVAL)
    write(circ, [[(num, {"bold": True, "color": WHITE, "size": 13})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0)
    shape(s3, CX + 0.52, y, CW - 0.52, h, fill=WHITE, line=col, lw=1.25, radius=0.14)
    return textbox(s3, CX + 0.6, y + 0.02, CW - 0.66, h - 0.04,
                   [[(title, {"bold": True, "color": col, "size": 11}), ("   " + human, {"italic": True, "color": INK, "size": 9.6})],
                    [(tech, {"size": 9.3, "color": MUTED})]] if tech else
                   [[(title, {"bold": True, "color": col, "size": 11}), ("   " + human, {"italic": True, "color": INK, "size": 9.6})]],
                   anchor=MSO_ANCHOR.MIDDLE if tech else MSO_ANCHOR.TOP, margin=0.03)
def down(y):
    shape(s3, CX + 0.1, y, 0.22, 0.13, fill=NAVY, kind=MSO_SHAPE.DOWN_ARROW)
SH, AG = 0.64, 0.15
for num, title, col, human, tech in stages:
    stage_card(num, title, col, human, tech, cy, SH)
    down(cy + SH + 0.01)
    cy += SH + AG
# stage 4: forecast engine with three branches
F_H = 1.28
stage_card("4", "FORECAST ENGINE", FC_C, "Estimate what happens next, 30 min – 6 h", None, cy, F_H)
branches = [("Persistence", "baseline: assume no change"),
            ("pySTEPS advection", "move storms along their motion"),
            ("ML probability", "how likely is deep convection? (calibrated)")]
bx0, bw = CX + 0.62, (CW - 0.52 - 0.2 - 2 * 0.1) / 3
for j, (bn, bh) in enumerate(branches):
    bx = bx0 + j * (bw + 0.1)
    shape(s3, bx + bw / 2 - 0.08, cy + 0.33, 0.16, 0.12, fill=FC_C, kind=MSO_SHAPE.DOWN_ARROW)
    b = shape(s3, bx, cy + 0.48, bw, 0.7, fill=RGBColor(0xE8, 0xF1, 0xF9), line=FC_C, lw=1.0, radius=0.18)
    write(b, [[(bn, {"bold": True, "color": FC_C, "size": 10})], [(bh, {"size": 9, "color": INK})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.04)
down(cy + F_H + 0.01)
cy += F_H + AG
stage_card("5", "VALIDATION", VAL_C, "Did the forecast actually work?",
           "CSI · FSS · Brier skill · reliability · held-out storm days · same pixels · replay", cy, SH)
# connector: process feeds the product
shape(s3, 9.07, 3.72, 0.3, 0.24, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW)

# RIGHT: what it produces (real thumbnails from the frozen E8 bundle)
outs = [("story_2_detect.png", "STORM CELL", TRACK_C, "cell #108, 14 May 2026"),
        ("story_3_track.png", "TRACK + MOTION", TRACK_C, "where it has been and is heading"),
        ("story_4_forecast.png", "30 MIN – 6 H FORECAST", FC_C, "where it may be next"),
        ("story_5_prob.png", "CALIBRATED PROBABILITY", FC_C, "how likely is deep convection?"),
        ("thumb_skill.png", "VALIDATED SKILL", VAL_C, "how far to trust it"),
        ("story_6_replay.png", "STORMLIFE DASHBOARD", PROD_C, "9-screen replay prototype")]
ry, TH, TW, RG = 1.55, 0.44, 0.62, 0.09
for i, (img, head, col, human) in enumerate(outs):
    picture(s3, A / img, 9.45, ry, w=TW, h=TH, border=col)
    textbox(s3, 10.13, ry - 0.01, 2.87, TH + 0.02, [[(head, {"bold": True, "color": col, "size": 9.8})],
                                                    [(human, {"italic": True, "color": INK, "size": 9.2})]],
            anchor=MSO_ANCHOR.MIDDLE, margin=0.02)
    if i < len(outs) - 1:
        shape(s3, 9.45 + TW / 2 - 0.07, ry + TH + 0.005, 0.14, RG - 0.01, fill=NAVY, kind=MSO_SHAPE.DOWN_ARROW)
    ry += TH + RG
pl = shape(s3, 9.45, ry + 0.04, 3.55, 0.28, fill=PROD_C, radius=0.4)
write(pl, [[("STORMLIFE RESEARCH PROTOTYPE · replay, not live", {"bold": True, "color": WHITE, "size": 9})]],
      anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
cards = ["Replay situation map", "0–6 h forecast", "Historical replay", "Model performance", "Data health", "Exercise alert (CAP)"]
cwid, chh = (3.55 - 0.08) / 2, 0.27
for k, c_ in enumerate(cards):
    r_, col_ = divmod(k, 2)
    cb = shape(s3, 9.45 + col_ * (cwid + 0.08), ry + 0.38 + r_ * (chh + 0.05), cwid, chh, fill=PINK, line=PROD_C, lw=0.75, radius=0.3)
    write(cb, [[(c_, {"bold": True, "color": INK, "size": 8.8})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.01)

# bottom strip: one takeaway
bt = shape(s3, 0.35, 6.3, 12.65, 0.46, fill=NAVY, radius=0.3)
write(bt, [[("Real satellite data  →  audited storm intelligence  →  forecast + calibrated probability  →  validated decision support",
             {"bold": True, "color": WHITE, "size": 12})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.04)
notes(s3, "Left: the tools, grouped by the stage they power. Centre: how StormLife works. Real satellite frames come in, are "
          "cleaned and put on one 2 km grid; cold cloud cells (deep convection) are found and followed; three methods estimate "
          "the next 30 minutes to 6 hours; and every method is scored on held-out storm days. Right: what it produces, shown "
          "with real images from 14 May 2026, ending in the 9-screen replay prototype. It is a research prototype running on "
          "replayed data, not a live system.")

# ---------- Slide 4: FEASIBILITY AND VIABILITY (built → measured → verified → clear limits → next validation) ----------
s4 = S[3]
drop_template_pointer_box(s4)
team_oval(s4)
story = [("BUILT", NAVY), ("MEASURED", PSTEPS), ("VERIFIED", TEAL), ("CLEAR LIMITS", RED), ("NEXT VALIDATION", GREEN)]
sw4 = [1.0, 1.35, 1.25, 1.55, 1.95]
x = 0.35 + (12.65 - (sum(sw4) + 0.34 * 4)) / 2
for i, ((word, col), w_) in enumerate(zip(story, sw4)):
    b = shape(s4, x, 1.1, w_, 0.3, fill=col, radius=0.4)
    write(b, [[(word, {"bold": True, "color": WHITE, "size": 10})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.01)
    if i < 4:
        shape(s4, x + w_ + 0.08, 1.18, 0.18, 0.14, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW)
    x += w_ + 0.34
# ZONE 1 — evidence at a glance
label(s4, 0.35, 1.5, 12.6, "Analysis of the feasibility of the idea: evidence at a glance")
kp = [("25 days", "600 real satellite files"), ("3 storm days", "held out: E8 · E10 · E11"), ("9 screens", "working replay prototype"),
      ("84 tests pass", "incl. 2 browser tests"), ("386 files", "evidence hash-frozen")]
kw = (12.65 - 4 * 0.15) / 5
for i, (big, small) in enumerate(kp):
    k = shape(s4, 0.35 + i * (kw + 0.15), 1.78, kw, 0.54, fill=MINT, line=RGBColor(0xB9, 0xDC, 0xDC), radius=0.2)
    write(k, [[(big, {"bold": True, "color": TEAL, "size": 12.5})], [(small, {"size": 8.8, "color": INK})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
# ZONE 2 — what the testing showed
label(s4, 0.35, 2.44, 12.6, "What the testing showed: 3 held-out storm days, pooled, same pixels")
CHW, CHH = 4.75, 4.75 / (1364 / 726)
picture(s4, A / "bss_by_lead.png", 0.35, 2.72, w=CHW, h=CHH, border=LINE)
ev = [("3 / 3", TEAL, "pySTEPS beats persistence", "at every tested lead, 30 min – 6 h"),
      ("≈ 2 h", TEAL, "Useful baseline skill", "FSS 40 km useful to ~90 min (persistence) / ~120 min (pySTEPS)"),
      ("≈ 4 h", TEAL, "ML probability skill", "BSS 0.27 at 2 h (no-fit ref. 0.02) · calibration error 0.002–0.004"),
      ("1 h", RED, "LIMIT: no yes/no gain", "ML does not improve binary yes/no maps over pySTEPS beyond 1 h")]
EX, EW = 0.35 + CHW + 0.2, 12.65 - CHW - 0.2
cw4, ch4 = (EW - 0.15) / 2, (CHH - 0.15) / 2
for i, (big, col, head, sub) in enumerate(ev):
    r_, c_ = divmod(i, 2)
    x, y = EX + c_ * (cw4 + 0.15), 2.72 + r_ * (ch4 + 0.15)
    lim_ = col == RED
    shape(s4, x, y, cw4, ch4, fill=PINK if lim_ else WHITE, line=col, lw=2.0 if lim_ else 1.25, radius=0.08)
    nb = shape(s4, x + 0.1, y + 0.12, 1.02, ch4 - 0.24, fill=col, radius=0.14)
    write(nb, [[(big, {"bold": True, "color": WHITE, "size": 20})]] + ([[("LIMIT", {"bold": True, "color": WHITE, "size": 9})]] if lim_ else []),
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
    textbox(s4, x + 1.22, y + 0.08, cw4 - 1.3, ch4 - 0.16, [[(head, {"bold": True, "color": RED if lim_ else INK, "size": 11})],
                                                           [(sub, {"size": 9.5, "color": INK if lim_ else MUTED})]],
            anchor=MSO_ANCHOR.MIDDLE, margin=0.02)
# ZONE 3 — viability roadmap
ZY = 2.72 + CHH + 0.14
label(s4, 0.35, ZY, 12.6, "Potential challenges and risks → Strategies for overcoming these challenges: viability roadmap")
road = [("BUILT NOW", NAVY, ["Research prototype · real satellite data", "3 held-out storm days · IR-only replay"]),
        ("NEXT  (not built)", TEAL, ["More seasons + regions", "Forward-time validation", "Independent radar / lightning verification"]),
        ("FUTURE  (not built)", PSTEPS, ["INSAT-3DS / Meteosat, 15-min+", "Radar / lightning truth", "Live pipeline + initiation score"])]
RY, RH, RG = ZY + 0.28, 0.84, 0.38
rw = (12.65 - 2 * RG) / 3
for i, (tag, col, lines) in enumerate(road):
    x = 0.35 + i * (rw + RG)
    shape(s4, x, RY, rw, RH, fill=MINT if i == 0 else WHITE, line=col, lw=1.25, radius=0.1)
    tg = shape(s4, x, RY, rw, 0.27, fill=col, radius=0.35)
    write(tg, [[(tag, {"bold": True, "color": WHITE, "size": 9.5})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.01)
    textbox(s4, x + 0.1, RY + 0.29, rw - 0.2, RH - 0.31, [[(ln, {"size": 9.5, "color": INK, "bold": i == 0})] for ln in lines],
            anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.01)
    if i < 2:
        shape(s4, x + rw + 0.07, RY + RH / 2 - 0.12, RG - 0.14, 0.24, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW)
textbox(s4, 0.35, RY + RH + 0.04, 12.65, 0.26,
        [[("Limits today: ", {"bold": True, "color": RED, "size": 9}),
          ("3 held-out days (May 2026, NW India) · ML tested backward in time · single IR, 30-min · parallax not verified · "
           "no radar/lightning truth · replay, not live", {"size": 9, "color": INK})]], align=PP_ALIGN.CENTER, margin=0.01)
notes(s4, "Built, measured, verified, clear limits, next validation. Top: what exists today. Centre: the frozen Brier skill chart "
          "from three held-out storm days and four findings; the red card is the limit we state openly: ML does not improve "
          "yes/no maps over pySTEPS beyond 1 hour. Bottom: only the first stage is built; next and future stages are not "
          "built. Limits: 3 held-out days in May 2026 over NW India, ML tested backward in time, single IR channel at 30 "
          "minutes, parallax not verified, no radar or lightning truth, replay not live.")

# ---------- Slide 5: IMPACT AND BENEFITS (one storm signal → three decision users) ----------
s5 = S[4]
drop_template_pointer_box(s5)
team_oval(s5)
textbox(s5, 0.35, 1.06, 12.6, 0.34, [[("One storm signal  →  three decision users", {"bold": True, "color": NAVY, "size": 13})]],
        align=PP_ALIGN.CENTER)
label(s5, 0.35, 1.45, 3.8, "Potential impact on the target audience")
hub = shape(s5, 4.45, 1.41, 4.45, 0.38, fill=NAVY, radius=0.4)
write(hub, [[("STORMLIFE:  storm • forecast • skill • replay", {"bold": True, "color": WHITE, "size": 11.5})]],
      anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
users = [("FORECASTER", "IMD / NCMRWF", NAVY, "icon_forecaster.png", "persona_forecaster.png",
          "Where is convection developing?", "Storm location + motion + forecast skill",
          "Compare forecast methods and focus attention", None),
         ("DISTRICT DISASTER OFFICIAL", "district level", RED, "icon_official.png", "persona_official.png",
          "Where should attention be focused?", "Probability + forecast track + replay",
          "Prioritize areas for exercise / advisory review", "EXERCISE / NOT OPERATIONAL"),
         ("RESEARCHER / EVALUATOR", "research", TEAL, "icon_researcher.png", "persona_researcher.png",
          "Did the system predict what happened?", "Replay + held-out events + baseline comparison",
          "Evaluate model skill, limitations and reproducibility", None)]
CW5, GAP5, CY, CH = (12.65 - 2 * 0.2) / 3, 0.2, 2.02, 3.16
for i, (who, sub, col, icon, shot, q, sees, dec, badge) in enumerate(users):
    x = 0.35 + i * (CW5 + GAP5)
    # arrow from the StormLife bar to each user
    shape(s5, x + CW5 / 2 - 0.14, 1.8, 0.28, 0.2, fill=col, kind=MSO_SHAPE.DOWN_ARROW)
    shape(s5, x, CY, CW5, CH, fill=WHITE, line=col, lw=1.5, radius=0.06)
    hd = shape(s5, x, CY, CW5, 0.72, fill=col, radius=0.12)
    ic = shape(s5, x + 0.1, CY + 0.08, 0.56, 0.56, fill=RGBColor(0xFF, 0xFF, 0xFF), kind=MSO_SHAPE.OVAL)
    ic.fill.solid(); ic.fill.fore_color.rgb = col; ic.line.color.rgb = WHITE; ic.line.width = Pt(1.5)
    s5.shapes.add_picture(str(A / icon), Inches(x + 0.17), Inches(CY + 0.15), Inches(0.42), Inches(0.42))
    textbox(s5, x + 0.74, CY + 0.06, CW5 - 0.8, 0.6, [[(who, {"bold": True, "color": WHITE, "size": 11.5})],
                                                      [(sub, {"color": WHITE, "size": 9})]], anchor=MSO_ANCHOR.MIDDLE, margin=0.02)
    textbox(s5, x + 0.1, CY + 0.78, CW5 - 0.2, 0.38, [[("“" + q + "”", {"bold": True, "italic": True, "color": col, "size": 12})]],
            anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.01)
    from PIL import Image as _Im
    pw_, ph_ = CW5 - 0.2, 1.08
    r0 = _Im.open(A / shot).size[0] / _Im.open(A / shot).size[1]
    pic = s5.shapes.add_picture(str(A / shot), Inches(x + 0.1), Inches(CY + 1.2), Inches(pw_))
    pic.crop_bottom = 1 - r0 / (pw_ / ph_); pic.height = Inches(ph_)
    pic.line.color.rgb = LINE; pic.line.width = Pt(0.75)
    ly = CY + 1.24 + ph_
    for tag, txt in (("SEES", sees), ("DECISION", dec)):
        rh_ = 0.3 if tag == "SEES" else 0.46
        tg = shape(s5, x + 0.1, ly + (rh_ - 0.24) / 2, 0.82, 0.24, fill=col, radius=0.4)
        write(tg, [[(tag, {"bold": True, "color": WHITE, "size": 8.8})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0)
        textbox(s5, x + 0.98, ly, CW5 - 1.06, rh_, [[(txt, {"bold": tag == "DECISION", "color": INK, "size": 9.8})]],
                anchor=MSO_ANCHOR.MIDDLE, margin=0.01)
        ly += rh_ + 0.03
    if badge:
        bg = shape(s5, x + CW5 - 2.12, CY + 0.42, 2.04, 0.24, fill=AMBER, radius=0.4)
        write(bg, [[(badge, {"bold": True, "color": WHITE, "size": 8.8})]], anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0)
label(s5, 0.35, 5.27, 12.6, "Benefits of the solution (social, economic, environmental, etc.)")
ben = [("SOCIAL", RED, "Potential earlier awareness of deep convection"),
       ("ECONOMIC", AMBER, "Open-data + open-source prototype"),
       ("ENVIRONMENTAL", GREEN, "Satellite-first; no new sensing hardware"),
       ("TRUST", NAVY, "Traceable metrics + visible limitations")]
bw5 = (12.65 - 3 * 0.15) / 4
for i, (head, col, body) in enumerate(ben):
    x = 0.35 + i * (bw5 + 0.15)
    pill = shape(s5, x, 5.58, bw5, 0.64, fill=WHITE, line=col, lw=1.5, radius=0.45)
    write(pill, [[(head, {"bold": True, "color": col, "size": 10})], [(body, {"size": 9.6, "color": INK})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.04)
textbox(s5, 0.35, 6.36, 12.65, 0.3, [[("Research prototype • replay of real satellite data • not operational • exercise alerts only",
        {"size": 9.5, "color": MUTED, "italic": True})]], align=PP_ALIGN.CENTER, margin=0.01)
notes(s5, "One storm signal, three decision users. StormLife provides the storm, the forecast, its validated skill and the replay. "
          "The forecaster uses it to see where convection is developing and compare forecast methods. The district official "
          "uses the probability and track to prioritise areas for review; advisories are exercise drafts only and nothing is "
          "operational. The researcher replays held-out storm days to check whether the system predicted what happened, "
          "against the same baselines. Each screenshot is the real prototype screen. No live alerts, deployment or savings "
          "are claimed.")

# ---------- Slide 6: RESEARCH AND REFERENCES (research gap → question → contribution → evidence → official sources) ----------
s6 = S[5]
drop_template_pointer_box(s6)
team_oval(s6)
URL_IMD = "https://mausam.imd.gov.in/newdelhi/mcdata/hailstorm_report.pdf"
URL_CPC = "https://www.cpc.ncep.noaa.gov/products/global_precip/html/wpage.merged_IR.shtml"
URL_CPC_FULL = "https://www.cpc.ncep.noaa.gov/products/global_precip/html/wpage.full_res.shtml"
URL_CPC_DATA = "https://ftp.cpc.ncep.noaa.gov/precip/global_full_res_IR/"


def linked(tb, text, url, size=8.8, bold=False, color=PSTEPS):
    """Append a clickable run to the last paragraph of a text box."""
    para = tb.text_frame.paragraphs[-1]
    r = para.add_run(); r.text = text
    r.font.name = FONT; r.font.size = Pt(size); r.font.bold = bold; r.font.underline = True; r.font.color.rgb = color
    r.hyperlink.address = url


def rarrow(sl, x, y):
    shape(sl, x, y, 0.2, 0.28, fill=MUTED, kind=MSO_SHAPE.RIGHT_ARROW)


def darr(sl, x, y):
    shape(sl, x - 0.12, y, 0.24, 0.14, fill=NAVY, kind=MSO_SHAPE.DOWN_ARROW)


textbox(s6, 0.35, 1.08, 12.6, 0.34, [[("Research question  →  StormLife contribution  →  verified prototype  →  data sources  →  methods & reproducibility",
        {"bold": True, "color": NAVY, "size": 12.5})]], align=PP_ALIGN.CENTER)
# LEFT: existing approaches -> data/access constraint
LX, LW = 0.35, 3.95
label(s6, LX, 1.45, LW, "Existing approaches")
appro = [("RADAR", "cell tracking, e.g. MeteoSwiss TRT; IMD radar nowcasts"), ("LIGHTNING", "flash data in severe-storm guidance"),
         ("NWP", "model environment, e.g. in NOAA ProbSevere v3"), ("SATELLITE PRODUCTS", "storm objects + phases, e.g. NWCSAF RDT")]
aw = (LW - 0.1) / 2
for i, (n, d) in enumerate(appro):
    r_, c_ = divmod(i, 2)
    b = shape(s6, LX + c_ * (aw + 0.1), 1.74 + r_ * 0.7, aw, 0.62, fill=PANEL, line=LINE)
    write(b, [[(n, {"bold": True, "color": NAVY, "size": 10})], [(d, {"size": 8.8, "color": INK})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.04)
textbox(s6, LX, 3.13, LW, 0.38, [[("Operational and research systems already provide storm detection, tracking and severe-weather guidance.",
        {"italic": True, "size": 9, "color": MUTED})]], margin=0.02)
darr(s6, LX + LW / 2, 3.52)
cst = shape(s6, LX, 3.7, LW, 1.58, fill=PINK, line=RED, lw=1.0)
write(cst, [[("DATA / ACCESS CONSTRAINT", {"bold": True, "color": RED, "size": 10})],
            [("Indian open-data access and latency constrain reproducible, independent validation.", {"bold": True, "size": 9.5, "color": INK})],
            bullet("IMD radar raw data: licence or research request", size=8.8),
            bullet("INSAT via MOSDAC: general users get data after ~3 days", size=8.8),
            bullet("Lightning networks: restricted research access", size=8.8),
            bullet("IMD AWS/ARG portal: closed to the public (May 2025)", size=8.8)], margin=0.08)
rarrow(s6, 4.33, 3.2)
# CENTER: the research question (visual centre) -> StormLife contribution
CX, CW = 4.58, 4.15
label(s6, CX, 1.45, CW, "Our research question")
q = shape(s6, CX, 1.74, CW, 1.28, fill=NAVY, radius=0.1)
write(q, [[("WHAT CAN ACTUALLY BE VERIFIED FROM OPEN GEOSTATIONARY IR ALONE?", {"bold": True, "color": WHITE, "size": 17})]],
      anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.12)
darr(s6, CX + CW / 2, 3.05)
textbox(s6, CX, 3.2, CW, 0.26, [[("STORMLIFE CONTRIBUTION", {"bold": True, "color": TEAL, "size": 10})]], margin=0.02)
contrib = [("SATELLITE-FIRST", "open geostationary IR only"), ("BASELINE-FIRST", "vs persistence + pySTEPS"),
           ("CALIBRATED PROBABILITY", "reliability shown"), ("AUDITED TRACKING", "ID switches 21 % → 0.4 %"),
           ("REAL-EVENT REPLAY", "knew · predicted · happened"), ("TRACEABLE EVIDENCE", "every number → hashed file")]
kw6 = (CW - 0.08) / 2
for i, (n, d) in enumerate(contrib):
    r_, c_ = divmod(i, 2)
    b = shape(s6, CX + c_ * (kw6 + 0.08), 3.48 + r_ * 0.5, kw6, 0.44, fill=MINT, line=TEAL, lw=1.0, radius=0.2)
    write(b, [[(n, {"bold": True, "color": TEAL, "size": 9.3})], [(d, {"size": 8.8, "color": INK})]],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
lim = shape(s6, CX, 4.98, CW, 0.3, fill=WHITE, line=RED, lw=1.0, radius=0.3)
write(lim, [[("+ EXPLICIT LIMITATIONS  ", {"bold": True, "color": RED, "size": 8.6}),
             ("3 days · single IR · no radar/lightning truth", {"size": 8.6, "color": INK})]],
      anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
rarrow(s6, 8.76, 3.2)
# RIGHT: verified prototype (real screenshot)
RX, RW = 9.0, 4.0
label(s6, RX, 1.45, RW, "Verified prototype")
picture(s6, A / "evidence_performance.png", RX, 1.74, w=RW, h=RW / (1208 / 632), border=TEAL)
ey = 1.74 + RW / (1208 / 632)
textbox(s6, RX, ey + 0.03, RW, 0.4, [[("3 held-out storm days • reproducible replay • validated metrics • evidence frozen",
        {"bold": True, "size": 8.8, "color": INK})]], align=PP_ALIGN.CENTER, margin=0.01)
cp = shape(s6, RX, ey + 0.47, RW, 0.62, fill=TEAL, radius=0.12)
write(cp, [[("StormLife complements existing operational systems; it does not replace them.", {"bold": True, "color": WHITE, "size": 10})],
           [("Research prototype · real-event replay · held-out validation", {"color": WHITE, "size": 9})]],
      anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.05)
# BOTTOM: DATA SOURCES (left) | METHODS & REPRODUCIBILITY (right), visually separated
URL_PYSTEPS = "https://github.com/pySTEPS/pysteps"
DSW, MPW = 8.85, 3.6
label(s6, 0.35, 5.34, DSW, "Details / links of the reference and research work: data sources used")
label(s6, 0.35 + DSW + 0.2, 5.34, MPW, "Methods & reproducibility")
def source_badge(x, w, tag, tag_sub, col, name, used, links, qr):
    shape(s6, x, 5.62, w, 1.24, fill=WHITE, line=col, lw=1.25)
    t_ = shape(s6, x + 0.07, 5.72, 0.72, 1.04, fill=col, radius=0.12)
    write(t_, [[(tag, {"bold": True, "color": WHITE, "size": 11.5})]] + [[(ln, {"color": WHITE, "size": 8.5})] for ln in tag_sub.split("|")],
          anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.02)
    tb = textbox(s6, x + 0.84, 5.64, w - 0.84 - 0.88, 1.2, [[(name, {"bold": True, "color": INK, "size": 9.2})],
                                                           [("Used for: ", {"bold": True, "color": col, "size": 8.6}), (used, {"size": 8.6, "color": INK})],
                                                           [("", {"size": 8.6})]], margin=0.02)
    for k, (txt, url) in enumerate(links):
        if k:
            para = tb.text_frame.paragraphs[-1]; r = para.add_run(); r.text = " · "; r.font.size = Pt(8.6); r.font.name = FONT
        linked(tb, txt, url, size=8.6)
    picture(s6, A / qr, x + w - 0.86, 5.8, w=0.8, h=0.8, border=WHITE)
bw_ = (DSW - 0.12) / 2
source_badge(0.35, bw_, "IMD", "Govt.|of India", RGBColor(0x2E, 0x4A, 0x7A),
             "India Meteorological Department",
             "hail-report dates to select storm days (context, not verification truth)",
             [("Hail-storm report (PDF)", URL_IMD), ("mausam.imd.gov.in", "https://mausam.imd.gov.in/")],
             "qr_imd_hail.png")
source_badge(0.35 + bw_ + 0.12, bw_, "NOAA", "NCEP|CPC", PSTEPS,
             "NOAA / NCEP Climate Prediction Center",
             "Globally Merged IR: all satellite inputs + truth · ~4 km · 30-min",
             [("Merged IR page", URL_CPC), ("Full-res IR", URL_CPC_FULL), ("Archive used", URL_CPC_DATA)],
             "qr_cpc_merged_ir.png")
MX = 0.35 + DSW + 0.2
shape(s6, MX, 5.62, MPW, 1.24, fill=WHITE, line=TEAL, lw=1.25)
mrows = [("pySTEPS", "external open-source: advection baseline + FSS", "pySTEPS official repo", URL_PYSTEPS),
         ("STORMLIFE REPOSITORY", "GitHub: our code · replay pipeline · validation · evidence", "[REPOSITORY URL]", None),
         ("DEMO / REPLAY", "short demo of the verified prototype", "Demo video [VIDEO LINK]", None)]
my, mh = 5.66, 1.16 / 3
for j, (ttl, purpose, lab, url) in enumerate(mrows):
    tb = textbox(s6, MX + 0.08, my + j * mh + 0.01, MPW - 0.16, mh - 0.02, [[(ttl, {"bold": True, "color": TEAL, "size": 8.8}), ("  →  ", {"color": MUTED, "size": 8.8})],
                                                             [(purpose, {"italic": True, "color": INK, "size": 8.5})]],
                 anchor=MSO_ANCHOR.MIDDLE, margin=0.0)
    for pa in tb.text_frame.paragraphs:
        pa.space_after = Pt(0)
    if url:
        para = tb.text_frame.paragraphs[0]
        r = para.add_run(); r.text = lab; r.font.name = FONT; r.font.size = Pt(8.8); r.font.bold = True; r.font.underline = True
        r.font.color.rgb = PSTEPS; r.hyperlink.address = url
    else:
        para = tb.text_frame.paragraphs[0]
        r = para.add_run(); r.text = lab; r.font.name = FONT; r.font.size = Pt(8.8); r.font.bold = True; r.font.color.rgb = AMBER
    if j < 2:
        sep = s6.shapes.add_connector(1, Inches(MX + 0.12), Inches(my + (j + 1) * mh), Inches(MX + MPW - 0.12), Inches(my + (j + 1) * mh))
        sep.line.color.rgb = LINE; sep.line.width = Pt(0.75)
notes(s6, "Existing radar, lightning, NWP and satellite systems already provide storm guidance; StormLife complements them. "
          "In India, open access and latency constrain independent validation, so our question was what can be verified from "
          "open geostationary IR alone. Our contribution answers it: satellite-first, baseline-first, calibrated probability, "
          "audited tracking, real-event replay, traceable evidence and explicit limitations. The two primary data sources are "
          "IMD (hail-report dates, for event selection) and NOAA/NCEP/CPC (Globally Merged IR, all satellite data). "
          "References: pySTEPS, Pulkkinen et al., GMD 12, 4185 (2019); tobac, Heikenfeld et al., GMD 12, 4551 (2019) and v1.5, "
          "GMD 17, 5309 (2024); TITAN, Dixon & Wiener (1993); FSS, Roberts & Lean (2008); ProbSevere v3, Cintineo et al., "
          "Wea. Forecasting 39(12) (2024). Links: " + URL_IMD + " ; " + URL_CPC + " ; " + URL_CPC_FULL + " ; " + URL_CPC_DATA)


# footer text on slides 2-6 (slide 1 has no footer in the official template); same placeholder, so position/style are unchanged
for _sl in S[1:]:
    for _sh in _sl.shapes:
        if _sh.name.startswith("Footer Placeholder"):
            _runs = [r for p_ in _sh.text_frame.paragraphs for r in p_.runs]
            _runs[0].text = FOOTER
            for r in _runs[1:]:
                r.text = ""

# delete the template's instruction slide (template note: it can be deleted before upload)
delete_slide(prs, 6)
prs.save(str(OUT))
print("saved", OUT, "slides:", len(prs.slides))
