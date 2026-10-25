// Cloudflare Pages Functions middleware: runs for every Function route (/ and
// /pm-book-bonus/download, see _routes.json written by build.py).
//
// Cloudflare Pages does not apply site/_headers to Function responses, so the
// same security headers are set here. Keep in sync with sitegen/headers.py
// (tests/test_headers.py compares the two).
export const SECURITY_HEADERS = {
  "Content-Security-Policy": [
    "default-src 'none'",
    "style-src 'self' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'none'",
  ].join("; "),
  "Strict-Transport-Security": "max-age=31536000",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

export async function onRequest(context) {
  const response = await context.next();
  // A copy: responses such as Response.redirect() have immutable headers.
  const out = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) out.headers.set(name, value);
  return out;
}
