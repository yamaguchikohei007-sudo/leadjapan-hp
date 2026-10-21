"""Map of Japan for the home page hero: projection and prefecture pins (stdlib only).

The map (static/img/japan-map.svg) and the pin table in functions/index.js are
both made by tools/japan_map.py from these values; tests check they agree.
"""
from __future__ import annotations

import math

# Map area: Hokkaido to Taiwan, with the Korean peninsula and the Russian coast.
LON_MIN, LON_MAX = 112.0, 158.0
LAT_MIN, LAT_MAX = 18.0, 52.0
MAP_WIDTH = 800


def _merc(lat: float) -> float:
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


MAP_HEIGHT = round(MAP_WIDTH * (_merc(LAT_MAX) - _merc(LAT_MIN)) / math.radians(LON_MAX - LON_MIN))


def project(lat: float, lon: float) -> tuple[float, float]:
    """Mercator (lat, lon) -> map (x, y), rounded to 0.1."""
    x = (lon - LON_MIN) / (LON_MAX - LON_MIN) * MAP_WIDTH
    y = (_merc(LAT_MAX) - _merc(lat)) / (_merc(LAT_MAX) - _merc(LAT_MIN)) * MAP_HEIGHT
    return round(x, 1), round(y, 1)


# ISO 3166-2:JP code -> (prefectural capital, lat, lon). The visitor's pin snaps
# to one of these, so it never shows more than "which prefecture".
PREFECTURES: dict[str, tuple[str, float, float]] = {
    "01": ("Sapporo", 43.06, 141.35), "02": ("Aomori", 40.82, 140.74),
    "03": ("Morioka", 39.70, 141.15), "04": ("Sendai", 38.27, 140.87),
    "05": ("Akita", 39.72, 140.10), "06": ("Yamagata", 38.24, 140.36),
    "07": ("Fukushima", 37.75, 140.47), "08": ("Mito", 36.34, 140.45),
    "09": ("Utsunomiya", 36.57, 139.88), "10": ("Maebashi", 36.39, 139.06),
    "11": ("Saitama", 35.86, 139.65), "12": ("Chiba", 35.61, 140.12),
    "13": ("Tokyo", 35.69, 139.69), "14": ("Yokohama", 35.45, 139.64),
    "15": ("Niigata", 37.90, 139.02), "16": ("Toyama", 36.70, 137.21),
    "17": ("Kanazawa", 36.59, 136.63), "18": ("Fukui", 36.07, 136.22),
    "19": ("Kofu", 35.66, 138.57), "20": ("Nagano", 36.65, 138.18),
    "21": ("Gifu", 35.39, 136.72), "22": ("Shizuoka", 34.98, 138.38),
    "23": ("Nagoya", 35.18, 136.91), "24": ("Tsu", 34.73, 136.51),
    "25": ("Otsu", 35.00, 135.87), "26": ("Kyoto", 35.02, 135.76),
    "27": ("Osaka", 34.69, 135.52), "28": ("Kobe", 34.69, 135.18),
    "29": ("Nara", 34.69, 135.83), "30": ("Wakayama", 34.23, 135.17),
    "31": ("Tottori", 35.50, 134.24), "32": ("Matsue", 35.47, 133.05),
    "33": ("Okayama", 34.66, 133.93), "34": ("Hiroshima", 34.40, 132.46),
    "35": ("Yamaguchi", 34.19, 131.47), "36": ("Tokushima", 34.07, 134.56),
    "37": ("Takamatsu", 34.34, 134.04), "38": ("Matsuyama", 33.84, 132.77),
    "39": ("Kochi", 33.56, 133.53), "40": ("Fukuoka", 33.61, 130.42),
    "41": ("Saga", 33.25, 130.30), "42": ("Nagasaki", 32.74, 129.87),
    "43": ("Kumamoto", 32.79, 130.74), "44": ("Oita", 33.24, 131.61),
    "45": ("Miyazaki", 31.91, 131.42), "46": ("Kagoshima", 31.56, 130.56),
    "47": ("Naha", 26.21, 127.68),
}

# Shown for visitors outside Japan, unknown locations, and when the Function does not run.
DEFAULT_PREFECTURE = "13"


def pin_xy(code: str = DEFAULT_PREFECTURE) -> tuple[float, float]:
    _, lat, lon = PREFECTURES[code]
    return project(lat, lon)
