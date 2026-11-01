// Tests for functions/_middleware.js. Run: node --test tests/js/security_headers.test.mjs
// (tests/test_headers.py runs this too when Node.js is installed.)
import assert from "node:assert/strict";
import test from "node:test";

import { SECURITY_HEADERS, onRequest } from "../../functions/_middleware.js";

const run = (response) => onRequest({ next: async () => response });

function assertSecurityHeaders(res) {
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
    assert.equal(res.headers.get(name), value, name);
  }
}

test("the home page gets the security headers and keeps its own", async () => {
  const page = new Response("<html></html>", {
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "private, no-store" },
  });
  const res = await run(page);
  assertSecurityHeaders(res);
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("Cache-Control"), "private, no-store");
  assert.equal(await res.text(), "<html></html>");
});

test("redirects get them too, even with immutable headers", async () => {
  for (const redirect of [
    new Response(null, { status: 303, headers: { Location: "/pm-book-bonus-error.html" } }),
    Response.redirect("https://example.com/pm-book-bonus.html", 303),
  ]) {
    const res = await run(redirect);
    assertSecurityHeaders(res);
    assert.equal(res.status, 303);
    assert.ok(res.headers.get("Location"));
  }
});

test("the CSP is the strict one", () => {
  const csp = SECURITY_HEADERS["Content-Security-Policy"];
  assert.match(csp, /^default-src 'none'; /);
  assert.doesNotMatch(csp, /unsafe-inline|unsafe-eval/);
});
