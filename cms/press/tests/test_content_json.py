from django.test import SimpleTestCase

from sitegen.news import load_news

from press.rendering import render_markdown


class CommittedNewsJsonTests(SimpleTestCase):
    """content/news.json stores body_html, which the site embeds without escaping.
    It must be exactly what the sanitising renderer makes of body_md, so a hand
    edit (or a drift between the two) cannot slip unsanitised HTML onto the site."""

    def test_body_html_matches_rendered_body_md(self):
        for item in load_news():
            with self.subTest(slug=item.slug):
                self.assertEqual(item.body_html.strip(), render_markdown(item.body_md).strip())
