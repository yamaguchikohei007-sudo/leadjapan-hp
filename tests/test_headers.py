"""Security headers: site/_headers (static pages) and the Pages Functions responses."""
import json
import re
import shutil
import subprocess
import unittest

from tests.helpers import ROOT, build_to_tmp
from sitegen.headers import SECURITY_HEADERS


def parse_headers_file(text: str) -> dict[str, dict[str, str]]:
    """Cloudflare Pages _headers -> {url pattern: {header name: value}}."""
    rules: dict[str, dict[str, str]] = {}
    current = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            current = rules.setdefault(line.strip(), {})
        else:
            name, _, value = line.strip().partition(":")
            current[name.strip()] = value.strip()
    return rules


def csp_directives(csp: str) -> dict[str, list[str]]:
    out = {}
    for part in csp.split(";"):
        if part.strip():
            name, *values = part.split()
            out[name] = values
    return out


class HeadersFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build_to_tmp()
        cls.addClassCleanup(shutil.rmtree, cls.out, ignore_errors=True)
        path = cls.out / "_headers"
        cls.rules = parse_headers_file(path.read_text(encoding="utf-8")) if path.exists() else {}

    def headers(self) -> dict[str, str]:
        self.assertIn("/*", self.rules, "site/_headers must cover every path")
        return self.rules["/*"]

    def test_headers_file_is_at_the_site_root(self):
        # Cloudflare Pages reads _headers only from the top of the output directory.
        self.assertTrue((self.out / "_headers").exists())
        self.assertFalse((self.out / "static" / "_headers").exists())

    def test_csp_is_strict(self):
        csp = csp_directives(self.headers()["Content-Security-Policy"])
        self.assertEqual(csp["default-src"], ["'none'"])
        self.assertEqual(csp["style-src"], ["'self'", "https://fonts.googleapis.com"])
        self.assertEqual(csp["font-src"], ["https://fonts.gstatic.com"])
        self.assertEqual(csp["img-src"], ["'self'"])
        self.assertEqual(csp["form-action"], ["'self'"])
        self.assertEqual(csp["frame-ancestors"], ["'none'"])
        self.assertEqual(csp["base-uri"], ["'none'"])
        self.assertNotIn("script-src", csp)  # falls back to default-src 'none'
        for values in csp.values():
            self.assertNotIn("'unsafe-inline'", values)
            self.assertNotIn("'unsafe-eval'", values)

    def test_hsts_without_subdomains_or_preload(self):
        # A custom domain's other subdomains must not be forced onto HTTPS by this site.
        self.assertEqual(self.headers()["Strict-Transport-Security"], "max-age=31536000")

    def test_other_security_headers(self):
        h = self.headers()
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")
        self.assertEqual(h["X-Frame-Options"], "DENY")
        self.assertEqual(h["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(h["Permissions-Policy"], "camera=(), microphone=(), geolocation=()")

    def test_parser(self):
        rules = parse_headers_file("# c\n/*\n  A: 1\n  B: x: y\n/b\n  C: 2\n")
        self.assertEqual(rules, {"/*": {"A": "1", "B": "x: y"}, "/b": {"C": "2"}})


@unittest.skipUnless(shutil.which("node"), "Node.js not installed")
class FunctionHeadersTests(unittest.TestCase):
    """_headers is not applied to Pages Functions responses (/ and /pm-book-bonus/download)."""

    def test_middleware_matches_headers_file(self):
        script = "import('./functions/_middleware.js').then((m) => console.log(JSON.stringify(m.SECURITY_HEADERS)))"
        r = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout), SECURITY_HEADERS)

    def test_node_tests_pass(self):
        r = subprocess.run(["node", "--test", "tests/js/security_headers.test.mjs"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertRegex(r.stdout, re.compile(r"# pass [1-9]"))


if __name__ == "__main__":
    unittest.main()
