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
        self.media = reverse('press:preview_media', args=['news/private.png'])

    def grant(self, codename):
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label='press', codename=codename))
        self.client.force_login(self.user)

    def test_staff_without_article_permissions_cannot_read_or_publish(self):
        self.client.force_login(self.user)
        with patch('press.views.publish') as publish:
            for url in (self.preview, self.media):
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

    def test_media_route_requires_authentication_and_allows_viewers(self):
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=Path(tmp)):
            (Path(tmp) / 'news').mkdir()
            (Path(tmp) / 'news/private.png').write_bytes(b'private image')
            self.assertEqual(self.media, '/media/news/private.png')
            self.assertEqual(self.client.get(self.media).status_code, 302)
            self.grant('view_article')
            response = self.client.get(self.media)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'private image')
            self.assertIn('no-store', response['Cache-Control'])

    def test_removed_preview_media_route_is_not_served(self):
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=Path(tmp)):
            (Path(tmp) / 'news').mkdir()
            (Path(tmp) / 'news/private.png').write_bytes(b'private image')
            old_url = '/preview/media/news/private.png'
            self.assertEqual(self.client.get(old_url).status_code, 404)
            self.grant('view_article')
            self.assertEqual(self.client.get(old_url).status_code, 404)

    def test_publish_rejects_post_without_csrf_and_unsupported_methods(self):
        self.grant('change_article')
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        with patch('press.views.publish') as publish:
            self.assertEqual(client.post(self.publish).status_code, 403)
            self.assertEqual(self.client.delete(self.publish).status_code, 405)
            publish.assert_not_called()
