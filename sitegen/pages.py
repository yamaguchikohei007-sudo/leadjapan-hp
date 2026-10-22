"""Page registry. PAGES is filled by later tasks."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Callable, Sequence

from sitegen.content import (
    BOOK, BOOK_ABOUT, BOOK_AUTHOR, BOOK_AUTHOR_BIO, BOOK_AUTHOR_NAME, BOOK_BADGES, BOOK_BONUS_ERROR,
    BOOK_BONUS_FEATURES, BOOK_BONUS_HOWTO, BOOK_BONUS_INTRO, BOOK_BONUS_TEXT, BOOK_BONUS_TITLE, BOOK_CATCH,
    BOOK_CLOSING_TITLE, BOOK_COLUMNS, BOOK_COLUMNS_LEAD, BOOK_COMING_SOON_NOTE, BOOK_COVER_ALT, BOOK_FORMATS,
    BOOK_FOR_YOU, BOOK_LEAD, BOOK_NOTIFY_TEXT, BOOK_NOTIFY_TITLE, BOOK_OG_DESCRIPTION, BOOK_PARTS, BOOK_SUBTITLE,
    BOOK_TITLE, BOOK_TRADEMARK_NOTE, ABOUT_LEAD, ABOUT_TEXT, BUSINESSES, COMPANY_NAME_ORIGIN, CONTACT_CATEGORIES, CONTACT_HOURS, CONTACT_INTRO, CTA_LEAD,
    HERO_LEAD, HERO_SUB, MESSAGE, MESSAGE_EXCERPT, MESSAGE_TITLE, NEWS, NOT_FOUND_TEXT, PAGE_META, PLACEHOLDER,
    PRIVACY, PRIVACY_ENACTED, SECTION_DISPLAY, SITE, SITE_URL, NewsItem,
)
from sitegen.geo import MAP_HEIGHT, MAP_WIDTH, pin_xy
from sitegen.render import esc, url
from sitegen.seo import book_jsonld, head_meta, organization_jsonld


@dataclass(frozen=True)
class Page:
    filename: str
    title: str
    description: str
    body: Callable[[], str]
    nav_current: str | None = None
    head_extra: str = ""
    indexable: bool = True  # listed in sitemap.xml
    lastmod: datetime.date | None = None
    layout: str = "site"  # "book": the book's landing-page header and footer (sitegen/render.py)


def news_page_filename(item: NewsItem) -> str:
    return f"news-{item.slug}.html"


def news_list_html(items: Sequence[NewsItem], *, with_summary: bool = False) -> str:
    if not items:
        return '<p class="news-empty">お知らせはまだありません。</p>'
    rows = []
    for item in items:
        summary = f'<p class="news-summary">{esc(item.summary)}</p>' if with_summary else ""
        rows.append(
            f'<li><time datetime="{item.date:%Y-%m-%d}">{item.date:%Y.%m.%d}</time>'
            f'<span class="news-cat">{esc(item.category)}</span>'
            f'<a href="{esc(url(news_page_filename(item)))}">{esc(item.title)}</a>{summary}</li>'
        )
    return '<ul class="news-list">\n' + "\n".join(rows) + "\n</ul>"


def _section_head(label: str, title: str, extra: str = "", display: str = "") -> str:
    """display: optional large English heading shown between the label and the title."""
    display_html = f'<p class="section-display" lang="en">{esc(display)}</p>' if display else ""
    return (
        f'<div class="section-head reveal{extra}">'
        f'<span class="section-label">{esc(label)}</span>'
        f"{display_html}"
        f'<h2 class="section-title">{esc(title)}</h2>'
        "</div>"
    )


def _more_link(href: str, label: str) -> str:
    return f'<a class="link-more" href="{esc(href)}">{esc(label)}</a>'


def _hero_map() -> str:
    """Map of Japan and the visitor's dot. The dot starts on Tokyo; on Cloudflare,
    functions/index.js moves it (data-visitor-pin) to the visitor's prefecture."""
    x, y = pin_xy()
    return (
        '<div class="hero-map" aria-hidden="true">'
        f'<img src="/static/img/japan-map.svg" alt="" width="{MAP_WIDTH}" height="{MAP_HEIGHT}" fetchpriority="high">'
        f'<svg class="hero-pin" viewBox="0 0 {MAP_WIDTH} {MAP_HEIGHT}" focusable="false">'
        f'<g data-visitor-pin transform="translate({x} {y})">'
        '<circle class="pin-wave" r="20"/><circle class="pin-dot" r="6"/></g></svg>'
        "</div>"
    )


def body_index() -> str:
    cards = "\n".join(
        f'<a class="biz-card reveal" style="--d: {i}" href="/business.html#{esc(b.slug)}">'
        f'<span class="biz-card-top"><span class="biz-icon-wrap">{ICONS.get(b.slug, "")}</span>'
        f'<span class="biz-num">{esc(b.number)}</span></span>'
        f'<span class="biz-en" lang="en">{esc(b.title_en)}</span>'
        f'<h3 class="biz-title">{esc(b.title)}</h3>'
        f'<p class="biz-summary">{esc(b.summary)}</p>'
        f'<span class="biz-more">詳しく見る</span>'
        "</a>"
        for i, b in enumerate(BUSINESSES)
    )
    band = "".join(
        f'<li><a href="/business.html#{esc(b.slug)}"><span class="hero-band-num">{esc(b.number)}</span>'
        f"{esc(b.title.removesuffix('の展開'))}</a></li>"
        for b in BUSINESSES
    )
    facts = (
        ("設立", SITE["founded"][:4]),
        ("事業領域", str(len(BUSINESSES))),
        ("拠点", "Tokyo"),
    )
    facts_html = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in facts)
    contact_cats = "".join(f"<li>{esc(c)}</li>" for c in CONTACT_CATEGORIES)
    return f"""<section class="section hero">
<div class="hero-grid" aria-hidden="true"></div>
{_hero_map()}
<p class="hero-word" aria-hidden="true">LEAD JAPAN</p>
<div class="container hero-inner">
<p class="hero-kicker reveal">{esc(HERO_SUB)}</p>
<h1><span>日本を導き、</span><span class="hero-accent">世界へ。</span></h1>
<p class="hero-sub reveal" style="--d: 1">{esc(HERO_LEAD)}</p>
<p class="hero-actions"><a class="btn btn-light" href="/business.html">事業を見る</a><a class="btn btn-outline-light" href="/contact.html">お問い合わせ</a></p>
</div>
<nav class="hero-band" aria-label="事業"><ul class="container">{band}</ul></nav>
</section>

<section class="section top-about" id="about">
<div class="container about-grid">
{_section_head("About", "会社紹介", " reveal--left", SECTION_DISPLAY["about"])}
<div class="about-body reveal" style="--d: 1">
<p class="about-lead">{esc(ABOUT_LEAD)}</p>
<p>{esc(ABOUT_TEXT)}</p>
{_more_link("/company.html", "会社紹介を見る")}
<dl class="about-facts">{facts_html}</dl>
</div>
</div>
</section>

<section class="section alt top-business" id="business">
<div class="container">
<div class="head-row">
{_section_head("Business", "事業概要", display=SECTION_DISPLAY["business"])}
{_more_link("/business.html", "事業概要を見る")}
</div>
<div class="biz-grid">
{cards}
</div>
</div>
</section>

<section class="section section-dark top-message" id="message">
<div class="container message-grid">
{_section_head("Message", "代表挨拶", " reveal--left", SECTION_DISPLAY["message"])}
<div class="reveal" style="--d: 1">
<blockquote class="message-excerpt"><p>{esc(MESSAGE_EXCERPT)}</p></blockquote>
<p class="message-sign">{esc(SITE["name"])} 代表社員 <strong>{esc(SITE["representative"])}</strong></p>
<a class="btn btn-outline-light" href="/message.html">代表挨拶を読む</a>
</div>
</div>
</section>

<section class="section top-news" id="news">
<div class="container">
<div class="head-row">
{_section_head("News", "ニュースルーム", display=SECTION_DISPLAY["news"])}
{_more_link("/news.html", "ニュース一覧へ")}
</div>
<div class="news-body reveal" style="--d: 1">
{news_list_html(NEWS[:3])}
</div>
</div>
</section>

<section class="section alt cta-band" id="contact">
<div class="container">
<div class="cta-card reveal">
<div class="cta-main">
<span class="section-label">Contact</span>
<p class="section-display" lang="en">{esc(SECTION_DISPLAY["contact"])}</p>
<h2 class="section-title">お問い合わせ</h2>
<p class="cta-lead">{esc(CTA_LEAD)}</p>
<ul class="cta-tags">{contact_cats}</ul>
</div>
<div class="cta-box">
<dl><dt>受付時間</dt><dd>{esc(CONTACT_HOURS)}</dd><dt>所在地</dt><dd>{esc(SITE["address"])}</dd></dl>
<a class="btn btn-light btn-block" href="/contact.html">お問い合わせはこちら</a>
</div>
</div>
</div>
</section>"""


def page_hero(
    title: str, label_en: str, crumbs: Sequence[tuple[str, str | None]] | None = None,
    *, heading: bool = True,
) -> str:
    """crumbs: (label, href-or-None) after ホーム; default is just the page title.
    heading=False when the page's own <h1> is further down (news articles)."""
    trail = crumbs if crumbs is not None else [(title, None)]
    parts = ['<a href="/">ホーム</a>']
    for label, href in trail:
        parts.append(f'<a href="{esc(url(href))}">{esc(label)}</a>' if href else f"<span>{esc(label)}</span>")
    title_html = f"<h1>{esc(title)}</h1>" if heading else f'<p class="page-hero-title">{esc(title)}</p>'
    return (
        '<section class="page-hero"><div class="container">'
        f'<span class="section-label">{esc(label_en)}</span>'
        f"{title_html}"
        "</div></section>\n"
        '<div class="container"><nav class="breadcrumb" aria-label="パンくずリスト">'
        + " / ".join(parts)
        + "</nav></div>"
    )


_SVG = (
    '<svg class="biz-icon" viewBox="0 0 120 120" width="120" height="120" aria-hidden="true" '
    'fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
)

ICONS: dict[str, str] = {
    "ai": _SVG
    + '<circle cx="60" cy="22" r="9"/><circle cx="24" cy="60" r="9"/><circle cx="96" cy="60" r="9"/>'
    '<circle cx="42" cy="98" r="9"/><circle cx="78" cy="98" r="9"/><circle cx="60" cy="60" r="7"/>'
    '<path d="M54 29 29 52M66 29l25 23M33 60h20M67 60h20M56 66 46 90M64 66l10 24M51 98h18"/></svg>',
    "consulting": _SVG
    + '<circle cx="60" cy="60" r="44"/><circle cx="60" cy="60" r="4"/>'
    '<path d="m82 38-12 28-28 16 12-28z"/><path d="M60 10v8M60 102v8M10 60h8M102 60h8"/></svg>',
    "system": _SVG
    + '<rect x="14" y="14" width="64" height="46" rx="3"/><path d="M14 26h64"/>'
    '<rect x="34" y="40" width="64" height="46" rx="3"/><path d="M34 52h64"/>'
    '<rect x="54" y="66" width="52" height="40" rx="3"/><path d="M54 78h52"/></svg>',
    "publishing": _SVG
    + '<path d="M60 36C48 26 30 24 12 28v62c18-4 36-2 48 8 12-10 30-12 48-8V28c-18-4-36-2-48 8z"/>'
    '<path d="M60 36v62M24 46c10-2 22 0 28 5M24 62c10-2 22 0 28 5M96 46c-10-2-22 0-28 5M96 62c-10-2-22 0-28 5"/></svg>',
}


def body_company() -> str:
    name_origin = "\n".join(f"<p>{esc(p)}</p>" for p in COMPANY_NAME_ORIGIN)
    biz_list = "<ul>" + "".join(f"<li>{esc(b.title)}</li>" for b in BUSINESSES) + "</ul>"
    rows = [
        ("商号", esc(SITE["name"])),
        ("英文社名", esc(SITE["name_en"])),
        ("設立", esc(SITE["founded"])),
        ("代表者", esc(SITE["representative"])),
        ("所在地", esc(SITE["address"])),
        ("事業内容", biz_list),
        ("現況", esc(SITE["status"])),
    ]
    table = "\n".join(f'<tr><th scope="row">{th}</th><td>{td}</td></tr>' for th, td in rows)
    return f"""{page_hero("会社紹介", "COMPANY")}
<section class="section">
<div class="container">
{_section_head("Philosophy", "企業理念")}
<blockquote class="philosophy reveal reveal--zoom"><p>{esc(SITE["philosophy"])}</p></blockquote>
</div>
</section>

<section class="section alt">
<div class="container name-origin">
{_section_head("Name", "社名の由来", " reveal--left")}
<div class="reveal reveal--right" style="--d: 1">
{name_origin}
</div>
</div>
</section>

<section class="section">
<div class="container">
{_section_head("Profile", "会社概要")}
<table class="company-table reveal">
{table}
</table>
</div>
</section>"""


def body_business() -> str:
    items = []
    for i, b in enumerate(BUSINESSES):
        side = "reveal--left" if i % 2 == 0 else "reveal--right"
        details = "".join(f"<li>{esc(d)}</li>" for d in b.details)
        icon = ICONS.get(b.slug, "")
        items.append(
            f'<section id="{esc(b.slug)}" class="business-item reveal {side}">\n'
            f'<div class="business-visual">{icon}</div>\n'
            '<div class="business-text">'
            f'<span class="biz-num">{esc(b.number)}</span>'
            f'<h2>{esc(b.title)}</h2>'
            f'<span class="biz-en">{esc(b.title_en)}</span>'
            f'<p>{esc(b.summary)}</p>'
            f'<ul>{details}</ul>'
            + (_more_link("/pm-book.html", "書籍の紹介を見る") if b.slug == "publishing" else "")
            + "</div>\n</section>"
        )
    return f"""{page_hero("事業概要", "BUSINESS")}
<div class="container business-list">
{chr(10).join(items)}
</div>"""


def body_message() -> str:
    paras = "\n".join(f"<p>{esc(p)}</p>" for p in MESSAGE)
    return f"""{page_hero("代表挨拶", "MESSAGE")}
<section class="section">
<div class="container message-layout">
<aside class="message-side reveal reveal--left" aria-hidden="true">
<img src="/static/img/tokyo-skyline.svg" alt="" width="1600" height="600">
</aside>
<article class="message-body reveal reveal--right" style="--d: 1">
<h2>{esc(MESSAGE_TITLE)}</h2>
{paras}
<p class="signature"><span>{esc(SITE["name"])}</span> 代表社員 <strong>{esc(SITE["representative"])}</strong></p>
</article>
</div>
</section>"""


def body_news() -> str:
    return f"""{page_hero("ニュースルーム", "NEWSROOM")}
<section class="section">
<div class="container news-articles">
{news_list_html(NEWS, with_summary=True)}
</div>
</section>"""


def body_news_article(item: NewsItem, *, image_src: str | None = None) -> str:
    src = image_src if image_src is not None else (url(item.image) if item.image else None)
    figure = (
        f'<figure class="article-image"><img src="{esc(src)}" alt="{esc(item.image_alt)}"></figure>\n'
        if src
        else ""
    )
    contact = ""
    if item.category == "プレスリリース":
        contact = (
            '<aside class="press-contact">\n'
            "<h3>本件に関するお問い合わせ</h3>\n"
            f'<p>{esc(SITE["name"])}<br><a href="/contact.html">お問い合わせページ</a></p>\n'
            "</aside>\n"
        )
    crumbs = [("ニュースルーム", "news.html"), (item.title, None)]
    return f"""{page_hero("ニュースルーム", "NEWSROOM", crumbs, heading=False)}
<section class="section">
<div class="container news-articles">
<article class="news-article">
<div class="news-meta"><time datetime="{item.date:%Y-%m-%d}">{item.date:%Y.%m.%d}</time><span class="news-cat">{esc(item.category)}</span></div>
<h1 class="article-title">{esc(item.title)}</h1>
{figure}<div class="article-body">{item.body_html}</div>
{contact}</article>
<p class="article-back"><a href="/news.html">ニュース一覧へ戻る</a></p>
</div>
</section>"""


def og_tags(item: NewsItem, site_url: str) -> str:
    return head_meta(filename=news_page_filename(item), title=item.title, description=item.summary,
                     og_type="article", image=item.image, site_url=site_url)


CONTACT_LABEL = "お問い合わせページ"
CONTACT_LINK = f'<a href="/contact.html">{CONTACT_LABEL}</a>'


def body_privacy() -> str:
    sections = []
    for n, (heading, paras) in enumerate(PRIVACY, start=1):
        # Only the contact-page pointer becomes a link; all text stays escaped.
        body = "".join(
            f"<p>{esc(p).replace(CONTACT_LABEL, CONTACT_LINK)}</p>" for p in paras
        )
        sections.append(f"<section>\n<h2>第{n}条　{esc(heading)}</h2>\n{body}\n</section>")
    return f"""{page_hero("プライバシーポリシー", "PRIVACY POLICY")}
<section class="section">
<div class="container policy reveal">
{chr(10).join(sections)}
<p class="policy-sign">制定日：{esc(PRIVACY_ENACTED)}<br>{esc(SITE["name"])} 代表社員 {esc(SITE["representative"])}</p>
</div>
</section>"""


def body_contact() -> str:
    email = SITE["email"]
    if email == PLACEHOLDER:
        email_html = esc(email)
    else:
        email_html = f'<a href="mailto:{esc(email)}">{esc(email)}</a>'
    categories = "".join(
        f"<li>{esc(c)}</li>" for c in CONTACT_CATEGORIES
    )
    btn = (
        f'<a class="btn" href="mailto:{esc(email)}">メールで問い合わせる</a>'
        if email != PLACEHOLDER
        else '<span class="btn is-disabled" aria-disabled="true">メールで問い合わせる</span>'
    )
    return f"""{page_hero("お問い合わせ", "CONTACT")}
<section class="section">
<div class="container contact reveal">
<p>{esc(CONTACT_INTRO)}</p>
<dl class="contact-info">
<dt>メール</dt><dd>{email_html}</dd>
<dt>所在地</dt><dd>{esc(SITE["address"])}</dd>
<dt>受付時間</dt><dd>{esc(CONTACT_HOURS)}</dd>
</dl>
<p>{btn}</p>
<!-- 無料の Google フォームを使う場合はここに埋め込みリンクを置く -->
<h2 class="contact-sub">お問い合わせの例</h2>
<ul class="contact-cats">{categories}</ul>
<p class="contact-note">お預かりした個人情報は、プライバシーポリシーに定める利用目的の範囲内で利用します。詳しくは<a href="/privacy.html">プライバシーポリシー</a>をご確認ください。</p>
</div>
</section>"""


BOOK_BONUS_ACTION = "/pm-book-bonus/download"  # functions/pm-book-bonus/download.js


def _book_head(title: str, lead: str = "") -> str:
    """Section heading on the book page: Japanese only, with a short yellow rule (no English label)."""
    lead_html = f'<p class="book-head-lead">{esc(lead)}</p>' if lead else ""
    return f'<div class="book-head reveal"><h2>{esc(title)}</h2>{lead_html}</div>'


_ICON = ('<svg class="icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" '
         'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">')
BOOK_ICONS: dict[str, str] = {
    "x": '<svg class="icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false" '
         'fill="currentColor"><path d="M17.8 3h3.1l-6.8 7.8L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.3-8.3L2 3h6.4l4.4 5.8L17.8 3Zm-1.1 16.2h1.7L7.4 4.7H5.6l11.1 14.5Z"/></svg>',
    "line": _ICON + '<path d="M21 11c0-4.4-4-8-9-8s-9 3.6-9 8c0 4 3.2 7.3 7.6 7.9.3.1.7.2.8.5l-.2 1.9c0 .4.3.6.6.4 2.6-1.4 6.4-4.2 8-6.6.8-1.2 1.2-2.6 1.2-4.1Z"/></svg>',
    "mail": _ICON + '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "cart": _ICON + '<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2 3h3l2.6 12.2a2 2 0 0 0 2 1.6h7.9a2 2 0 0 0 2-1.5L21 8H6"/></svg>',
    "check": _ICON + '<path d="m5 12 5 5L20 7"/></svg>',
    "browser": _ICON + '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10 6.5h.01"/></svg>',
    "lock": _ICON + '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
    "chart": _ICON + '<path d="M4 6h9M8 12h10M6 18h7"/><path d="M4 3v18"/></svg>',
}
BONUS_FEATURE_ICONS = ("browser", "lock", "chart")

# (BOOK key, label, icon)
BUY_LINKS = (("kindle_url", "Kindle版をAmazonで見る"), ("paperback_url", "ペーパーバックをAmazonで見る"))
NOTIFY_LINKS = (("x_url", "Xでフォロー", "x"), ("line_url", "LINEで受け取る", "line"),
                ("newsletter_url", "メールで受け取る", "mail"))


def _buy_buttons(book: dict[str, str | None], extra_class: str = "") -> str:
    links = [
        f'<a class="btn book-btn{extra_class}" href="{esc(book[key])}" target="_blank" rel="noopener">'
        f'{BOOK_ICONS["cart"]}{esc(label)}</a>'
        for key, label in BUY_LINKS if book.get(key)
    ]
    return f'<div class="book-buy">{"".join(links)}</div>' if links else ""


def _notify_panel(book: dict[str, str | None], *, panel_id: str = "") -> str:
    """Where to hear about the release. Channels without a URL are left out; with none, a note."""
    links = "".join(
        f'<a class="book-notify-btn" href="{esc(book[key])}" target="_blank" rel="noopener">'
        f'{BOOK_ICONS[icon]}{esc(label)}</a>'
        for key, label, icon in NOTIFY_LINKS if book.get(key)
    )
    id_attr = f' id="{panel_id}"' if panel_id else ""
    body = (f'<p class="book-notify-text">{esc(BOOK_NOTIFY_TEXT)}</p><div class="book-notify-links">{links}</div>'
            if links else f'<p class="book-notify-text">{esc(BOOK_COMING_SOON_NOTE)}</p>')
    return f'<div class="book-notify"{id_attr}><p class="book-notify-title">{esc(BOOK_NOTIFY_TITLE)}</p>{body}</div>'


def _book_actions(book: dict[str, str | None], *, panel_id: str = "") -> str:
    """Buy buttons once there is a product page; the release notice while it is coming soon."""
    actions = _buy_buttons(book)
    if book["status"] != "on_sale":
        actions += _notify_panel(book, panel_id=panel_id)
    return actions


def _price(value: str | None) -> str | None:
    return f"{int(value):,}円（税込）" if value else None


def body_book(book: dict[str, str | None] = BOOK) -> str:
    on_sale = book["status"] == "on_sale"
    label = "好評発売中" if on_sale else book["release_label"]
    badges = "".join(f"<li>{esc(b)}</li>" for b in BOOK_BADGES)
    about = "\n".join(f"<p>{esc(p)}</p>" for p in BOOK_ABOUT)
    for_you = "".join(f'<li class="reveal" style="--d: {i}">{BOOK_ICONS["check"]}<span>{esc(t)}</span></li>'
                      for i, t in enumerate(BOOK_FOR_YOU))
    parts = "\n".join(
        f'<article class="book-part reveal" style="--d: {i % 2}">'
        f'<div class="book-part-top"><span class="book-part-label">{esc(part.label)}</span>'
        f'<p class="book-part-count" aria-hidden="true"><span>{esc(part.count)}</span>{esc(part.count_unit)}</p></div>'
        f'<h3>{esc(part.title)}</h3>'
        f'<p class="book-part-summary">{esc(part.summary)}</p>'
        + (f'<p class="book-part-note">{esc(part.note)}</p>' if part.note else "")
        + '<ul class="book-part-list">'
        + "".join(f'<li>{BOOK_ICONS["check"]}<span>{esc(h)}</span></li>' for h in part.headings)
        + "</ul></article>"
        for i, part in enumerate(BOOK_PARTS)
    )
    columns = "".join(f"<li>{esc(c)}</li>" for c in BOOK_COLUMNS)
    bonus = "\n".join(f"<p>{esc(p)}</p>" for p in BOOK_BONUS_TEXT)
    features = "".join(
        f'<li>{BOOK_ICONS[icon]}<div><strong>{esc(title)}</strong><span>{esc(text)}</span></div></li>'
        for (title, text), icon in zip(BOOK_BONUS_FEATURES, BONUS_FEATURE_ICONS)
    )
    bio = "\n".join(f"<p>{esc(p)}</p>" for p in BOOK_AUTHOR_BIO)
    buy_links = " ／ ".join(
        f'<a href="{esc(book[key])}" target="_blank" rel="noopener">{esc(label.removesuffix("をAmazonで見る"))}（Amazon）</a>'
        for key, label in BUY_LINKS if book.get(key)
    )
    rows = [
        ("書名", esc(BOOK_TITLE)),
        ("副題", esc(BOOK_SUBTITLE)),
        ("著者", esc(BOOK_AUTHOR)),
        ("発行・発売", esc(SITE["name"])),
        ("形態", esc(BOOK_FORMATS)),
        ("発売日", esc(book["release_date"]) if book.get("release_date") else None),
        ("価格（Kindle版）", esc(_price(book.get("kindle_price"))) if book.get("kindle_price") else None),
        ("価格（ペーパーバック）", esc(_price(book.get("paperback_price"))) if book.get("paperback_price") else None),
        ("ISBN", esc(book["isbn"]) if book.get("isbn") else None),
        ("購入", buy_links or None),
    ]
    info = "\n".join(f'<tr><th scope="row">{k}</th><td>{v}</td></tr>' for k, v in rows if v)
    return f"""<section class="book-hero" id="hero">
<div class="container book-hero-inner">
<div class="book-cover-wrap">
<picture class="book-cover">
<source srcset="/static/img/book/cover_front.webp" type="image/webp">
<img src="/static/img/book/cover_front.png" alt="{esc(BOOK_COVER_ALT)}" width="1000" height="1422" fetchpriority="high">
</picture>
<p class="book-seal">{esc(label)}</p>
</div>
<div class="book-hero-text">
<h1 class="book-title"><span>外資系プロジェクトマネージャー</span><span class="book-title-main">1年目の教科書</span></h1>
<p class="book-subtitle">{esc(BOOK_SUBTITLE)}</p>
<p class="book-author">{esc(BOOK_AUTHOR)} 著<span class="book-format">{esc(BOOK_FORMATS)}</span></p>
<p class="book-catch">{esc(BOOK_CATCH)}</p>
<p class="book-lead">{esc(BOOK_LEAD)}</p>
<ul class="book-badges" aria-label="この本の特長">{badges}</ul>
{_book_actions(book, panel_id="notify")}
<p class="book-more"><a href="#contents">本書の構成を見る</a></p>
</div>
</div>
</section>

<section class="book-section" id="about">
<div class="container book-narrow">
{_book_head("この本について")}
<div class="book-prose reveal">
{about}
</div>
</div>
</section>

<section class="book-section book-section-tint" id="for-you">
<div class="container book-narrow">
{_book_head("こんな方におすすめです")}
<ul class="book-checklist">{for_you}</ul>
</div>
</section>

<section class="book-section" id="contents">
<div class="container book-narrow">
{_book_head("本書の構成", "現場で使う「ルール」と、共通言語としての「知識」の二本立てです。")}
<div class="book-parts">
{parts}
</div>
<div class="book-columns reveal"><p>{esc(BOOK_COLUMNS_LEAD)}</p><ul>{columns}</ul></div>
</div>
</section>

<section class="book-section book-section-tint" id="bonus">
<div class="container book-narrow">
{_book_head(f"読者特典　{BOOK_BONUS_TITLE}")}
<div class="book-bonus">
<div class="book-bonus-text reveal">
{bonus}
<ul class="book-bonus-features">{features}</ul>
<p><a class="btn book-btn book-btn-large" href="/pm-book-bonus.html">特典ページへ</a></p>
</div>
<figure class="book-bonus-shots reveal" style="--d: 1">
<img class="shot-main" src="/static/img/book/bonus-screen-chart.webp" alt="特典ツールのガントチャート画面。タスクの期間、依存関係、進み具合が表示されている" width="1280" height="760" loading="lazy">
<img class="shot-sub" src="/static/img/book/bonus-screen-board.webp" alt="特典ツールのかんばん画面。未着手・進行中・完了の列にタスクが並んでいる" width="1280" height="470" loading="lazy">
<figcaption>サンプルデータを入れた実際の画面</figcaption>
</figure>
</div>
</div>
</section>

<section class="book-section" id="author">
<div class="container book-narrow">
{_book_head("著者紹介")}
<div class="book-author-card reveal">
<p class="book-author-name">{esc(BOOK_AUTHOR_NAME)}</p>
{bio}
</div>
</div>
</section>

<section class="book-section book-section-tint" id="info">
<div class="container book-narrow">
{_book_head("書籍情報")}
<div class="book-info reveal">
<table class="book-info-table">
{info}
</table>
</div>
</div>
</section>

<section class="book-closing">
<div class="container book-narrow book-closing-inner">
<p class="book-closing-label">{esc(label)}</p>
<h2>{esc(BOOK_CLOSING_TITLE)}</h2>
{_book_actions(book)}
<p class="book-closing-bonus">読者特典の<a href="/pm-book-bonus.html">ガントチャート作成ツール</a>もご用意しています。</p>
<p class="book-notes" id="notes">{esc(BOOK_TRADEMARK_NOTE)}</p>
</div>
</section>"""


def body_book_bonus(*, error: bool = False) -> str:
    """Password form for the reader bonus. The form posts to a Pages Function, which
    sends the file or redirects to the error version of this page (no JavaScript)."""
    alert = (
        f'<p class="bonus-error" id="bonus-error" role="alert">{esc(BOOK_BONUS_ERROR)}</p>\n' if error else ""
    )
    invalid = ' aria-invalid="true" aria-describedby="bonus-error"' if error else ""
    howto = "".join(f"<li>{esc(t)}</li>" for t in BOOK_BONUS_HOWTO)
    return f"""<section class="page-hero"><div class="container"><h1>読者特典</h1></div></section>
<div class="container"><nav class="breadcrumb" aria-label="パンくずリスト"><a href="/pm-book.html">書籍トップ</a> / <span>読者特典</span></nav></div>
<section class="section">
<div class="container book-narrow">
<div class="bonus-card reveal">
<p class="bonus-book">『{esc(BOOK_TITLE)}』</p>
<h2 class="bonus-title">{esc(BOOK_BONUS_TITLE)}</h2>
<p>{esc(BOOK_BONUS_INTRO)}</p>
{alert}<form class="bonus-form" method="post" action="{BOOK_BONUS_ACTION}">
<label for="bonus-password">読者パスワード</label>
<div class="bonus-row">
<input id="bonus-password" name="password" type="password" required maxlength="64" autocomplete="off" autocapitalize="off" spellcheck="false"{invalid}>
<button class="btn" type="submit">ダウンロード</button>
</div>
</form>
<h3 class="bonus-sub">ご利用にあたって</h3>
<ul class="bonus-howto">{howto}</ul>
</div>
<p class="article-back"><a href="/pm-book.html">書籍の紹介へ戻る</a></p>
</div>
</section>"""


def body_404() -> str:
    return f"""{page_hero("ページが見つかりません", "404 NOT FOUND")}
<section class="section">
<div class="container">
<p>{esc(NOT_FOUND_TEXT)}</p>
<p><a class="btn" href="/">トップページへ戻る</a></p>
</div>
</section>"""


_BODIES: dict[str, Callable[[], str]] = {
    "index.html": body_index,
    "company.html": body_company,
    "business.html": body_business,
    "message.html": body_message,
    "news.html": body_news,
    "privacy.html": body_privacy,
    "contact.html": body_contact,
    "pm-book.html": body_book,
    "pm-book-bonus.html": body_book_bonus,
    "pm-book-bonus-error.html": lambda: body_book_bonus(error=True),
    "404.html": body_404,
}

# Reader-bonus pages: only for readers of the book, so kept out of search results.
NOINDEX = ("404.html", "pm-book-bonus.html", "pm-book-bonus-error.html")

def _fixed_page(name: str, body: Callable[[], str]) -> Page:
    title, description = PAGE_META[name]
    book = name.startswith("pm-book")  # the book's landing page and its reader-bonus pages
    current = "pm-book.html" if book else None
    layout = "book" if book else "site"
    if name in NOINDEX:
        # 404 is served for any missing URL: keep it (and the bonus pages) out of search results and the sitemap.
        return Page(name, title, description, body, nav_current=current,
                    head_extra='<meta name="robots" content="noindex">', indexable=False, layout=layout)
    if name == "pm-book.html":
        head = head_meta(filename=name, title=BOOK_TITLE, description=BOOK_OG_DESCRIPTION, og_type="book",
                         image="static/img/book/og_image.png")
        return Page(name, title, description, body, nav_current=current, head_extra=head + "\n" + book_jsonld(),
                    layout=layout)
    head = head_meta(filename=name, title=title, description=description)
    if name == "index.html":
        head += "\n" + organization_jsonld()
    return Page(name, title, description, body, head_extra=head)


PAGES: list[Page] = [_fixed_page(name, body) for name, body in _BODIES.items()]


def article_page_title(title: str) -> str:
    """<title> of a news article page (also used by the admin preview and its checks)."""
    return f"{title} | {SITE['name']}"


def article_pages(items: Sequence[NewsItem] | None = None) -> list[Page]:
    """One Page per news item. Reads NEWS at call time when items is None."""
    items = NEWS if items is None else items
    return [
        Page(
            filename=news_page_filename(item),
            title=article_page_title(item.title),
            description=item.summary,
            body=lambda item=item: body_news_article(item),
            nav_current="news.html",
            head_extra=og_tags(item, SITE_URL),
            lastmod=item.date,
        )
        for item in items
    ]


PAGES.extend(article_pages())
