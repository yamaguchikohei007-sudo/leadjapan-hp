from django.contrib import admin
from django.urls import include, path

from press.views import preview_media

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("press.urls")),
    path("media/<path:path>", preview_media, name="protected_media"),
]
