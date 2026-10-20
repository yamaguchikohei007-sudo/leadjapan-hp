from django.urls import path

from . import views

app_name = "press"

# /static/ and /media/ match the root-relative paths the site pages use.
urlpatterns = [
    path("static/<path:path>", views.preview_static, name="preview_static"),
    path("media/<path:path>", views.preview_media, name="preview_media"),
    path("preview/<int:pk>.html", views.preview, name="preview"),
]
