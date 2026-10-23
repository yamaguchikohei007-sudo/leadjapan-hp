"""Make static/img/japan-map.svg and the pin table in functions/index.js.

Map data: Natural Earth (public domain), countries drawn from Japan's point of view:
https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries_jpn.geojson

    python3 tools/japan_map.py path/to/ne_10m_admin_0_countries_jpn.geojson

Run it again only when sitegen/geo.py changes (map area or prefectures).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sitegen.geo import (DEFAULT_PREFECTURE, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, MAP_HEIGHT,  # noqa: E402
                         MAP_WIDTH, PREFECTURES, project)

ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "static/img/japan-map.svg"
FUNCTION = ROOT / "functions/index.js"
PINS_RE = re.compile(r"(// BEGIN PINS[^\n]*\n).*?(// END PINS)", re.S)

PAD = 10      # px outside the view kept, so clipped coasts do not show an edge
STEP = 1.6    # px: points closer than this to the previous one are dropped
MIN_AREA = 3  # px²: smaller islands are dropped

STYLE = (".land{fill:#A9C1E3;fill-opacity:.07;stroke:#A9C1E3;stroke-opacity:.28;stroke-width:.8}"
         ".jp{fill:#A9C1E3;fill-opacity:.22;stroke:#fff;stroke-opacity:.6;stroke-width:1}")


def _clip(x: float, y: float) -> tuple[float, float]:
    return min(max(x, -PAD), MAP_WIDTH + PAD), min(max(y, -PAD), MAP_HEIGHT + PAD)


def _area(pts: list[tuple[float, float]]) -> float:
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2


def _ring_path(ring: list[list[float]]) -> str:
    if not any(LON_MIN - 5 < lon < LON_MAX + 5 and LAT_MIN - 5 < lat < LAT_MAX + 5 for lon, lat in ring):
        return ""
    pts: list[tuple[float, float]] = []
    for lon, lat in ring:
        lat = max(min(lat, 85), -85)
        p = _clip(*project(lat, lon))
        if not pts or abs(p[0] - pts[-1][0]) + abs(p[1] - pts[-1][1]) >= STEP:
            pts.append(p)
    if len(pts) < 3 or _area(pts) < MIN_AREA:
        return ""
    return "M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in pts) + "Z"


def map_svg(geojson: dict) -> str:
    paths = []
    for feature in geojson["features"]:
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        d = "".join(_ring_path(poly[0]) for poly in polys)
        if d:
            cls = "jp" if feature["properties"]["ADM0_A3"] == "JPN" else "land"
            paths.append(f'<path class="{cls}" d="{d}"/>')
    paths.sort(key=lambda p: 'class="jp"' in p)  # Japan on top
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MAP_WIDTH} {MAP_HEIGHT}" '
            f'width="{MAP_WIDTH}" height="{MAP_HEIGHT}"><style>{STYLE}</style>{"".join(paths)}</svg>\n')


def pins_js() -> str:
    rows = []
    for code, (city, lat, lon) in PREFECTURES.items():
        x, y = project(lat, lon)
        rows.append(f'  "{code}": [{x}, {y}, {lat}, {lon}], // {city}')
    return ("const PINS = {\n" + "\n".join(rows) + "\n};\n"
            f'const DEFAULT_CODE = "{DEFAULT_PREFECTURE}";\n')


def update_function(text: str) -> str:
    new, n = PINS_RE.subn(lambda m: m.group(1) + pins_js() + m.group(2), text)
    if n != 1:
        raise SystemExit(f"{FUNCTION}: BEGIN/END PINS markers not found")
    return new


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    geojson = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    SVG_OUT.write_text(map_svg(geojson), encoding="utf-8")
    FUNCTION.write_text(update_function(FUNCTION.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"wrote {SVG_OUT.relative_to(ROOT)} ({SVG_OUT.stat().st_size} bytes) and the pins in "
          f"{FUNCTION.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
