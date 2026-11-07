"""Render the official NKDA plan-area sheet to a PNG, for georeferencing by hand.

The boundary itself is digitised by `tools/nkda_boundary.py`, which does not need this
image. This exists because the sheet is an unregistered CAD plot with no coordinate grid,
so a better registration is only possible by hand-picking ground control against the
drawing. `sheet_annotated.png` carries a 1000-unit graticule and all 351 text labels at
their true positions, which is what you pick points off.

Two images, same pixels-per-unit scale so they overlay exactly:

* sheet_plain.png      - the drawing only
* sheet_annotated.png  - the drawing plus a 1000-unit graticule and every text label

Output pixel coordinates map to PDF user space as
    x_px = (x_pdf - X0) * SCALE
    y_px = (Y1 - y_pdf) * SCALE      (PDF y is up, PNG y is down)
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

import nkda_boundary as N

SCALE = 1.0                 # pixels per PDF unit
X0, Y0, X1, Y1 = 0.0, 1200.0, 13300.0, 17400.0
GRATICULE_STEP = 1000.0

WIDTH = int((X1 - X0) * SCALE)
HEIGHT = int((Y1 - Y0) * SCALE)

WHITE = (255, 255, 255)
FRAME = (0, 0, 0)
GRAT = (255, 0, 255)
GRAT_TXT = (150, 0, 150)
LABEL = (200, 0, 0)


def to_px(x: float, y: float) -> tuple[float, float]:
    return ((x - X0) * SCALE, (Y1 - y) * SCALE)


def _font(size: int) -> ImageFont.ImageFont:
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_rotated(base: Image.Image, xy: tuple[float, float], text: str,
                 angle_deg: float, font: ImageFont.ImageFont, fill) -> None:
    """Draw text rotated about its baseline origin (matches the PDF text matrix)."""
    if not text.strip():
        return
    pad = 12
    box = font.getbbox(text)
    w = max(1, box[2] - box[0]) + 2 * pad
    h = max(1, box[3] - box[1]) + 2 * pad
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad - box[0], pad - box[1]), text, font=font, fill=fill)
    rot = tile.rotate(-angle_deg, expand=True, resample=Image.BILINEAR)
    base.paste(rot, (int(xy[0]), int(xy[1])), rot)


def render(plain_path: str, annotated_path: str, show_labels: bool = True) -> None:
    sheet = N.load(os.environ.get("NKDA_MAP_CACHE", "boundary/map.pdf"))
    rings = [r for li in sorted(sheet.per_layer) for r in sheet.rings(li)]
    labels = [lb for li in sorted(sheet.per_layer) for lb in sheet.per_layer[li].labels]

    img = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    d = ImageDraw.Draw(img)

    # fills first, then strokes, so linework stays visible
    for source in ("fill", "stroke"):
        for r in rings:
            if r.source != source or len(r.points) < 2:
                continue
            col = r.fill if source == "fill" else r.stroke
            if not col:
                continue
            rgb = tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in col)
            pts = [to_px(*p) for p in r.points]
            if source == "fill" and len(pts) >= 3:
                d.polygon(pts, fill=rgb)
            else:
                lw = 1 if source == "fill" else max(1, int(round(r.line_width * SCALE)))
                d.line(pts, fill=rgb, width=lw)
                if r.line_width * SCALE >= 4:      # thick CAD boundary casing
                    d.line(pts, fill=rgb, width=lw)

    x0, y0 = to_px(101, 1442)
    x1, y1 = to_px(13152, 17284)
    d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)],
                outline=(0, 0, 160), width=3)
    img.save(plain_path)
    print(f"wrote {plain_path}  ({WIDTH} x {HEIGHT} px, {SCALE} px/unit)")

    if not show_labels:
        return

    # ---- annotated companion -------------------------------------------------
    ann = img.copy()
    da = ImageDraw.Draw(ann)
    small = _font(26)
    gx = X0
    while gx <= X1:
        px, _ = to_px(gx, Y0)
        da.line([(px, 0), (px, HEIGHT)], fill=GRAT, width=1)
        da.text((px + 3, 6), f"{int(gx)}", font=small, fill=GRAT_TXT)
        gx += GRATICULE_STEP
    gy = Y0
    while gy <= Y1:
        _, py = to_px(X0, gy)
        da.line([(0, py), (WIDTH, py)], fill=GRAT, width=1)
        da.text((6, py + 3), f"{int(gy)}", font=small, fill=GRAT_TXT)
        gy += GRATICULE_STEP

    for lb in labels:
        size = max(11, int(round(lb.font_size * SCALE * 0.62)))
        f = _font(size)
        draw_rotated(ann, to_px(lb.x, lb.y), lb.text, lb.angle_deg, f, LABEL)

    ann.save(annotated_path)
    print(f"wrote {annotated_path}  (graticule every {int(GRATICULE_STEP)} PDF units "
          f"+ {len(labels)} labels)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="boundary")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    render(os.path.join(a.outdir, "sheet_plain.png"),
           os.path.join(a.outdir, "sheet_annotated.png"))