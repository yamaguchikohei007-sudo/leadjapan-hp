"""Visitor pin: map data, generated pin table and the Pages Function."""
import json
import re
import shutil
import subprocess
import unittest

from tests.helpers import ROOT
from sitegen.geo import DEFAULT_PREFECTURE, MAP_HEIGHT, MAP_WIDTH, PREFECTURES, pin_xy
from tools.japan_map import PINS_RE, pins_js

FUNCTION = ROOT / "functions/index.js"


class MapTests(unittest.TestCase):
    def test_map_svg(self):
        path = ROOT / "static/img/japan-map.svg"
        svg = path.read_text(encoding="utf-8")
        self.assertIn(f'viewBox="0 0 {MAP_WIDTH} {MAP_HEIGHT}"', svg)
        self.assertEqual(svg.count('class="jp"'), 1)
        self.assertNotIn("<script", svg)
        self.assertLess(path.stat().st_size, 100 * 1024)

    def test_every_prefecture_inside_the_map(self):
        self.assertEqual(sorted(PREFECTURES), [f"{n:02d}" for n in range(1, 48)])
        for code in PREFECTURES:
            x, y = pin_xy(code)
            self.assertTrue(0 < x < MAP_WIDTH and 0 < y < MAP_HEIGHT, code)

    def test_function_pins_match_geo(self):
        # regenerate with: python3 tools/japan_map.py <geojson>
        block = PINS_RE.search(FUNCTION.read_text(encoding="utf-8"))
        self.assertIsNotNone(block)
        self.assertIn(pins_js(), block.group(0))
        self.assertEqual(DEFAULT_PREFECTURE, "13")


class RoutesTests(unittest.TestCase):
    def test_function_only_runs_for_the_home_page(self):
        from tests.helpers import build_to_tmp
        out = build_to_tmp()
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        routes = json.loads((out / "_routes.json").read_text(encoding="utf-8"))
        self.assertEqual(routes, {"version": 1, "include": ["/"], "exclude": []})
        self.assertEqual([p.name for p in (ROOT / "functions").iterdir()], ["index.js"])

    def test_function_never_logs_or_stores(self):
        js = FUNCTION.read_text(encoding="utf-8")
        for word in ("console.", "fetch(", ".put(", "caches"):
            self.assertNotIn(word, js)
        self.assertIn('"private, no-store"', js)


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class FunctionBehaviourTests(unittest.TestCase):
    def test_node_tests_pass(self):
        r = subprocess.run(["node", "--test", "tests/js/visitor_pin.test.mjs"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, re.compile(r"# pass [1-9]"))


if __name__ == "__main__":
    unittest.main()
