import datetime
import unittest
from pathlib import Path

from tests.helpers import ROOT
from unittest import mock

from sitegen.content import BUSINESSES, NEWS, PLACEHOLDER, PRIVACY, SITE, NewsItem
from sitegen.render import esc
from sitegen.pages import (HERO_WIDTHS, PAGES, article_page_title, body_business, body_company, body_contact, body_index,
                           body_message, body_news, body_news_article,
                           body_privacy, article_pages, news_page_filename, news_list_html, og_tags,
                           page_hero)


def _webp_size(path: Path) -> tuple[int, int]:
    """(width, height) from a lossy or lossless WebP header, stdlib only."""
    data = path.read_bytes()[:30]
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP", path
    chunk = data[12:16]
    if chunk == b"VP8 ":
        return (int.from_bytes(data[26:28], "little") & 0x3FFF,
                int.from_bytes(data[28:30], "little") & 0x3FFF)
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
    raise AssertionError(f"{path}: unknown WebP chunk {chunk!r}")


class IndexPageTests(unittest.TestCase):
    def test_index_first_and_titled(self):
        self.assertEqual(PAGES[0].filename, "index.html")
        self.assertEqual(PAGES[0].title, "Lead Japan 合同会社 | 日本を導き、世界へ。")

    def test_index_hero(self):
        b = body_index()
        self.assertIn("<h1>日本を導き、世界へ。</h1>", b)
        self.assertIn('src="/static/img/hero-tokyo.jpg"', b)
        self.assertIn('alt="東京タワーと東京の街並み"', b)
        self.assertIn("Lead Japan — Tokyo, Japan", b)

    def test_hero_webp_versions(self):
        b = body_index()
        self.assertIn('<source type="image/webp" srcset="', b)
        for w in HERO_WIDTHS:
            self.assertIn(f"/static/img/hero-tokyo-{w}.webp {w}w", b)
            path = ROOT / f"static/img/hero-tokyo-{w}.webp"
            self.assertEqual(_webp_size(path)[0], w, path.name)
            self.assertLess(path.stat().st_size, 300 * 1024)
        self.assertEqual(_webp_size(ROOT / "static/img/hero-tokyo-1920.webp"), (1920, 1278))

    def test_hero_photo_is_light_enough(self):
        photo = ROOT / "static/img/hero-tokyo.jpg"
        self.assertTrue(photo.exists())
        self.assertLess(photo.stat().st_size, 800 * 1024)

    def test_index_links_all_businesses(self):
        b = body_index()
        for biz in BUSINESSES:
            self.assertIn(f'href="/business.html#{biz.slug}"', b)

    def test_index_shows_latest_three_news(self):
        self.assertEqual(body_index().count("<li><time"), min(3, len(NEWS)))

    def test_index_has_reveal_blocks(self):
        self.assertGreaterEqual(body_index().count("reveal"), 5)

    def test_index_links_sections(self):
        b = body_index()
        for href in ("/company.html", "/message.html", "/news.html", "/contact.html"):
            self.assertIn(f'href="{href}"', b)

    def test_skyline_svg_has_tower_and_no_script(self):
        svg = (ROOT / Path("static/img/tokyo-skyline.svg")).read_text(encoding="utf-8")
        self.assertIn('id="beacon"', svg)
        self.assertNotIn("<script", svg)
        self.assertIn("#d71920", svg.lower())
        self.assertIn('viewBox="0 0 1600 600"', svg)
        self.assertLess(len(svg.encode("utf-8")), 60 * 1024)


class NewsListTests(unittest.TestCase):
    def test_news_list_markup_and_escaping(self):
        item = NewsItem("s", datetime.date(2026, 1, 5), "A&B", "<x>", "b", "<p>b</p>")
        out = news_list_html([item])
        self.assertIn('<ul class="news-list">', out)
        self.assertIn('<li><time datetime="2026-01-05">2026.01.05</time>', out)
        self.assertIn('<span class="news-cat">A&amp;B</span>', out)
        self.assertIn('<a href="/news-s.html">&lt;x&gt;</a>', out)
        self.assertNotIn("<x>", out)


def _item(**kw):
    d = dict(slug="s", date=datetime.date(2026, 1, 5), category="お知らせ", title="T",
             summary="sum", body_html="<p><strong>x</strong></p>")
    d.update(kw)
    return NewsItem(**d)


class EmptyNewsTests(unittest.TestCase):
    def test_empty_list_shows_placeholder_not_empty_ul(self):
        out = news_list_html([])
        self.assertIn("お知らせはまだありません。", out)
        self.assertNotIn("<ul", out)

    def test_news_and_home_pages_with_no_items(self):
        with mock.patch("sitegen.pages.NEWS", ()):
            for body in (body_news(), body_index()):
                self.assertIn("お知らせはまだありません。", body)
                self.assertNotIn('<ul class="news-list">', body)


class NewsListLinkTests(unittest.TestCase):
    def test_news_list_links_article_pages(self):
        item = _item()
        out = news_list_html([item], with_summary=True)
        self.assertIn('href="/news-s.html"', out)
        self.assertIn('<p class="news-summary">sum</p>', out)
        self.assertNotIn("news-summary", news_list_html([item]))


class ArticleTests(unittest.TestCase):
    def test_article_body_trusted_html_rest_escaped(self):
        out = body_news_article(_item(title="<b>", category="A&B", image="static/img/news/a.png",
                                      image_alt='"q"'))
        self.assertIn("<p><strong>x</strong></p>", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out)
        self.assertIn('<figure class="article-image"><img src="/static/img/news/a.png" alt="&quot;q&quot;"', out)
        self.assertIn('<div class="article-body">', out)
        self.assertIn('<a href="/news.html">ニュースルーム</a>', out)
        self.assertIn('href="/news.html">ニュース一覧へ戻る', out)

    def test_article_title_is_the_only_h1(self):
        out = body_news_article(_item(title="記事タイトル"))
        self.assertEqual(out.count("<h1"), 1)
        self.assertIn('<h1 class="article-title">記事タイトル</h1>', out)
        self.assertIn('<p class="page-hero-title">ニュースルーム</p>', out)

    def test_page_hero_has_h1_by_default(self):
        self.assertIn("<h1>会社紹介</h1>", page_hero("会社紹介", "COMPANY"))

    def test_article_image_src_override_and_no_image(self):
        self.assertIn('src="preview.png"', body_news_article(_item(image="a.png"), image_src="preview.png"))
        self.assertNotIn("<figure", body_news_article(_item()))

    def test_press_release_has_contact_block(self):
        out = body_news_article(_item(category="プレスリリース"))
        self.assertIn("本件に関するお問い合わせ", out)
        self.assertIn('href="/contact.html"', out)
        self.assertIn(SITE["name"], out)
        self.assertNotIn("本件に関するお問い合わせ", body_news_article(_item(category="お知らせ")))

    def test_og_tags_without_site_url(self):
        out = og_tags(_item(image="static/img/news/a.png"), "")
        self.assertIn('property="og:title" content="T"', out)
        self.assertIn('property="og:type" content="article"', out)
        self.assertIn('property="og:site_name" content="Lead Japan 合同会社"', out)
        self.assertNotIn("og:url", out)
        self.assertNotIn("og:image", out)
        self.assertNotIn("canonical", out)

    def test_og_tags_with_site_url(self):
        out = og_tags(_item(slug="founding", image="static/img/news/a.png", title="<t>"), "https://x.pages.dev/")
        # Cloudflare Pages serves news-founding.html as /news-founding
        self.assertIn('<link rel="canonical" href="https://x.pages.dev/news-founding">', out)
        self.assertIn('property="og:url" content="https://x.pages.dev/news-founding"', out)
        self.assertIn('property="og:image" content="https://x.pages.dev/static/img/news/a.png"', out)
        self.assertIn("&lt;t&gt;", out)
        self.assertIn('property="og:image" content="https://x.pages.dev/static/img/hero-tokyo.jpg"',
                      og_tags(_item(), "https://x.pages.dev"))

    def test_article_page_title_uses_site_name(self):
        with mock.patch.dict("sitegen.pages.SITE", {"name": "X社"}):
            self.assertEqual(article_page_title("T"), "T | X社")

    def test_page_hero_title_aligns_with_breadcrumb(self):
        # a flex item container shrinks and centres itself unless it is full width
        css = (ROOT / "static/css/style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.page-hero > \.container \{[^}]*width: 100%")

    def test_article_pages_metadata(self):
        pages = article_pages([_item()])
        self.assertEqual(pages[0].filename, "news-s.html")
        self.assertEqual(pages[0].title, "T | Lead Japan 合同会社")
        self.assertEqual(pages[0].description, "sum")
        self.assertEqual(pages[0].nav_current, "news.html")
        self.assertIn("og:title", pages[0].head_extra)


class SubPageTests(unittest.TestCase):
    def test_company_table_rows(self):
        b = body_company()
        for th in ("商号", "英文社名", "設立", "代表者", "所在地", "事業内容"):
            self.assertIn(f'<th scope="row">{th}</th>', b)
        self.assertIn("Lead Japan 合同会社", b)

    def test_business_sections_have_ids(self):
        b = body_business()
        for biz in BUSINESSES:
            self.assertIn(f'id="{biz.slug}"', b)
        self.assertIn("スタートアップ向け業務システムの開発", b)

    def test_business_text_is_escaped(self):
        from unittest import mock
        evil = BUSINESSES[0].__class__("ai", "01", "<b>X</b>", "E", "s&t", ("d",))
        with mock.patch("sitegen.pages.BUSINESSES", (evil,)):
            b = body_business()
        self.assertIn("&lt;b&gt;X&lt;/b&gt;", b)
        self.assertIn("s&amp;t", b)

    def test_message_has_signature(self):
        self.assertIn("代表社員", body_message())

    def test_subpages_have_breadcrumb(self):
        for fn in (body_company, body_business, body_message):
            self.assertIn('aria-label="パンくずリスト"', fn())

    def test_pages_registered_in_order(self):
        self.assertEqual([p.filename for p in PAGES[:4]],
                         ["index.html", "company.html", "business.html", "message.html"])
        self.assertEqual(PAGES[1].title, "会社紹介 | Lead Japan 合同会社")

    def test_page_hero_escapes(self):
        self.assertIn("&lt;", page_hero("<", "X"))


class NewsPrivacyContactTests(unittest.TestCase):
    def test_news_page_lists_summaries_and_article_links(self):
        b = body_news()
        for item in NEWS:
            self.assertIn(f'href="/news-{item.slug}.html"', b)
            self.assertIn(esc(item.summary), b)
        self.assertNotIn('href="news.html#', b)

    def test_privacy_sections(self):
        b = body_privacy()
        for heading, _ in PRIVACY:
            self.assertIn(heading, b)
        self.assertIn("制定日：2026年10月19日", b)

    def test_privacy_links_to_contact_page(self):
        self.assertIn('<a href="/contact.html">お問い合わせページ</a>', body_privacy())

    def test_privacy_enactment_date_once(self):
        self.assertEqual(body_privacy().count("制定日"), 1)

    def test_privacy_contact_section_names_operator(self):
        text = " ".join(dict(PRIVACY)["お問い合わせ窓口"])
        for key in ("name", "address", "representative", "email"):
            self.assertIn(SITE[key], text)
        self.assertIn("お問い合わせページ", text)

    def test_contact_note_matches_privacy_purpose(self):
        self.assertIn("プライバシーポリシーに定める利用目的の範囲内で", body_contact())

    def test_contact_no_form_post(self):
        b = body_contact()
        self.assertNotIn("<form", b)
        self.assertIn('href="/privacy.html"', b)

    def test_contact_placeholder_email_not_mailto(self):
        with mock.patch.dict("sitegen.pages.SITE", {"email": PLACEHOLDER}):
            self.assertNotIn("mailto:", body_contact())
        with mock.patch.dict("sitegen.pages.SITE", {"email": "info@example.jp"}):
            self.assertIn('href="mailto:info@example.jp"', body_contact())

    def test_all_pages_registered(self):
        self.assertEqual([p.filename for p in PAGES],
                         ["index.html", "company.html", "business.html", "message.html",
                          "news.html", "privacy.html", "contact.html", "404.html"]
                         + [news_page_filename(n) for n in NEWS])


if __name__ == "__main__":
    unittest.main()
