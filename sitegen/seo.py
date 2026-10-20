"""Search/share metadata: canonical URLs, Open Graph, JSON-LD, sitemap.xml, robots.txt."""
from __future__ import annotations

import datetime
import json
from typing import Sequence
from xml.sax.saxutils import escape as xml_escape

from sitegen.content import PLACEHOLDER, SITE, SITE_URL
from sitegen.render import esc

# Shared image for pages (and articles) without their own.
DEFAULT_OG_IMAGE = "static/img/hero-tokyo.jpg"


def page_url(filename: str, site_url: str = SITE_URL) -> str:
    """Public URL of a page. Cloudflare Pages serves company.html as /company
    (and redirects /company.html there), so canonical URLs drop ".html"."""
    base = site_url.rstrip("/")
    if filename == "index.html":
        return base + "/"
    return f"{base}/{filename.removesuffix('.html')}"


def head_meta(*, filename: str, title: str, description: str, og_type: str = "website",
              image: str | None = None, site_url: str = SITE_URL) -> str:
    """canonical + Open Graph tags. URL-based tags need site_url, so they are
    left out when it is empty."""
    def og(prop: str, value: str) -> str:
        return f'<meta property="{prop}" content="{esc(value)}">'

    tags = []
    if site_url:
        tags.append(f'<link rel="canonical" href="{esc(page_url(filename, site_url))}">')
    tags += [
        og("og:title", title),
        og("og:description", description),
        og("og:type", og_type),
        og("og:site_name", SITE["name"]),
        og("og:locale", "ja_JP"),
    ]
    if site_url:
        tags.append(og("og:url", page_url(filename, site_url)))
        tags.append(og("og:image", site_url.rstrip("/") + "/" + (image or DEFAULT_OG_IMAGE)))
        tags.append('<meta name="twitter:card" content="summary_large_image">')
    return "\n".join(tags)


def organization_jsonld(site_url: str = SITE_URL) -> str:
    address = {"@type": "PostalAddress", "addressCountry": "JP", "addressRegion": SITE["location"]}
    locality = SITE["address"].removeprefix(SITE["location"])
    if locality and PLACEHOLDER not in locality:
        address["addressLocality"] = locality
    data: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": SITE["name"],
        "alternateName": SITE["name_en"],
        "address": address,
    }
    if site_url:
        data["url"] = page_url("index.html", site_url)
    if SITE["email"] != PLACEHOLDER:
        data["email"] = SITE["email"]
    # "</" would end the script element early.
    text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>'


def sitemap_xml(entries: Sequence[tuple[str, datetime.date | None]], site_url: str = SITE_URL) -> str:
    """entries: (filename, last-modified date or None)."""
    rows = []
    for filename, lastmod in entries:
        loc = f"<loc>{xml_escape(page_url(filename, site_url))}</loc>"
        mod = f"<lastmod>{lastmod.isoformat()}</lastmod>" if lastmod else ""
        rows.append(f"  <url>{loc}{mod}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def robots_txt(site_url: str = SITE_URL) -> str:
    return f"User-agent: *\nAllow: /\n\nSitemap: {site_url.rstrip('/')}/sitemap.xml\n"
