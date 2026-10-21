import pathlib
import shutil
import tempfile
import unittest
from unittest import mock

from tests.helpers import (LinkCollector, build_to_tmp, check_internal_links_resolve, check_no_javascript,
                           check_only_free_external_hosts, check_unique_titles, collect)
from build import build, format_warnings, placeholder_report
from sitegen.content import SITE_URL, UNCONFIRMED, NEWS
from sitegen.pages import NOINDEX, PAGES, article_pages, news_page_filename


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build_to_tmp()
        cls.addClassCleanup(shutil.rmtree, cls.out, ignore_errors=True)

    def test_writes_all_pages(self):
        names = sorted(p.name for p in self.out.glob("*.html"))
        self.assertEqual(names, sorted(["index.html", "company.html", "business.html", "message.html",
                                        "news.html", "privacy.html", "contact.html", "404.html",
                                        "pm-book.html", "pm-book-bonus.html", "pm-book-bonus-error.html"]
                                       + [news_page_filename(n) for n in NEWS]))

    def test_article_pages_written_and_linked(self):
        index = (self.out / "index.html").read_text(encoding="utf-8")
        latest = {news_page_filename(n) for n in NEWS[:3]}  # the home page shows only the latest three
        for item in NEWS:
            name = news_page_filename(item)
            self.assertTrue((self.out / name).exists(), name)
            self.assertIn(f'href="/{name}"', (self.out / "news.html").read_text(encoding="utf-8"))
            if name in latest:
                self.assertIn(f'href="/{name}"', index)
            page = (self.out / name).read_text(encoding="utf-8")
            self.assertIn('<a href="/news.html" aria-current="page">', page)
            self.assertEqual(page.count('aria-current="page"'), 1)
            self.assertIn('property="og:title"', page)

    def test_unpublished_article_has_no_page_or_link(self):
        if len(NEWS) < 2:
            self.skipTest("needs at least two articles")
        kept, dropped = NEWS[:-1], news_page_filename(NEWS[-1])
        pages = [p for p in PAGES if not p.filename.startswith("news-")] + article_pages(kept)
        out = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        with mock.patch("sitegen.pages.NEWS", kept):
            build(out, pages)
        self.assertFalse((out / dropped).exists())
        for page in out.glob("*.html"):
            self.assertNotIn(f'href="/{dropped}"', page.read_text(encoding="utf-8"), page.name)
        sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn(dropped.removesuffix(".html") + "<", sitemap)

    def test_static_copied(self):
        self.assertTrue((self.out / "static/css/style.css").exists())
        self.assertTrue((self.out / "static/img/tokyo-skyline.svg").exists())

    def test_resources_are_root_relative(self):
        # 404.html is served for missing URLs at any depth (/a/b/c), so CSS and
        # images must not depend on the page's own location.
        for page in self.out.glob("*.html"):
            for link in collect(page).resources:
                if not link.startswith("https:"):
                    self.assertTrue(link.startswith("/"), f"{page.name}: {link}")

    def test_layout_links_are_root_relative(self):
        text = (self.out / "404.html").read_text(encoding="utf-8")
        for href in ("/", "/company.html", "/news.html", "/privacy.html"):
            self.assertIn(f'href="{href}"', text)
        self.assertNotIn('href="company.html"', text)

    def test_sitemap_and_robots(self):
        sitemap = (self.out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"<loc>{SITE_URL}/</loc>", sitemap)
        self.assertIn(f"<loc>{SITE_URL}/company</loc>", sitemap)
        self.assertNotIn("404", sitemap)
        for item in NEWS:
            self.assertIn(f"<loc>{SITE_URL}/news-{item.slug}</loc><lastmod>{item.date.isoformat()}</lastmod>",
                          sitemap)
        robots = (self.out / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Sitemap: {SITE_URL}/sitemap.xml", robots)

    def test_every_page_has_canonical_and_og_except_noindex(self):
        for page in self.out.glob("*.html"):
            text = page.read_text(encoding="utf-8")
            if page.name in NOINDEX:
                self.assertIn('<meta name="robots" content="noindex">', text)
                self.assertNotIn('rel="canonical"', text)
                continue
            self.assertEqual(text.count('rel="canonical"'), 1, page.name)
            self.assertIn('property="og:image"', text, page.name)

    def test_home_has_organization_jsonld(self):
        self.assertEqual(collect(self.out / "index.html").jsonld, 1)
        for page in self.out.glob("*.html"):
            if page.name not in ("index.html", "pm-book.html"):  # pm-book.html: Book (tests/test_book.py)
                self.assertEqual(collect(page).jsonld, 0, page.name)

    def test_all_internal_links_resolve(self):
        check_internal_links_resolve(self, self.out)

    def test_no_javascript_anywhere(self):
        check_no_javascript(self, self.out)

    def test_only_free_external_hosts(self):
        check_only_free_external_hosts(self, self.out)

    def test_unique_titles(self):
        check_unique_titles(self, self.out)

    def test_404_content(self):
        text = (self.out / "404.html").read_text(encoding="utf-8")
        self.assertIn("ページが見つかりません", text)
        self.assertIn('href="/"', text)

    def test_placeholder_report(self):
        # Content-independent: real pages may or may not still contain markers.
        with tempfile.TemporaryDirectory() as d:
            marked = pathlib.Path(d) / "a.html"
            clean = pathlib.Path(d) / "b.html"
            marked.write_text("x【要入力】y【要入力】", encoding="utf-8")
            clean.write_text("nothing to fill", encoding="utf-8")
            self.assertEqual(placeholder_report([marked, clean]), {"a.html": 2})
        report = placeholder_report(list(self.out.glob("*.html")))
        self.assertTrue(all(v > 0 for v in report.values()))

    def test_format_warnings_lists_unconfirmed(self):
        out = format_warnings({"company.html": 2})
        self.assertIn("警告: 【要入力】 が 2 箇所", out)
        lines = out.splitlines()
        confirm = [l for l in lines if l.startswith("要確認: ")]
        self.assertEqual(len(confirm), len(UNCONFIRMED))
        for item in UNCONFIRMED:
            self.assertIn(f"要確認: {item}", lines)
        self.assertLess(lines.index(next(l for l in lines if l.startswith("警告"))), lines.index(confirm[0]))

    def test_unconfirmed_not_rendered(self):
        for page in self.out.glob("*.html"):
            self.assertNotIn("要確認", page.read_text(encoding="utf-8"), page.name)

    def test_founding_news_placeholder_not_new_year(self):
        founding = [n for n in NEWS if n.slug == "founding"]  # tolerant: only checked if it exists
        for n in founding:
            self.assertNotEqual((n.date.month, n.date.day), (1, 1))


if __name__ == "__main__":
    unittest.main()
