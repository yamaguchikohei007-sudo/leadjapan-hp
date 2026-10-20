"""HTML layout rendering (standard library only, no JavaScript)."""
from __future__ import annotations

import html

from sitegen.content import COPYRIGHT, NAV, PLACEHOLDER, SITE

FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&"
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


def _nav_links(current: str | None) -> str:
    items = []
    for filename, label in NAV:
        attr = ' aria-current="page"' if filename == current else ""
        items.append(f'<a href="{esc(filename)}"{attr}>{esc(label)}</a>')
    return "\n".join(items)


def render_layout(*, title: str, description: str, body: str, current: str,
                  head_extra: str = "") -> str:
    nav = _nav_links(current)
    footer_links = "\n".join(
        f'<a href="{esc(f)}">{esc(label)}</a>' for f, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" type="image/svg+xml" href="static/img/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_URL}">
<link rel="stylesheet" href="static/css/style.css">
<link rel="stylesheet" href="static/css/motion.css">
{head_extra}
</head>
<body>
<a class="skip-link" href="#main">本文へスキップ</a>
<header class="site-header">
<div class="container header-inner">
<a class="logo" href="index.html" aria-label="{esc(SITE["name"])}">{LOGO_MARK}<span class="logo-text">Lead Japan <small>合同会社</small></span></a>
<input type="checkbox" id="nav-toggle" class="nav-toggle" aria-label="メニュー">
<label for="nav-toggle" class="nav-toggle-label"><span class="visually-hidden">メニュー</span><span></span></label>
<nav class="global-nav" aria-label="グローバルナビゲーション">
{nav}
</nav>
</div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
<div class="container footer-inner">
<div class="footer-company">
<div class="footer-logo">{LOGO_MARK}</div>
<p class="footer-name">{esc(SITE["name"])}</p>
<p>{esc(SITE["location"])}</p>
</div>
<nav class="footer-nav" aria-label="フッターナビゲーション">
{footer_links}
<a href="privacy.html">プライバシーポリシー</a>
</nav>
</div>
<p class="copyright container">{esc(COPYRIGHT)}</p>
</footer>
</body>
</html>
"""
