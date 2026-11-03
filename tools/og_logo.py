"""Make static/img/og-logo.png, the default share image (og:image).

The logo mark comes from sitegen.render.LOGO_MARK (same shapes, white strokes and
a red dot) on the site's navy. Mark and name are stacked in the centre so they
survive the square crop some apps (LINE, X) apply.

    python3 tools/og_logo.py

Needs Pillow plus the Inter and IPAGothic fonts (Debian: fonts-inter, fonts-ipafont-gothic).
Run it again only when the logo, the company name or the colours change.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sitegen.render import LOGO_MARK  # noqa: E402

OUT = ROOT / "static/img/og-logo.png"
WIDTH, HEIGHT = 1200, 630
SCALE = 4  # draw large, then downsample for smooth edges
NAVY = "#10366B"
WHITE = "#FFFFFF"
LATIN_FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
JA_FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

MARK_W, MARK_H = 256, 196  # LOGO_MARK viewBox
MARK_HEIGHT = 230          # on the 1200x630 image
NAME_SIZE = 76             # "Lead Japan"
SUFFIX_SIZE = 46           # "合同会社"
GAP = 44                   # mark -> name


def mark_shapes() -> tuple[list[list[tuple[float, float]]], tuple[float, float, float]]:
    polygons = [[tuple(map(float, p.split(","))) for p in pts.split()]
                for pts in re.findall(r'points="([^"]+)"', LOGO_MARK)]
    cx, cy, r = map(float, re.search(r'cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', LOGO_MARK).groups())
    red = re.search(r'<circle[^>]*fill="(#[0-9A-Fa-f]{6})"', LOGO_MARK).group(1)
    return polygons, (cx, cy, r, red)


def main() -> None:
    s = SCALE
    img = Image.new("RGB", (WIDTH * s, HEIGHT * s), NAVY)
    draw = ImageDraw.Draw(img)

    name_font = ImageFont.truetype(LATIN_FONT, NAME_SIZE * s)
    suffix_font = ImageFont.truetype(JA_FONT, SUFFIX_SIZE * s)
    name, suffix, space = "Lead Japan", "合同会社", 20 * s
    name_w = draw.textlength(name, font=name_font)
    suffix_w = draw.textlength(suffix, font=suffix_font)
    text_w = name_w + space + suffix_w
    cap_h = name_font.getbbox("L")[3] - name_font.getbbox("L")[1]

    k = MARK_HEIGHT * s / MARK_H
    mark_w = MARK_W * k
    block_h = MARK_HEIGHT * s + GAP * s + cap_h
    top = (HEIGHT * s - block_h) / 2
    left = (WIDTH * s - mark_w) / 2

    polygons, (cx, cy, r, red) = mark_shapes()
    for poly in polygons:
        draw.polygon([(left + x * k, top + y * k) for x, y in poly], fill=WHITE)
    draw.ellipse([left + (cx - r) * k, top + (cy - r) * k, left + (cx + r) * k, top + (cy + r) * k], fill=red)

    # Baseline-align both runs; bottom of the cap height sits at the block bottom.
    baseline = top + block_h
    x = (WIDTH * s - text_w) / 2
    draw.text((x, baseline), name, font=name_font, fill=WHITE, anchor="ls")
    draw.text((x + name_w + space, baseline), suffix, font=suffix_font, fill=WHITE, anchor="ls")

    img.resize((WIDTH, HEIGHT), Image.LANCZOS).save(OUT, optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
