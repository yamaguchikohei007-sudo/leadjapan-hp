import unittest

from tests.helpers import LinkCollector
from sitegen.content import SITE
from sitegen.render import LOGO_MARK, render_layout, find_placeholders, url


class RenderTests(unittest.TestCase):
    def test_layout_basics(self):
        html = render_layout(title="会社紹介 | Lead Japan 合同会社", description="d", body="<p>x</p>", current="company.html")
        self.assertIn('<html lang="ja">', html)
        self.assertIn('<meta charset="utf-8">', html)
        self.assertIn('name="viewport"', html)
        self.assertIn('<a href="/company.html" aria-current="page">会社紹介</a>', html)
        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertIn('href="/privacy.html"', html)
        self.assertIn('href="/static/css/style.css"', html)
        self.assertIn("© 2026 Lead Japan LLC", html)

    def test_url(self):
        self.assertEqual(url("company.html"), "/company.html")
        self.assertEqual(url("business.html#ai"), "/business.html#ai")
        self.assertEqual(url("index.html"), "/")
        self.assertEqual(url("index.html#news"), "/#news")
        self.assertEqual(url("static/img/a.png"), "/static/img/a.png")
        for unchanged in ("/media/a.png", "https://example.com/", "mailto:a@example.jp", "#main"):
            self.assertEqual(url(unchanged), unchanged)

    def test_head_extra_inserted_before_head_close(self):
        html = render_layout(title="t", description="d", body="", current="x.html", head_extra="<meta x>")
        self.assertIn("<meta x>\n</head>", html)
        self.assertNotIn("<meta x>", render_layout(title="t", description="d", body="", current="x.html"))

    def test_layout_escapes_title_and_description(self):
        html = render_layout(title='A<b>&"', description='<x>', body="", current="index.html")
        self.assertIn("<title>A&lt;b&gt;&amp;&quot;</title>", html)
        self.assertNotIn("<x>", html)

    def test_mobile_nav_is_a_native_popover(self):
        # popover: Esc closes it and the button reports open/closed, without JavaScript
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn('<button type="button" class="nav-toggle" popovertarget="global-nav">', html)
        self.assertIn('<nav id="global-nav" class="global-nav" popover ', html)
        self.assertIn('popovertarget="global-nav" popovertargetaction="hide"', html)
        self.assertIn("メニューを閉じる", html)
        self.assertNotIn('type="checkbox"', html)

    def test_menu_button_named_once(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        toggle = html.split('class="nav-toggle"', 1)[1].split("</button>", 1)[0]
        self.assertEqual(toggle.count("メニュー"), 1)
        self.assertNotIn("aria-label", toggle)

    def test_menu_fallback_links_to_footer_nav(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn('<a class="nav-fallback" href="#footer-nav">メニュー</a>', html)
        self.assertIn('<nav id="footer-nav"', html)

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
            f'<a class="logo" href="/" aria-label="{SITE["name"]}">{LOGO_MARK}'
            '<span class="logo-text">Lead Japan <small>合同会社</small></span></a>', html)

    def test_footer_logo_markup(self):
        html = render_layout(title="t", description="d", body="", current="index.html")
        self.assertIn(f'<div class="footer-logo">{LOGO_MARK}</div>', html)

    def test_find_placeholders(self):
        self.assertEqual(find_placeholders("a【要入力】b【要入力】"), 2)


if __name__ == "__main__":
    unittest.main()
