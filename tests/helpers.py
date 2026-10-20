"""Shared test helpers."""
from __future__ import annotations

import html.parser
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class LinkCollector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []      # every href/src (resources + anchors)
        self.resources: list[str] = []  # loaded resources: src=, <link href>
        self.anchors: list[str] = []    # <a href>
        self.scripts = 0                # executable scripts only
        self.jsonld = 0                 # <script type="application/ld+json"> (data, not code)
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script":
            if a.get("type") == "application/ld+json":
                self.jsonld += 1
            else:
                self.scripts += 1
        if tag == "title":
            self._in_title = True
        for key in ("href", "src"):
            if a.get(key) is not None:
                self.links.append(a[key])
                if key == "src" or (tag == "link" and a.get("rel") != "canonical"):
                    self.resources.append(a[key])
                elif tag == "a":
                    self.anchors.append(a[key])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def build_to_tmp() -> pathlib.Path:
    from build import build
    out = pathlib.Path(tempfile.mkdtemp())
    build(out)
    return out


def collect(path: pathlib.Path) -> LinkCollector:
    c = LinkCollector()
    c.feed(path.read_text(encoding="utf-8"))
    return c


def check_internal_links_resolve(tc, out: pathlib.Path) -> None:
    for page in out.glob("*.html"):
        for link in collect(page).links:
            if link.startswith(("http:", "https:", "mailto:", "#")):
                continue
            path, _, frag = link.partition("#")
            if path.startswith("/"):
                path = path.removeprefix("/") or "index.html"
            target = out / path
            tc.assertTrue(target.exists(), f"{page.name}: {link}")
            if frag:
                tc.assertIn(f'id="{frag}"', target.read_text(encoding="utf-8"), f"{page.name}: {link}")


def check_no_javascript(tc, out: pathlib.Path) -> None:
    for page in out.glob("*.html"):
        tc.assertEqual(collect(page).scripts, 0, page.name)
    tc.assertEqual(list(out.rglob("*.js")), [])


def check_only_free_external_hosts(tc, out: pathlib.Path) -> None:
    for page in out.glob("*.html"):
        # only loaded resources (src=, <link href>) are restricted; <a href> to
        # external sites (e.g. links inside press-release bodies) is allowed.
        for link in collect(page).resources:
            if link.startswith(("http:", "https:", "//")):
                tc.assertRegex(link, r"^https://fonts\.(googleapis|gstatic)\.com(/|$)")


def check_unique_titles(tc, out: pathlib.Path) -> None:
    titles = [collect(p).title for p in out.glob("*.html")]
    tc.assertEqual(len(titles), len(set(titles)))


def check_whole_site(tc, out: pathlib.Path) -> None:
    check_internal_links_resolve(tc, out)
    check_no_javascript(tc, out)
    check_only_free_external_hosts(tc, out)
    check_unique_titles(tc, out)
