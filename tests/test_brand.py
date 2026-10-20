import re
import unittest

from tests.helpers import ROOT
from sitegen.render import render_layout

CSS = ROOT / "static/css/style.css"

LEGACY = ("0b1f3a", "13315c", "e8380d", "c4300a", "c8a24a", "071629",
          "ff6a3d", "ff5a2a", "rgba(11, 31, 58", "rgba(5, 15, 32", "--tower", "--gold")


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(hex1: str, hex2: str) -> float:
    hi, lo = sorted((_luminance(hex1), _luminance(hex2)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def css_rule(selector: str) -> str:
    # every rule for the selector (it may also appear inside a media query)
    pattern = r"(?<![\w-])" + re.escape(selector) + r"\s*\{([^}]*)\}"
    return "\n".join(re.findall(pattern, CSS.read_text(encoding="utf-8")))


class BrandColorTests(unittest.TestCase):
    def test_root_tokens(self):
        css = CSS.read_text(encoding="utf-8").lower()
        for token in ("--navy: #10366b;", "--red: #d71920;", "--sky: #a9c1e3;"):
            self.assertIn(token, css)

    def test_no_legacy_colors(self):
        files = [*ROOT.glob("static/css/*.css"), *ROOT.glob("static/img/*.svg"),
                 *ROOT.glob("sitegen/*.py")]
        for path in files:
            text = path.read_text(encoding="utf-8").lower()
            for legacy in LEGACY:
                self.assertNotIn(legacy, text, f"{path.name}: {legacy}")

    def test_contrast_pairs(self):
        self.assertGreaterEqual(contrast("#D71920", "#FFFFFF"), 4.5)
        self.assertGreaterEqual(contrast("#FFFFFF", "#10366B"), 4.5)
        self.assertGreaterEqual(contrast("#A9C1E3", "#10366B"), 4.5)
        self.assertGreaterEqual(contrast("#10366B", "#F3F6FA"), 4.5)
        # red text on navy is unreadable: keep red to decoration there
        self.assertLess(contrast("#D71920", "#10366B"), 4.5)

    def test_labels_on_navy_use_sky(self):
        for selector in (".page-hero .section-label", ".cta-band .section-label", ".hero-kicker"):
            self.assertIn("color: var(--sky)", css_rule(selector), selector)

    def test_focus_and_current_marks_on_navy_are_white(self):
        # red on navy is 2.3:1, under the 3:1 WCAG 1.4.11 needs for focus/state cues
        self.assertGreaterEqual(contrast("#FFFFFF", "#10366B"), 3)
        css = re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)
        rules = {sel.strip(): body for sels, body in re.findall(r"([^{}]+)\{([^}]*)\}", css)
                 for sel in sels.split(",")}
        for selector in (".site-footer :focus-visible", ".cta-band :focus-visible",
                         ".page-hero :focus-visible", ".hero :focus-visible",
                         ".skip-link:focus-visible",
                         ".global-nav:popover-open :focus-visible"):
            self.assertIn("outline-color: #fff", rules.get(selector, ""), selector)
        self.assertIn("background: #fff",
                      rules.get(".global-nav:popover-open a::after", ""))


class MobileMenuCssTests(unittest.TestCase):
    def css(self) -> str:
        return re.sub(r"/\*.*?\*/", "", CSS.read_text(encoding="utf-8"), flags=re.S)

    def test_closed_popover_stays_hidden_on_mobile(self):
        # an unscoped display on .global-nav would beat the browser's popover hiding
        base = re.search(r"(?m)^\.global-nav \{([^}]*)\}", self.css())
        self.assertNotIn("display", base.group(1))

    def test_open_menu_styles_apply_at_every_width(self):
        # a menu opened on a narrow screen can stay open while it widens (tablet rotation)
        css = self.css()
        self.assertRegex(css, r"(?m)^\.global-nav:popover-open \{")
        self.assertRegex(css, r"(?m)^\.global-nav:popover-open \.nav-close \{")
        self.assertIn(".global-nav[popover]:not(:popover-open) {", css)

    def test_page_behind_open_menu_does_not_scroll(self):
        self.assertIn("html:has(.global-nav:popover-open) { overflow: hidden; }", self.css())

    def test_fallback_without_popover_support(self):
        css = self.css()
        start = css.index("@supports not selector(:popover-open)")
        self.assertIn(".nav-fallback", css[start:])


class FaviconTests(unittest.TestCase):
    def test_favicon_uses_brand_mark(self):
        path = ROOT / "static/img/favicon.svg"
        svg = path.read_text(encoding="utf-8")
        self.assertRegex(svg, r'<rect[^>]*fill="#10366B"')
        self.assertRegex(svg, r'<circle[^>]*fill="#D71920"')
        self.assertEqual(svg.count("<polygon"), 2)
        self.assertNotIn("<text", svg)
        self.assertNotIn("<script", svg)
        self.assertLess(path.stat().st_size, 1024)

    def test_theme_color(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn('<meta name="theme-color" content="#10366B">', html)


if __name__ == "__main__":
    unittest.main()
