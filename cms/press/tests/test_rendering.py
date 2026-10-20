from django.test import SimpleTestCase

from press.rendering import render_markdown


class RenderMarkdownTests(SimpleTestCase):
    def test_unsafe_link_preserves_formatted_label_and_following_safe_link(self):
        out = render_markdown('[**注意**](JaVaScRiPt:alert(1)) [案内](contact.html)')
        self.assertEqual(out, '<p><strong>注意</strong> <a href="contact.html">案内</a></p>\n')

    def test_images_inside_links_keep_escaped_alt_text_and_safe_link(self):
        for target, expected in (
            ('https://example.com', '<a href="https://example.com">説明 &lt;b&gt;&amp;</a>'),
            ('javascript:alert(1)', '説明 &lt;b&gt;&amp;'),
        ):
            with self.subTest(target=target):
                out = render_markdown(f'[![説明 <b>&](https://example.com/image.png)]({target})')
                self.assertEqual(out, f'<p>{expected}</p>\n')

    def test_images_in_separate_blocks_keep_only_alt_text(self):
        out = render_markdown('> ![引用](data:image/png;base64,AAAA)\n\n- ![項目](static/x.png)\n\n![](x.png)')
        self.assertEqual(out, '<blockquote>\n<p>引用</p>\n</blockquote>\n<ul>\n<li>項目</li>\n</ul>\n<p></p>\n')

    def test_render_markdown_basic(self):
        out = render_markdown("## 見出し\n\n**太字**\n\n- a")
        self.assertIn("<h2>見出し</h2>", out)
        self.assertIn("<strong>太字</strong>", out)
        self.assertIn("<li>a</li>", out)

    def test_render_markdown_escapes_html_and_unsafe_links(self):
        out = render_markdown(
            '<script>alert(1)</script>\n\n<img src=x onerror=alert(1)>\n\n'
            "[x](javascript:alert(1)) [ok](https://a.jp) [m](mailto:a@b.jp) [r](contact.html)"
        )
        self.assertNotIn("<script", out)
        self.assertNotIn("<img", out)
        self.assertNotIn("javascript:", out)
        for href in ("https://a.jp", "mailto:a@b.jp", "contact.html"):
            self.assertIn(f'href="{href}"', out)

    def test_body_images_render_as_escaped_alt_text(self):
        out = render_markdown(
            "![説明 <b>&](https://example.com/a.png) ![](static/x.png) ![z](javascript:alert(1))")
        self.assertNotIn("<img", out)
        self.assertNotIn("example.com", out)
        self.assertNotIn("javascript:", out)
        self.assertIn("説明 &lt;b&gt;&amp;", out)
