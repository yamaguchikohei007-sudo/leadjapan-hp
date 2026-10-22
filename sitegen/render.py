"""HTML layout rendering (standard library only, no JavaScript)."""
from __future__ import annotations

import html

from sitegen.content import BOOK, COPYRIGHT, FOOTER_CONTACT, FOOTER_DESCRIPTION, NAV, PLACEHOLDER, SITE

# Only the weights style.css uses (400, 500, 700): each extra weight is another download.
FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;700&"
    "family=Noto+Sans+JP:wght@400;500;700&display=swap"
)

# Brand mark: two strokes follow the text colour (navy / white), the dot stays red.
LOGO_MARK = (
    '<svg class="logo-mark" viewBox="0 0 256 196" width="256" height="196" '
    'aria-hidden="true" focusable="false">'
    '<polygon points="0,179 56,179 179,0 123,0" fill="currentColor"/>'
    '<polygon points="140,84 166,66 254,194 196,194" fill="currentColor"/>'
    '<circle cx="129" cy="165" r="26" fill="#D71920"/>'
    "</svg>"
)


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def find_placeholders(text: str) -> int:
    return text.count(PLACEHOLDER)


def url(path: str) -> str:
    """Root-relative URL for a site file ("company.html#x" -> "/company.html#x").

    Root-relative so pages served from any depth (e.g. 404.html for /a/b/c)
    still find their CSS and images. Absolute URLs and "/..." pass through.
    """
    if path.startswith(("/", "#", "http:", "https:", "mailto:")):
        return path
    if path == "index.html" or path.startswith("index.html#"):
        return "/" + path.removeprefix("index.html")
    return "/" + path


def _nav_links(current: str | None) -> str:
    items = []
    for filename, label in NAV:
        attr = ' aria-current="page"' if filename == current else ""
        items.append(f'<a href="{esc(url(filename))}"{attr}>{esc(label)}</a>')
    return "\n".join(items)


# Book landing page (pm-book.html and its reader-bonus pages): a header of its own with
# in-page links, so the page reads as the book's site rather than a company subpage.
BOOK_NAV: tuple[tuple[str, str], ...] = (
    ("about", "内容"),
    ("contents", "構成"),
    ("bonus", "読者特典"),
    ("author", "著者"),
    ("info", "書籍情報"),
)


def _book_header() -> str:
    links = "\n".join(f'<a href="/pm-book.html#{slug}">{esc(label)}</a>' for slug, label in BOOK_NAV)
    if BOOK["status"] == "on_sale":
        cta = '<a class="book-header-cta" href="/pm-book.html#hero">購入する</a>'
    else:
        # the second half is dropped on narrow phones, so the header keeps to two rows
        cta = '<a class="book-header-cta" href="/pm-book.html#notify">発売通知<span class="cta-more">を受け取る</span></a>'
    return f"""<header class="book-header">
<div class="container book-header-inner">
<a class="book-brand" href="/pm-book.html"><span class="book-brand-sub">外資系プロジェクトマネージャー</span><span class="book-brand-main">1年目の教科書</span></a>
<nav class="book-nav" aria-label="書籍ページ内のリンク">
{links}
</nav>
{cta}
</div>
</header>"""


def _book_footer() -> str:
    return f"""<footer class="book-footer">
<div class="container book-footer-inner">
<a class="book-footer-brand" href="/">{LOGO_MARK}<span>発行 {esc(SITE["name"])}</span></a>
<nav class="book-footer-nav" aria-label="発行元">
<a href="/company.html">会社紹介</a>
<a href="/contact.html">お問い合わせ</a>
<a href="/privacy.html">プライバシーポリシー</a>
</nav>
<p class="copyright">{esc(COPYRIGHT)}</p>
</div>
</footer>"""


def render_layout(*, title: str, description: str, body: str, current: str,
                  head_extra: str = "", layout: str = "site") -> str:
    """layout: "site" (company header and footer) or "book" (the book's landing page)."""
    nav = _nav_links(current)
    footer_links = "\n".join(
        f'<a href="{esc(url(f))}">{esc(label)}</a>' for f, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#10366B">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" type="image/svg+xml" href="/static/img/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_URL}">
<link rel="stylesheet" href="/static/css/style.css">
<link rel="stylesheet" href="/static/css/motion.css">
{head_extra}
</head>
<body{' class="layout-book"' if layout == "book" else ""}>
<a class="skip-link" href="#main">本文へスキップ</a>
{_book_header() if layout == "book" else _site_header(nav)}
<main id="main">
{body}
</main>
{_book_footer() if layout == "book" else _site_footer(footer_links)}
</body>
</html>
"""


def _site_header(nav: str) -> str:
    return f"""<header class="site-header">
<div class="container header-inner">
<a class="logo" href="/" aria-label="{esc(SITE["name"])}">{LOGO_MARK}<span class="logo-text">Lead Japan <small>合同会社</small></span></a>
<button type="button" class="nav-toggle" popovertarget="global-nav"><span class="visually-hidden">メニュー</span><span class="nav-toggle-bars" aria-hidden="true"></span></button>
<a class="nav-fallback" href="#footer-nav">メニュー</a>
<nav id="global-nav" class="global-nav" popover aria-label="グローバルナビゲーション">
<button type="button" class="nav-close" popovertarget="global-nav" popovertargetaction="hide"><span class="visually-hidden">メニューを閉じる</span></button>
{nav}
</nav>
</div>
</header>"""


def _site_footer(footer_links: str) -> str:
    return f"""<footer class="site-footer">
<div class="container">
<div class="footer-grid">
<div class="footer-company">
<div class="footer-brand"><div class="footer-logo">{LOGO_MARK}</div><span class="logo-text">Lead Japan <small>合同会社</small></span></div>
<p>{esc(FOOTER_DESCRIPTION)}</p>
</div>
<nav id="footer-nav" class="footer-nav" aria-labelledby="footer-nav-heading">
<h2 class="footer-heading" id="footer-nav-heading" lang="en">Sitemap</h2>
{footer_links}
</nav>
<div class="footer-col">
<h2 class="footer-heading" lang="en">Company</h2>
<p class="footer-name">{esc(SITE["name"])}</p>
<p>{esc(SITE["address"])}</p>
<p>設立 {esc(SITE["founded"])}</p>
</div>
<div class="footer-col">
<h2 class="footer-heading" lang="en">Contact</h2>
<p>{esc(FOOTER_CONTACT)}</p>
<a class="btn btn-outline-light btn-small" href="/contact.html">お問い合わせ</a>
</div>
</div>
<div class="footer-bottom">
<p class="copyright">{esc(COPYRIGHT)}</p>
<a href="/privacy.html">プライバシーポリシー</a>
</div>
</div>
</footer>"""
