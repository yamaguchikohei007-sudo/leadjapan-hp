import unittest

from tests.helpers import LinkCollector
from sitegen.content import SITE
from sitegen.render import LOGO_MARK, render_layout, find_placeholders


class RenderTests(unittest.TestCase):
    def test_layout_basics(self):
        html = render_layout(title="会社紹介 | Lead Japan 合同会社", description="d", body="<p>x</p>", current="company.html")
        self.assertIn('<html lang="ja">', html)
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn('name="viewport"', html)
        self.assertIn('<a href="company.html" aria-current="page">会社紹介</a>', html)
        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertIn('href="privacy.html"', html)
        self.assertIn("© 2026 Lead Japan LLC", html)

    def test_head_extra_inserted_before_head_close(self):
        html = render_layout(title="t", description="d", body="", current="x.html", head_extra="<meta x>")
        self.assertIn("<meta x>\n</head>", html)
        self.assertNotIn("<meta x>", render_layout(title="t", description="d", body="", current="x.html"))

    def test_layout_escapes_title_and_description(self):
        html = render_layout(title='A<b>&"', description='<x>', body="", current="index.html")
        self.assertIn("<title>A&lt;b&gt;&amp;&quot;</title>", html)
        self.assertNotIn("<x>", html)

    def test_mobile_nav_toggle_markup(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn('id="nav-toggle"', html)
        self.assertIn('for="nav-toggle"', html)

    def test_no_scripts(self):
        p = LinkCollector()
        p.feed(render_layout(title="t", description="d", body="", current="index.html"))
        self.assertEqual(p.scripts, 0)

    def test_logo_mark_uses_current_color(self):
        self.assertIn('viewBox="0 0 256 196"', LOGO_MARK)
        self.assertEqual(LOGO_MARK.count('fill="currentColor"'), 2)
        self.assertEqual(LOGO_MARK.count("<circle"), 1)
        self.assertEqual(LOGO_MARK.count("#D71920"), 1)
        self.assertIn('aria-hidden="true"', LOGO_MARK)

    def test_header_logo_markup(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn(
            f'<a class="logo" href="index.html" aria-label="{SITE["name"]}">{LOGO_MARK}'
            '<span class="logo-text">Lead Japan <small>合同会社</small></span></a>', html)

    def test_footer_logo_markup(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn(f'<div class="footer-logo">{LOGO_MARK}</div>', html)

    def test_find_placeholders(self):
        self.assertEqual(find_placeholders("a【要入力】b【要入力】"), 2)


if __name__ == "__main__":
    unittest.main()
