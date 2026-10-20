"""Page registry. PAGES is filled by later tasks."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Callable, Sequence

from sitegen.content import (
    BUSINESSES, COMPANY_NAME_ORIGIN, CONTACT_CATEGORIES, CONTACT_HOURS, CONTACT_INTRO, HERO_SUB,
    MESSAGE, MESSAGE_TITLE, NEWS, NOT_FOUND_TEXT, PAGE_META, PLACEHOLDER, PRIVACY, PRIVACY_ENACTED,
    SITE, SITE_URL, NewsItem,
)
from sitegen.render import esc, url
from sitegen.seo import head_meta, organization_jsonld


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


def _section_head(label: str, title: str, extra: str = "") -> str:
    return (
        f'<div class="section-head reveal{extra}">'
        f'<span class="section-label">{esc(label)}</span>'
        f'<h2 class="section-title">{esc(title)}</h2>'
        "</div>"
    )


# WebP versions of hero-tokyo.jpg, made by tools/hero_images.py (same widths).
HERO_WIDTHS: tuple[int, ...] = (960, 1280, 1920)
# The photo covers the hero (object-fit: cover, at least one screen tall), so on
# tall screens it is wider than the viewport: 1.5 = its width / height.
HERO_SIZES = "max(100vw, 150vh)"


def _hero_srcset() -> str:
    return ", ".join(f"/static/img/hero-tokyo-{w}.webp {w}w" for w in HERO_WIDTHS)


def body_index() -> str:
    cards = "\n".join(
        f'<a class="card biz-card reveal" style="--d: {i}" href="/business.html#{esc(b.slug)}">'
        f'<span class="biz-num">{esc(b.number)}</span>'
        f'<h3 class="biz-title">{esc(b.title)}</h3>'
        f'<span class="biz-en">{esc(b.title_en)}</span>'
        f'<p class="biz-summary">{esc(b.summary)}</p>'
        f'<span class="biz-more">詳しく見る</span>'
        "</a>"
        for i, b in enumerate(BUSINESSES)
    )
    return f"""<section class="section hero">
<!-- Photo: Louie Martinez / Unsplash (Unsplash License) https://unsplash.com/photos/IocJwyqRv3M -->
<picture>
<source type="image/webp" srcset="{_hero_srcset()}" sizes="{HERO_SIZES}">
<img class="hero-skyline" src="/static/img/hero-tokyo.jpg" alt="東京タワーと東京の街並み" width="1920" height="1278" fetchpriority="high">
</picture>
<div class="hero-sky" aria-hidden="true"></div>
<div class="container hero-inner">
<p class="hero-kicker reveal">{esc(SITE["name_en"])}</p>
<h1>{esc(SITE["tagline"])}</h1>
<p class="hero-sub reveal" style="--d: 1">{esc(HERO_SUB)}</p>
</div>
<a class="scroll-cue" href="#about" aria-label="下へスクロール"><span>SCROLL</span></a>
</section>

<section class="section top-about" id="about">
<div class="container about-grid">
{_section_head("About", "会社紹介", " reveal--left")}
<div class="about-body reveal" style="--d: 1">
<p class="lead-text">{esc(SITE["philosophy"])}</p>
<a class="btn" href="/company.html">会社紹介を見る</a>
</div>
</div>
</section>

<section class="section alt top-business" id="business">
<div class="container">
{_section_head("Business", "事業概要")}
<div class="biz-grid">
{cards}
</div>
</div>
</section>

<section class="section top-message" id="message">
<div class="container message-inner">
{_section_head("Message", "代表挨拶")}
<blockquote class="message-excerpt reveal reveal--zoom" style="--d: 1"><p>{esc(MESSAGE[0])}</p></blockquote>
<a class="btn reveal" style="--d: 2" href="/message.html">代表挨拶を読む</a>
</div>
</section>

<section class="section alt top-news" id="news">
<div class="container news-grid">
{_section_head("News", "ニュースルーム", " reveal--left")}
<div class="news-body reveal reveal--right" style="--d: 1">
{news_list_html(NEWS[:3])}
<a class="btn" href="/news.html">ニュース一覧へ</a>
</div>
</div>
</section>

<section class="section cta-band" id="contact">
<div class="container cta-inner reveal">
<span class="section-label">Contact</span>
<a class="cta-link" href="/contact.html">お問い合わせはこちら</a>
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
            "</div>\n</section>"
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
    "404.html": body_404,
}

def _fixed_page(name: str, body: Callable[[], str]) -> Page:
    title, description = PAGE_META[name]
    if name == "404.html":
        # Served for any missing URL: keep it out of search results and the sitemap.
        return Page(name, title, description, body, head_extra='<meta name="robots" content="noindex">',
                    indexable=False)
    head = head_meta(filename=name, title=title, description=description)
    if name == "index.html":
        head += "\n" + organization_jsonld()
    return Page(name, title, description, body, head_extra=head)


PAGES: list[Page] = [_fixed_page(name, body) for name, body in _BODIES.items()]


def article_pages(items: Sequence[NewsItem] | None = None) -> list[Page]:
    """One Page per news item. Reads NEWS at call time when items is None."""
    items = NEWS if items is None else items
    return [
        Page(
            filename=news_page_filename(item),
            title=f"{item.title} | Lead Japan 合同会社",
            description=item.summary,
            body=lambda item=item: body_news_article(item),
            nav_current="news.html",
            head_extra=og_tags(item, SITE_URL),
            lastmod=item.date,
        )
        for item in items
    ]


PAGES.extend(article_pages())
