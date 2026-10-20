import datetime

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models

from sitegen import content as site_content
from sitegen.news import CATEGORIES, SLUG_RE
from sitegen.pages import article_page_title

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def suggest_slug(on: datetime.date) -> str:
    base = on.isoformat()
    slug, n = base, 1
    while Article.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


class Article(models.Model):
    title = models.CharField("タイトル", max_length=200, unique=True)
    slug = models.CharField(
        "スラッグ",
        max_length=80,
        unique=True,
        validators=[RegexValidator(SLUG_RE, "半角英小文字・数字・ハイフンのみ使用できます")],
        help_text="公開後に変更するとURLが変わります",
    )
    published_on = models.DateField("公開日")
    category = models.CharField("カテゴリ", max_length=20, choices=[(c, c) for c in CATEGORIES])
    summary = models.CharField("概要", max_length=200)
    body_md = models.TextField("本文 (Markdown)")
    image = models.ImageField(
        "画像", upload_to="news/", blank=True,
        validators=[FileExtensionValidator(
            ["jpg", "jpeg", "png", "webp"],
            message="画像は jpg / png / webp 形式にしてください")],
    )
    image_alt = models.CharField("画像の代替テキスト", max_length=200, blank=True)
    status = models.CharField(
        "状態", max_length=10, choices=[("draft", "下書き"), ("published", "公開")], default="draft"
    )
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ["-published_on", "slug"]
        verbose_name = "記事"
        verbose_name_plural = "記事"

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if any(article_page_title(self.title) == t for t, _ in site_content.PAGE_META.values()):
            errors["title"] = "このタイトルは固定ページのタイトルと重なるため使えません。別のタイトルにしてください"
        if self.image:
            if not self.image_alt.strip():
                errors["image_alt"] = "画像を設定する場合は代替テキストが必要です"
            try:
                too_big = self.image.size > MAX_IMAGE_BYTES
            except OSError:  # stored file missing/unreadable: skip the size check
                too_big = False
            if too_big:
                errors["image"] = "画像は5MB以下にしてください"
        if errors:
            raise ValidationError(errors)
