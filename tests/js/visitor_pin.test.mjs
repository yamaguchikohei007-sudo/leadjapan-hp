// Tests for functions/index.js. Run: node --test tests/js/visitor_pin.test.mjs
// (tests/test_visitor_pin.py runs this too when Node.js is installed.)
import assert from "node:assert/strict";
import test from "node:test";

import { onRequestGet, pinFor } from "../../functions/index.js";

const TOKYO = pinFor(undefined);

test("visitors outside Japan and unknown locations get Tokyo", () => {
  for (const cf of [undefined, {}, { country: "US", regionCode: "27" }, { country: "JP" },
    { country: "JP", regionCode: "99" }, { country: "JP", latitude: "x", longitude: "1" }]) {
    assert.deepEqual(pinFor(cf), TOKYO, JSON.stringify(cf));
  }
});

test("region code picks the prefecture, in any common spelling", () => {
  const osaka = pinFor({ country: "JP", regionCode: "27" });
  assert.notDeepEqual(osaka, TOKYO);
  assert.deepEqual(pinFor({ country: "JP", regionCode: "JP-27" }), osaka);
  assert.deepEqual(pinFor({ country: "JP", regionCode: "1" }), pinFor({ country: "JP", regionCode: "01" }));
});

test("without a region code, the nearest prefectural capital is used", () => {
  const fukuoka = pinFor({ country: "JP", regionCode: "40" });
  assert.deepEqual(pinFor({ country: "JP", latitude: "33.59", longitude: "130.40" }), fukuoka);
});

// Minimal stand-in for Cloudflare's HTMLRewriter: applies the handler to one fake element.
class FakeRewriter {
  on(selector, handlers) {
    this.selector = selector;
    this.handlers = handlers;
    return this;
  }
  transform(response) {
    const el = { attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } };
    this.handlers.element(el);
    FakeRewriter.last = { selector: this.selector, attrs: el.attrs };
    return new Response(response.body, response);
  }
}
globalThis.HTMLRewriter = FakeRewriter;

const page = (type = "text/html; charset=utf-8", status = 200) => () =>
  new Response("<html></html>", { status, headers: { "Content-Type": type, ETag: '"abc"' } });

test("moves the pin and forbids shared caching", async () => {
  const res = await onRequestGet({ request: { cf: { country: "JP", regionCode: "27" } }, next: page() });
  const [x, y] = pinFor({ country: "JP", regionCode: "27" });
  assert.equal(FakeRewriter.last.selector, "[data-visitor-pin]");
  assert.equal(FakeRewriter.last.attrs.transform, `translate(${x} ${y})`);
  assert.equal(res.headers.get("Cache-Control"), "private, no-store");
  assert.equal(res.headers.get("ETag"), null);
});

test("non-HTML and error responses pass through untouched", async () => {
  for (const next of [page("text/css"), page("text/html", 404)]) {
    const res = await onRequestGet({ request: { cf: {} }, next });
    assert.equal(res.headers.get("Cache-Control"), null);
  }
});
