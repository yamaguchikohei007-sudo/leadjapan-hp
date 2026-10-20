import re
import unittest

from tests.helpers import ROOT

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


if __name__ == "__main__":
    unittest.main()
