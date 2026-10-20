import datetime
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from sitegen.news import NewsItem, load_news, news_to_json

from press.export import MAX_IMAGE_WIDTH, ExportError, article_to_newsitem, export_published, image_target
from press.models import Article
from press.tests.test_models import make_article


def image_bytes(fmt="PNG", size=(40, 30), exif=None) -> bytes:
    out = BytesIO()
    kw = {"exif": exif} if exif is not None else {}
    Image.new("RGB", size, (16, 54, 107)).save(out, fmt, **kw)
    return out.getvalue()


class ExportBase(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        (self.repo / "content").mkdir(parents=True)
        (self.repo / "static/img/news").mkdir(parents=True)
        self.media = Path(self._tmp.name) / "media"
        ov = override_settings(MEDIA_ROOT=self.media)
        ov.enable()
        self.addCleanup(ov.disable)

    def make(self, **kw):
        a = make_article(**kw)
        a.save()
        return a


class ExportTests(ExportBase):
    def test_export_only_published(self):
        self.make(slug="pub-1", title="公開", status="published")
        self.make(slug="dr-1", title="下書き")
        export_published(self.repo)
        items = load_news(self.repo / "content/news.json")
        self.assertEqual([i.slug for i in items], ["pub-1"])
        self.assertEqual(items[0], article_to_newsitem(Article.objects.get(slug="pub-1")))

    def test_export_renders_body_html(self):
        self.make(slug="pub-1", status="published", body_md="**x**")
        export_published(self.repo)
        self.assertIn("<strong>x</strong>", load_news(self.repo / "content/news.json")[0].body_html)

    def test_export_copies_image(self):
        a = self.make(slug="pic-1", status="published", image=SimpleUploadedFile("Photo.PNG", image_bytes()),
                      image_alt="alt")
        export_published(self.repo)
        self.assertEqual(image_target(a), "static/img/news/pic-1.png")
        with Image.open(self.repo / "static/img/news/pic-1.png") as im:
            self.assertEqual((im.format, im.size), ("PNG", (40, 30)))
        self.assertEqual(load_news(self.repo / "content/news.json")[0].image, "static/img/news/pic-1.png")

    def test_export_shrinks_wide_images_and_drops_metadata(self):
        exif = Image.Exif()
        exif[0x010F] = "CameraMaker"  # Make; GPS data would travel the same way
        data = image_bytes("JPEG", size=(3200, 2000), exif=exif.tobytes())
        self.make(slug="big-1", status="published", image=SimpleUploadedFile("big.jpg", data), image_alt="alt")
        export_published(self.repo)
        out = self.repo / "static/img/news/big-1.jpg"
        with Image.open(out) as im:
            self.assertEqual(im.size, (MAX_IMAGE_WIDTH, 1000))
            self.assertNotIn("exif", im.info)
        self.assertLess(out.stat().st_size, len(data))

    def test_export_is_repeatable(self):
        # identical bytes on every run, or each publish would commit "changed" images
        self.make(slug="pic-1", status="published", image=SimpleUploadedFile("p.jpg", image_bytes("JPEG")),
                  image_alt="alt")
        export_published(self.repo)
        first = (self.repo / "static/img/news/pic-1.jpg").read_bytes()
        export_published(self.repo)
        self.assertEqual((self.repo / "static/img/news/pic-1.jpg").read_bytes(), first)

    def test_export_rejects_unreadable_image(self):
        self.make(slug="bad-1", status="published", image=SimpleUploadedFile("b.png", b"not an image"),
                  image_alt="alt")
        with self.assertRaises(ExportError) as cm:
            export_published(self.repo)
        self.assertIn("bad-1", str(cm.exception))
        self.assertFalse((self.repo / "content/news.json").exists())

    def test_image_target_none_and_bad_extension(self):
        self.assertIsNone(image_target(make_article()))
        a = make_article(image=SimpleUploadedFile("x.gif", b"d"))
        with self.assertRaises(ExportError):
            image_target(a)

    def test_export_removes_stale_images(self):
        (self.repo / "static/img/news/old.png").write_bytes(b"old")
        self.make(slug="dr-1", title="下書き", image=SimpleUploadedFile("d.png", b"d"), image_alt="a")
        self.make(slug="pub-1", status="published")
        removed = export_published(self.repo)
        self.assertFalse((self.repo / "static/img/news/old.png").exists())
        self.assertFalse((self.repo / "static/img/news/dr-1.png").exists())
        self.assertIn("static/img/news/old.png", removed)

    def test_export_reports_missing_image_file(self):
        a = self.make(slug="gone-1", status="published", image=SimpleUploadedFile("g.png", b"d"),
                      image_alt="a")
        Path(a.image.path).unlink()
        with self.assertRaises(ExportError) as cm:
            export_published(self.repo)
        self.assertIn("gone-1", str(cm.exception))
        self.assertIn("g", str(cm.exception))
        self.assertFalse((self.repo / "content/news.json").exists())

    def test_clean_tolerates_missing_image_file(self):
        a = self.make(slug="gone-2", image=SimpleUploadedFile("g.png", b"d"), image_alt="a")
        Path(a.image.path).unlink()
        a.clean()  # must not raise FileNotFoundError


class ImportTests(TestCase):
    def test_import_news_idempotent(self):
        items = [
            NewsItem("alpha", datetime.date(2026, 4, 1), "お知らせ", "アルファ", "概要A", "<p>a</p>", "a"),
            NewsItem("beta-1", datetime.date(2026, 5, 2), "出版", "ベータ", "概要B", "<p>b</p>", "b"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "news.json"
            path.write_text(news_to_json(items), encoding="utf-8")
            for _ in range(2):
                call_command("import_news", "--path", str(path), stdout=StringIO())
            self.assertEqual(Article.objects.count(), 2)
            self.assertEqual(set(Article.objects.values_list("status", flat=True)), {"published"})
            self.assertEqual({a.slug for a in Article.objects.all()}, {i.slug for i in load_news(path)})
        a = Article.objects.get(slug="alpha")
        self.assertEqual(a.published_on, datetime.date(2026, 4, 1))
