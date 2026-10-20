"""Static site build: python3 build.py -> site/"""
from __future__ import annotations

import pathlib
import shutil
from typing import Sequence

from sitegen import content
from sitegen.content import UNCONFIRMED
from sitegen.pages import PAGES, Page
from sitegen.render import find_placeholders, render_layout
from sitegen.seo import robots_txt, sitemap_xml

ROOT = pathlib.Path(__file__).resolve().parent
STATIC = ROOT / "static"


def build(out_dir: pathlib.Path, pages: Sequence[Page] | None = None) -> list[pathlib.Path]:
    """Writes the site; returns the HTML pages written (sitemap.xml/robots.txt are extra)."""
    out_dir = pathlib.Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    pages = PAGES if pages is None else pages
    written: list[pathlib.Path] = []
    for page in pages:
        html = render_layout(
            title=page.title,
            description=page.description,
            body=page.body(),
            current=page.nav_current or page.filename,
            head_extra=page.head_extra,
        )
        path = out_dir / page.filename
        path.write_text(html, encoding="utf-8")
        written.append(path)
    if content.SITE_URL:  # both files need absolute URLs
        entries = [(p.filename, p.lastmod) for p in pages if p.indexable]
        (out_dir / "sitemap.xml").write_text(sitemap_xml(entries, content.SITE_URL), encoding="utf-8")
        (out_dir / "robots.txt").write_text(robots_txt(content.SITE_URL), encoding="utf-8")
    if STATIC.exists():
        shutil.copytree(STATIC, out_dir / "static")
    return written


def placeholder_report(paths: list[pathlib.Path]) -> dict[str, int]:
    """filename -> count of 【要入力】 markers, only for files with at least one."""
    report: dict[str, int] = {}
    for p in paths:
        n = find_placeholders(pathlib.Path(p).read_text(encoding="utf-8"))
        if n:
            report[pathlib.Path(p).name] = n
    return report


def format_warnings(report: dict[str, int], unconfirmed: tuple[str, ...] = UNCONFIRMED) -> str:
    lines: list[str] = []
    total = sum(report.values())
    if total:
        lines.append(f"警告: 【要入力】 が {total} 箇所残っています ({', '.join(report)})")
    if unconfirmed:
        lines.extend(f"要確認: {item}" for item in unconfirmed)
    return "\n".join(lines)


def main() -> None:
    written = build(ROOT / "site")
    print(f"{len(written)} ページを site/ に生成しました")
    warnings = format_warnings(placeholder_report(written))
    if warnings:
        print(warnings)


if __name__ == "__main__":
    main()
