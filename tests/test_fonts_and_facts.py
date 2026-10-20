import re
import unittest
from pathlib import Path

from sitegen.content import NEWS, PLACEHOLDER, SITE, UNCONFIRMED
from sitegen.render import FONTS_URL

ROOT = Path(__file__).resolve().parents[1]


class FontTests(unittest.TestCase):
    def test_google_fonts_inter_and_noto_sans_jp_only(self):
        self.assertIn("family=Inter:", FONTS_URL)
        self.assertIn("family=Noto+Sans+JP:", FONTS_URL)
        self.assertNotIn("Serif", FONTS_URL)

    def test_loads_exactly_the_weights_the_css_uses(self):
        css = "".join((ROOT / f"static/css/{n}.css").read_text(encoding="utf-8") for n in ("style", "motion"))
        used = {"400"} | set(re.findall(r"font-weight:\s*(\d+)", css))  # 400: body text
        for family in ("Inter", "Noto+Sans+JP"):
            m = re.search(rf"family={re.escape(family)}:wght@([\d;]+)", FONTS_URL)
            self.assertEqual(set(m.group(1).split(";")), used, family)

    def test_css_uses_inter_then_noto_sans_jp(self):
        css = (ROOT / "static/css/style.css").read_text(encoding="utf-8")
        self.assertNotIn("Noto Serif JP", css)
        self.assertIn('--font: "Inter", "Noto Sans JP", sans-serif', css)


class CompanyFactsTests(unittest.TestCase):
    def test_company_facts(self):
        self.assertEqual(SITE["representative"], "山口康平")
        self.assertEqual(SITE["founded"], "2026年10月19日")
        self.assertEqual(SITE["address"], "東京都中野区")
        self.assertEqual(SITE["email"], PLACEHOLDER)  # TBC

    def test_founding_news_dated_on_founding_day(self):
        founding = [n for n in NEWS if n.slug == "founding"]
        if founding:
            self.assertEqual(founding[0].date.isoformat(), "2026-10-19")
        self.assertFalse(any("設立のお知らせ" in u for u in UNCONFIRMED))


if __name__ == "__main__":
    unittest.main()
