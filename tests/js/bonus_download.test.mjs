// Tests for bonus/download.js. Run: node --test tests/js/bonus_download.test.mjs
// (tests/test_book.py runs this too when Node.js is installed.)
// The real password is not in the repository, so a stand-in password is used.
import assert from "node:assert/strict";
import test from "node:test";

import { ERROR_PAGE, FORM_PAGE, handlePost, normalize, PASSWORD_SHA256, sha256Hex } from "../../bonus/download.js";
import file from "../../bonus/pm-book-gantt-tool.js";
import { onRequestGet, onRequestPost } from "../../functions/pm-book-bonus/download.js";

const TEST_HASH = await sha256Hex("open-sesame");

function post(password) {
  const body = new FormData();
  if (password !== undefined) body.set("password", password);
  return new Request("https://example.com/pm-book-bonus/download", { method: "POST", body });
}

test("the right password downloads the file", async () => {
  const res = await handlePost(post("open-sesame"), "<html>tool</html>", TEST_HASH);
  assert.equal(res.status, 200);
  assert.equal(await res.text(), "<html>tool</html>");
  assert.match(res.headers.get("Content-Disposition"), /^attachment; filename="[\x20-\x7e]+\.html"; filename\*=UTF-8''/);
  assert.equal(res.headers.get("Cache-Control"), "private, no-store");
});

test("full-width letters, spaces and capitals are accepted", async () => {
  for (const typed of ["OPEN-SESAME", "  open-sesame ", "ｏｐｅｎ－ｓｅｓａｍｅ"]) {
    const res = await handlePost(post(typed), "x", TEST_HASH);
    assert.equal(res.status, 200, typed);
  }
});

test("a wrong or missing password goes to the error page", async () => {
  for (const typed of ["open-sesam", "", undefined, "x".repeat(500)]) {
    const res = await handlePost(post(typed), "x", TEST_HASH);
    assert.equal(res.status, 303, String(typed));
    assert.equal(res.headers.get("Location"), ERROR_PAGE);
  }
  const notAForm = new Request("https://example.com/", { method: "POST", body: "{}" });
  assert.equal((await handlePost(notAForm, "x", TEST_HASH)).status, 303);
});

test("the function uses the real hash and the bundled tool", async () => {
  assert.match(PASSWORD_SHA256, /^[0-9a-f]{64}$/);
  assert.notEqual(PASSWORD_SHA256, TEST_HASH);
  assert.ok(file.startsWith("<!DOCTYPE html>"));
  const wrong = await onRequestPost({ request: post("open-sesame") });
  assert.equal(wrong.headers.get("Location"), ERROR_PAGE);
  assert.equal(onRequestGet().headers.get("Location"), FORM_PAGE);
});

test("normalize", () => {
  assert.equal(normalize(" ＡＢｃ "), "abc");
  assert.equal(normalize(null), "");
});
