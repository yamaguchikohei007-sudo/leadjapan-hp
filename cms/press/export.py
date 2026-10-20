from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

from sitegen.news import NewsItem, news_to_json

from .models import Article
from .rendering import render_markdown

IMAGE_DIR = "static/img/news"
ALLOWED_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MAX_IMAGE_WIDTH = 1600  # the article column is 760px wide; 2x for high-density screens
_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


class ExportError(Exception):
    pass


def _to_rgb(im: Image.Image, icc: bytes | None, *, alpha: bool) -> tuple[Image.Image, bytes | None]:
    """RGB(A) pixels for JPEG/WebP, with a colour profile that still matches them.

    A CMYK or grey profile cannot describe RGB pixels: such images are converted
    through their profile to sRGB (the web default, so no profile is embedded),
    or, if that fails, converted plainly and the profile dropped."""
    has_alpha = alpha and (im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info)
    target = "RGBA" if has_alpha else "RGB"
    if im.mode in ("RGB", "RGBA", "P"):  # their profiles are RGB profiles
        return (im if im.mode == target else im.convert(target)), icc
    if icc and not has_alpha:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            return ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB"), None
        except (ImageCms.PyCMSError, OSError, ValueError):
            pass
    return im.convert(target), None


def optimized_image(data: bytes, ext: str) -> bytes:
    """Rotate per EXIF, shrink to MAX_IMAGE_WIDTH and re-encode without metadata
    (camera EXIF can include the GPS location). An RGB colour profile is kept."""
    with Image.open(io.BytesIO(data)) as src:
        icc = src.info.get("icc_profile")
        im = ImageOps.exif_transpose(src)
    if im.width > MAX_IMAGE_WIDTH:
        im = im.resize((MAX_IMAGE_WIDTH, round(im.height * MAX_IMAGE_WIDTH / im.width)), Image.LANCZOS)
    fmt = _FORMATS[ext]
    if fmt in ("JPEG", "WEBP"):  # both store RGB only (WebP: plus alpha)
        im, icc = _to_rgb(im, icc, alpha=fmt == "WEBP")
    opts: dict[str, object] = {"icc_profile": icc} if icc else {}
    if fmt == "JPEG":
        opts.update(quality=82, optimize=True, progressive=True)
    elif fmt == "WEBP":
        opts.update(quality=82, method=6)
    else:
        opts.update(optimize=True)
    out = io.BytesIO()
    im.save(out, fmt, **opts)
    return out.getvalue()


def image_target(article: Article) -> str | None:
    if not article.image:
        return None
    ext = Path(article.image.name).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise ExportError(f"{article.slug}: 画像の拡張子 {ext!r} は使用できません ({', '.join(ALLOWED_EXTS)})")
    return f"{IMAGE_DIR}/{article.slug}{ext}"


def article_to_newsitem(article: Article, *, image: str | None = ...) -> NewsItem:
    if image is ...:
        image = image_target(article)
    return NewsItem(
        slug=article.slug,
        date=article.published_on,
        category=article.category,
        title=article.title,
        summary=article.summary,
        body_html=render_markdown(article.body_md),
        body_md=article.body_md,
        image=image,
        image_alt=article.image_alt if image else "",
    )


def export_published(repo_root: Path) -> list[str]:
    repo_root = Path(repo_root)
    articles = list(Article.objects.filter(status="published"))

    # Validate (and re-encode images) first so a failure leaves the repo untouched.
    plan = []
    images: dict[str, bytes] = {}
    for a in articles:
        target = image_target(a)
        if target:
            if not a.image.storage.exists(a.image.name):
                raise ExportError(f"{a.slug}: 画像ファイルが見つかりません ({a.image.name})")
            with a.image.storage.open(a.image.name, "rb") as src:
                data = src.read()
            try:
                images[target] = optimized_image(data, Path(target).suffix)
            except (OSError, ValueError, Image.DecompressionBombError) as e:
                raise ExportError(f"{a.slug}: 画像を読み込めません ({a.image.name}): {e}") from e
        plan.append((a, target))

    changed: list[str] = []
    (repo_root / "content").mkdir(parents=True, exist_ok=True)
    img_dir = repo_root / IMAGE_DIR
    img_dir.mkdir(parents=True, exist_ok=True)

    referenced = set()
    for target, data in images.items():
        referenced.add(target)
        (repo_root / target).write_bytes(data)
        changed.append(target)

    for f in sorted(img_dir.iterdir()):
        rel = f"{IMAGE_DIR}/{f.name}"
        if f.is_file() and not f.name.startswith(".") and rel not in referenced:
            f.unlink()
            changed.append(rel)

    items = [article_to_newsitem(a, image=t) for a, t in plan]
    (repo_root / "content/news.json").write_text(news_to_json(items), encoding="utf-8")
    changed.append("content/news.json")
    return changed
