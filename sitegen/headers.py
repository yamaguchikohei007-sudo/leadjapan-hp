"""Security headers for every response (stdlib only).

build.py writes them to site/_headers for the static pages. Cloudflare Pages does
not apply _headers to Pages Functions responses, so functions/_middleware.js sets
the same values on those (tests/test_headers.py checks that the two agree).
"""
from __future__ import annotations

# The public site runs no JavaScript and has no inline styles (tests/helpers.py
# check_no_javascript / check_no_inline_styles); the only outside resources are
# Google Fonts. <script type="application/ld+json"> is data, not code, so the
# CSP does not block it.
CONTENT_SECURITY_POLICY = "; ".join((
    "default-src 'none'",
    "style-src 'self' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self'",
    "form-action 'self'",  # the reader-bonus form posts to /pm-book-bonus/download
    "frame-ancestors 'none'",
    "base-uri 'none'",
))

SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    # No includeSubDomains / preload: other subdomains of a future custom domain
    # must not be forced onto HTTPS by this site.
    "Strict-Transport-Security": "max-age=31536000",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def headers_file(headers: dict[str, str] = SECURITY_HEADERS) -> str:
    """Cloudflare Pages _headers applying `headers` to every path."""
    return "/*\n" + "".join(f"  {name}: {value}\n" for name, value in headers.items())
