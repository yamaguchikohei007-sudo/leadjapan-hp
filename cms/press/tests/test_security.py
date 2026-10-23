import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .test_models import make_article


class AccessControlTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('staff', is_staff=True)
        self.article = make_article(slug='private-draft', title='Private draft')
        self.article.save()
        self.preview = reverse('press:preview', args=[self.article.pk])
        self.publish = reverse('admin:press_article_publish')

    def grant(self, codename):
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label='press', codename=codename))
        self.client.force_login(self.user)

    def test_staff_without_article_permissions_cannot_read_or_publish(self):
        self.client.force_login(self.user)
        with patch('press.views.publish') as publish:
            for url in (self.preview, '/preview/media/news/private.png', '/media/news/private.png'):
                self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(self.publish).status_code, 403)
            publish.assert_not_called()

    def test_viewer_can_preview_but_cannot_publish(self):
        self.grant('view_article')
        response = self.client.get(self.preview)
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        with patch('press.views.publish') as publish:
            self.assertEqual(self.client.post(self.publish).status_code, 403)
            publish.assert_not_called()
        response = self.client.get(reverse('admin:press_article_changelist'))
        self.assertNotContains(response, self.publish)

    def test_both_media_routes_require_authentication_and_allow_viewers(self):
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=Path(tmp)):
            (Path(tmp) / 'news').mkdir()
            (Path(tmp) / 'news/private.png').write_bytes(b'private image')
            for url in ('/media/news/private.png', '/preview/media/news/private.png'):
                self.client.logout()
                self.assertEqual(self.client.get(url).status_code, 302)
                self.grant('view_article')
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), b'private image')
                self.assertIn('no-store', response['Cache-Control'])

    def test_publish_rejects_post_without_csrf_and_unsupported_methods(self):
        self.grant('change_article')
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        with patch('press.views.publish') as publish:
            self.assertEqual(client.post(self.publish).status_code, 403)
            self.assertEqual(self.client.delete(self.publish).status_code, 405)
            publish.assert_not_called()

    def test_preview_routes_preserve_login_redirect_and_permission_boundary(self):
        urls = (self.preview, '/preview/static/css/style.css',
                '/preview/media/news/private.png', '/media/news/private.png')
        for url in urls:
            with self.subTest(url=url, role='anonymous'):
                response = self.client.get(url)
                self.assertRedirects(response, reverse('admin:login') + '?next=' + url,
                                     fetch_redirect_response=False)
        self.grant('view_article')
        for active, staff in ((True, False), (False, True)):
            self.user.is_active, self.user.is_staff = active, staff
            self.user.save()
            self.client.force_login(self.user)
            for url in urls:
                with self.subTest(url=url, active=active, staff=staff):
                    self.assertEqual(self.client.get(url).status_code, 302)

    def test_authorized_static_preview_preserves_content_and_cache_headers(self):
        self.grant('view_article')
        response = self.client.get('/preview/static/css/style.css')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/css'))
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('private', response['Cache-Control'])
        from django.conf import settings
        self.assertEqual(b''.join(response.streaming_content),
                         (settings.REPO_ROOT / 'static/css/style.css').read_bytes())

    def test_authorized_missing_preview_resources_remain_not_found(self):
        self.grant('view_article')
        for url in (reverse('press:preview', args=[999999]),
                    '/preview/static/nonexistent.css',
                    '/preview/media/nonexistent.png', '/media/nonexistent.png'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
