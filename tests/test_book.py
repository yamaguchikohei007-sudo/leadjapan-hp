"""Book page (pm-book.html) and the reader bonus: password form and Pages Function."""
import json
import re
import shutil
import subprocess
import unittest

from tests.helpers import ROOT, build_to_tmp, collect
from sitegen.content import BOOK, BOOK_AUTHOR_BIO, BOOK_PARTS, NAV, PLACEHOLDER
from sitegen.pages import BOOK_BONUS_ACTION, body_book, body_book_bonus
from sitegen.render import esc
from sitegen.seo import book_jsonld
from tools.bonus_module import MODULE, SOURCE, module_js

FUNCTION = ROOT / "functions/pm-book-bonus/download.js"

# Fixed settings, so these tests keep passing when BOOK is updated for the release.
COMING_SOON = {"status": "coming_soon", "release_label": "近日発売", "release_date": None,
               "kindle_url": None, "paperback_url": None, "kindle_price": None, "paperback_price": None,
               "isbn": None, "x_url": None, "line_url": None, "newsletter_url": None}
ON_SALE = {**COMING_SOON, "status": "on_sale", "release_date": "2026-12-01",
           "kindle_url": "https://www.amazon.co.jp/dp/K", "paperback_url": "https://www.amazon.co.jp/dp/P",
           "kindle_price": "1250", "paperback_price": "1980"}


class BookPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build_to_tmp()
        cls.addClassCleanup(shutil.rmtree, cls.out, ignore_errors=True)

    def test_sections_in_order(self):
        b = body_book()
        ids = ["hero", "about", "for-you", "contents", "bonus", "author", "info", "notes"]
        positions = [b.index(f'id="{i}"') for i in ids]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(b.count("<h1"), 1)
        self.assertEqual(b.count('class="book-part reveal"'), len(BOOK_PARTS))

    def test_coming_soon_has_no_buy_button(self):
        b = body_book(COMING_SOON)
        self.assertNotIn("Amazonで購入する", b)
        self.assertIn("発売日が決まりしだい", b)
        self.assertIn('href="#contents"', b)

    def test_on_sale_shows_buy_button_and_known_rows(self):
        book = ON_SALE
        b = body_book(book)
        self.assertIn("好評発売中", b)
        for edition in ("K", "P"):
            self.assertIn(f'href="https://www.amazon.co.jp/dp/{edition}" target="_blank" rel="noopener"', b)
        self.assertIn("Kindle版をAmazonで見る", b)
        self.assertIn("ペーパーバックをAmazonで見る", b)
        self.assertIn("1,250円", b)
        self.assertIn("1,980円", b)
        self.assertNotIn("ISBN", b)
        self.assertNotIn('id="notify"', b)  # on sale: buy buttons instead of the release notice
        data = json.loads(re.search(r">(\{.*\})<", book_jsonld(book)).group(1))
        self.assertEqual([o["price"] for o in data["offers"]], ["1250", "1980"])
        self.assertEqual(data["datePublished"], "2026-12-01")

    def test_notify_channels_show_only_when_set(self):
        b = body_book(COMING_SOON)
        self.assertIn('id="notify"', b)
        self.assertIn("発売日が決まりしだい", b)
        for label in ("Xでフォロー", "LINEで受け取る", "メールで受け取る", "Amazonで見る"):
            self.assertNotIn(label, b)
        b = body_book({**COMING_SOON, "x_url": "https://x.com/example", "newsletter_url": "https://forms.example/n"})
        self.assertIn('href="https://x.com/example" target="_blank" rel="noopener"', b)
        self.assertIn("メールで受け取る", b)
        self.assertNotIn("LINEで受け取る", b)
        # a pre-order page may come before the release: the button shows as soon as the URL is set
        self.assertIn("Kindle版をAmazonで見る", body_book({**COMING_SOON, "kindle_url": "https://www.amazon.co.jp/dp/K"}))

    def test_no_english_section_labels(self):
        b = body_book(COMING_SOON)
        self.assertNotIn("section-label", b)
        for word in ("About", "For you", "Contents", "Bonus", "Author", "Information"):
            self.assertNotIn(f">{word}<", b)
        self.assertNotIn("READER BONUS", body_book_bonus())

    def test_badges_and_formats(self):
        from sitegen.content import BOOK_BADGES, BOOK_FORMATS
        b = body_book(COMING_SOON)
        self.assertIn("ペーパーバック", BOOK_FORMATS)
        self.assertIn(esc(BOOK_FORMATS), b)
        for badge in BOOK_BADGES:
            self.assertIn(esc(badge), b)
        for claim in ("位", "推薦", "ベストセラー"):  # only facts; rankings and endorsements once they exist
            self.assertFalse(any(claim in badge for badge in BOOK_BADGES), claim)

    def test_unknown_values_are_left_out(self):
        b = body_book(COMING_SOON)
        for word in ("発売日</th>", "価格</th>", "ISBN", PLACEHOLDER, "【"):
            self.assertNotIn(word, b)
        data = json.loads(re.search(r">(\{.*\})<", book_jsonld(COMING_SOON)).group(1))
        self.assertEqual(data["@type"], "Book")
        for key in ("offers", "isbn", "datePublished"):
            self.assertNotIn(key, data)

    def test_live_settings_render_without_placeholders(self):
        self.assertIn(BOOK["status"], ("coming_soon", "on_sale"))
        self.assertNotIn(PLACEHOLDER, body_book())

    def test_page_meta_and_links(self):
        page = (self.out / "pm-book.html").read_text(encoding="utf-8")
        self.assertIn('<meta property="og:type" content="book">', page)
        self.assertIn("/static/img/book/og_image.png", page)
        self.assertIn('<body class="layout-book">', page)
        self.assertIn('class="book-header"', page)
        self.assertNotIn('class="site-header"', page)  # landing page: no company navigation
        self.assertIn('href="/pm-book-bonus.html"', page)
        for name in ("bonus-screen-chart.webp", "bonus-screen-board.webp"):
            self.assertIn(f"/static/img/book/{name}", page)
            self.assertTrue((self.out / "static/img/book" / name).exists(), name)
        self.assertEqual(collect(self.out / "pm-book.html").jsonld, 1)
        self.assertIn('href="/pm-book.html"', (self.out / "business.html").read_text(encoding="utf-8"))
        self.assertIn(("pm-book.html", "書籍"), NAV)
        for name in ("cover_front.webp", "cover_front.png", "og_image.png"):
            self.assertTrue((self.out / "static/img/book" / name).exists(), name)

    def test_author_bio_confirmed_and_shown(self):
        # confirmed by the author on 2026-10-21, as written in the book
        from sitegen.content import UNCONFIRMED
        self.assertFalse(any("BOOK_AUTHOR_BIO" in u for u in UNCONFIRMED))
        b = body_book()
        for para in BOOK_AUTHOR_BIO:
            self.assertIn(para, b)


class BonusPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build_to_tmp()
        cls.addClassCleanup(shutil.rmtree, cls.out, ignore_errors=True)

    def test_form_posts_to_the_function(self):
        b = body_book_bonus()
        self.assertIn(f'<form class="bonus-form" method="post" action="{BOOK_BONUS_ACTION}">', b)
        self.assertIn('<label for="bonus-password">', b)
        self.assertIn('name="password" type="password" required', b)
        self.assertNotIn('role="alert"', b)
        self.assertEqual(BOOK_BONUS_ACTION, "/pm-book-bonus/download")
        self.assertTrue(FUNCTION.exists())

    def test_error_page_says_so(self):
        b = body_book_bonus(error=True)
        self.assertIn('role="alert"', b)
        self.assertIn('aria-invalid="true" aria-describedby="bonus-error"', b)

    def test_bonus_pages_not_indexed(self):
        for name in ("pm-book-bonus.html", "pm-book-bonus-error.html"):
            page = (self.out / name).read_text(encoding="utf-8")
            self.assertIn('<meta name="robots" content="noindex">', page)
            self.assertIn('<body class="layout-book">', page)
        sitemap = (self.out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn("/pm-book</loc>", sitemap)
        self.assertNotIn("pm-book-bonus", sitemap)

    def test_function_redirects_match_the_built_pages(self):
        js = (ROOT / "bonus/download.js").read_text(encoding="utf-8")
        for name in ("pm-book-bonus.html", "pm-book-bonus-error.html"):
            self.assertIn(f'"/{name}"', js)
            self.assertTrue((self.out / name).exists())

    def test_tool_is_not_on_the_public_site(self):
        self.assertFalse(list(self.out.rglob("*gantt*")))
        source = SOURCE.read_text(encoding="utf-8")
        sample = source[len(source) // 2:len(source) // 2 + 200]  # a piece of the tool's own code
        for page in self.out.rglob("*"):
            if page.is_file() and page.suffix in (".html", ".js", ".css", ".xml", ".txt", ".json"):
                self.assertNotIn(sample, page.read_text(encoding="utf-8"), page.name)

    def test_password_is_nowhere_in_the_site_or_repo(self):
        # Only a hash is kept (bonus/download.js); the book is the only place the password is given.
        for path in [*self.out.rglob("*"), *ROOT.glob("sitegen/*.py"), *ROOT.glob("bonus/*"),
                     *ROOT.rglob("functions/**/*.js"), ROOT / "README.md"]:
            if path.is_file() and path.suffix in (".html", ".js", ".py", ".md", ".xml", ".txt", ".json", ".css"):
                self.assertNotRegex(path.read_text(encoding="utf-8").lower(), "lead" + "pm", path.name)  # split so this file passes a repo-wide search too

    def test_bundled_tool_matches_source(self):
        # regenerate with: python3 tools/bonus_module.py
        self.assertEqual(MODULE.read_text(encoding="utf-8"), module_js(SOURCE.read_text(encoding="utf-8")))


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class BonusFunctionTests(unittest.TestCase):
    def test_node_tests_pass(self):
        r = subprocess.run(["node", "--test", "tests/js/bonus_download.test.mjs"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, re.compile(r"# pass [1-9]"))


if __name__ == "__main__":
    unittest.main()
