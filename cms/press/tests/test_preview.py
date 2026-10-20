import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from press.models import Article
from press.tests.test_models import make_article


class PreviewTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        ov = override_settings(MEDIA_ROOT=Path(self._tmp.name))
        ov.enable()
        self.addCleanup(ov.disable)
        self.article = make_article(slug="draft-1", title="下書きの記事", body_md="**太字**の本文")
        self.article.save()
        self.url = reverse("press:preview", args=[self.article.pk])

    def login(self):
        user = get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        self.client.force_login(user)

    def test_preview_requires_staff(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("admin:login"), r["Location"])

    def test_preview_renders_draft_with_site_layout(self):
        self.login()
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        self.assertIn("下書きの記事 | Lead Japan 合同会社", html)
        self.assertIn("<strong>太字</strong>", html)
        self.assertIn('href="/static/css/style.css"', html)

    def test_preview_missing_is_404(self):
        self.login()
        self.assertEqual(self.client.get(reverse("press:preview", args=[99999])).status_code, 404)

    def test_preview_static_served(self):
        # same root-relative path the published pages use
        self.login()
        r = self.client.get("/static/css/style.css")
        self.assertEqual(r.status_code, 200)

    def test_preview_static_requires_staff(self):
        self.assertEqual(self.client.get("/static/css/style.css").status_code, 302)

    def test_preview_media_requires_staff(self):
        self.assertEqual(self.client.get("/media/news/p.png").status_code, 302)

    def test_preview_static_traversal_is_404(self):
        self.login()
        for path in ("/static/../build.py", "/static/%2e%2e/build.py", "/media/../db.sqlite3"):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertIn(r.status_code, (400, 404))  # never 200

    def test_preview_uses_media_image(self):
        self.login()
        (Path(self._tmp.name) / "news").mkdir()
        (Path(self._tmp.name) / "news/p.png").write_bytes(b"png")
        Article.objects.filter(pk=self.article.pk).update(image="news/p.png", image_alt="alt")
        html = self.client.get(self.url).content.decode()
        self.assertIn('src="/media/news/p.png"', html)
        self.assertEqual(self.client.get("/media/news/p.png").status_code, 200)

    def test_change_form_has_preview_link(self):
        self.login()
        r = self.client.get(reverse("admin:press_article_change", args=[self.article.pk]))
        self.assertContains(r, self.url)
        self.assertContains(r, "プレビュー")

    def test_add_form_has_no_preview_link(self):
        self.login()
        r = self.client.get(reverse("admin:press_article_add"))
        self.assertNotContains(r, "プレビュー")
