"""Regenerate the hero photo's WebP versions from static/img/hero-tokyo.jpg.

Run after replacing the photo (needs Pillow, e.g. the admin venv):
    ~/.venvs/leadjapan-cms/bin/python tools/hero_images.py
"""
from __future__ import annotations

import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static/img/hero-tokyo.jpg"
WIDTHS = (960, 1280, 1920)  # keep in step with HERO_WIDTHS in sitegen/pages.py


def main() -> None:
    with Image.open(SOURCE) as src:
        im = src.convert("RGB")
    for w in WIDTHS:
        out = SOURCE.with_name(f"hero-tokyo-{w}.webp")
        size = (w, round(im.height * w / im.width))
        (im if size == im.size else im.resize(size, Image.LANCZOS)).save(out, "WEBP", quality=80, method=6)
        print(f"{out.relative_to(ROOT)}: {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
