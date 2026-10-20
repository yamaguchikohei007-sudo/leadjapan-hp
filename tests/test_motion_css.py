"""Motion CSS contract: content must stay visible without scroll timelines."""
import re
import unittest

from tests.helpers import ROOT

SUPPORTS = "@supports (animation-timeline: view())"
REDUCED = "@media (prefers-reduced-motion: reduce)"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _match_end(css: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced braces")


def extract_block(css: str, prelude: str) -> str:
    """Return the full text of the block starting at `prelude` (incl. braces)."""
    start = css.find(prelude)
    if start == -1:
        return ""
    open_idx = css.index("{", start)
    return css[start:_match_end(css, open_idx)]


def strip_keyframes(css: str, prefix: str) -> str:
    """Remove every `@keyframes <prefix>...{...}` block."""
    while True:
        m = re.search(r"@keyframes\s+" + re.escape(prefix), css)
        if not m:
            return css
        end = _match_end(css, css.index("{", m.start()))
        css = css[:m.start()] + css[end:]


class MotionCssTests(unittest.TestCase):
    def css(self) -> str:
        return strip_comments(read("static/css/motion.css"))

    def test_hidden_state_only_inside_supports(self):
        css = self.css()
        inside = extract_block(css, SUPPORTS)
        self.assertTrue(inside)
        outside = strip_keyframes(css.replace(inside, ""), prefix="hero-")
        self.assertIn("opacity: 0", inside)
        self.assertNotIn("opacity: 0", outside)

    def test_reveal_uses_view_timeline(self):
        inside = extract_block(self.css(), SUPPORTS)
        self.assertIn("animation-timeline: view()", inside)
        self.assertIn("scroll(root)", inside)
        for mod in ("reveal--left", "reveal--right", "reveal--zoom"):
            self.assertIn(mod, inside)

    def test_hero_keyframes_outside_supports(self):
        css = self.css()
        outside = css.replace(extract_block(css, SUPPORTS), "")
        self.assertRegex(outside, r"@keyframes hero-")

    def test_reduced_motion_disables_animation(self):
        block = extract_block(self.css(), REDUCED)
        self.assertIn("animation: none !important", block)
        self.assertIn("transition: none !important", block)
        self.assertIn("scroll-behavior: auto !important", block)
        self.assertIn("opacity: 1 !important", block)

    def test_style_css_never_hides_reveal(self):
        css = strip_comments(read("static/css/style.css"))
        self.assertNotRegex(css, r"\.reveal[^{]*\{[^}]*opacity:\s*0")

    def reveal_rule(self) -> str:
        m = re.search(r"(?m)^\s*\.reveal\s*\{([^}]*)\}", extract_block(self.css(), SUPPORTS))
        self.assertTrue(m, ".reveal rule inside @supports")
        return m.group(1)

    def test_reveal_rule_order_and_fill(self):
        body = self.reveal_rule()
        shorthand = re.search(r"animation:\s*([^;]*);", body).group(1).split()
        # "backwards": hidden before the range, but never held hidden after it
        self.assertIn("backwards", shorthand)
        self.assertFalse({"both", "forwards"} & set(shorthand))
        # the shorthand resets animation-timeline, so the timeline must come after it
        self.assertGreater(body.index("animation-timeline"), body.index("animation:"))

    def test_reveal_range_is_capped_in_absolute_lengths(self):
        # tall wrappers must not stretch the fade over their whole height
        rng = " ".join(re.search(r"animation-range:([^;]*);", self.reveal_rule()).group(1).split())
        self.assertTrue(rng.startswith("entry"), rng)
        self.assertIn("px", rng)
        self.assertNotIn("cover", rng)
        self.assertNotIn("%", rng)

    def test_hero_copy_rules_exist(self):
        css = self.css()
        self.assertIn(".hero .hero-kicker {", css)
        self.assertIn(".hero .hero-sub", css)

    def test_main_clips_horizontal_overflow(self):
        css = strip_comments(read("static/css/style.css"))
        self.assertRegex(css, r"(?m)^main\s*\{[^}]*overflow-x:\s*clip")
        for sel in ("html", "body"):
            m = re.search(r"(?m)^" + sel + r"\s*\{([^}]*)\}", css)
            self.assertNotIn("overflow-x: hidden", m.group(1) if m else "")

    def test_helpers(self):
        css = "@a{x{y:1}} @keyframes hero-a{from{opacity: 0}} @keyframes b{}"
        self.assertEqual(extract_block(css, "@a"), "@a{x{y:1}}")
        self.assertNotIn("hero-a", strip_keyframes(css, "hero-"))
        self.assertIn("@keyframes b", strip_keyframes(css, "hero-"))


if __name__ == "__main__":
    unittest.main()
