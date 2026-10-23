from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html
from django.views.static import serve
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from sitegen.pages import article_page_title, body_news_article
from sitegen.render import render_layout

from .export import article_to_newsitem
from .models import Article
from .publish import publish


def _article_preview(view):
    """Require active staff and article access before serving uncached previews."""
    uncached_view = never_cache(view)
    authorized_view = permission_required(
        "press.view_article", raise_exception=True
    )(uncached_view)
    return staff_member_required(authorized_view)


@_article_preview
def preview(request, pk):
    article = get_object_or_404(Article, pk=pk)
    item = article_to_newsitem(article, image=None)
    image_src = article.image.url if article.image else None
    html = render_layout(
        title=article_page_title(item.title),
        description=item.summary,
        body=body_news_article(item, image_src=image_src),
        current="news.html",
    )
    return HttpResponse(html)


@_article_preview
def preview_static(request, path):
    return serve(request, path, document_root=settings.REPO_ROOT / "static")


@_article_preview
def preview_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@staff_member_required
@permission_required("press.change_article", raise_exception=True)
@csrf_protect
@require_http_methods(["GET", "POST"])
def publish_view(request):
    if request.method != "POST":
        return render(request, "admin/press/article/publish.html", {**admin.site.each_context(request),
                                                                      "title": "サイトに反映"})
    result = publish(settings.REPO_ROOT)
    level = {"pr_created": messages.SUCCESS, "pr_updated": messages.SUCCESS, "pr_closed": messages.INFO,
             "no_changes": messages.INFO,
             "push_failed": messages.WARNING, "pr_failed": messages.WARNING}.get(result.status, messages.ERROR)
    text = format_html("{}", result.message)
    if result.url:
        text = format_html('{} <a href="{}" target="_blank" rel="noopener">{}</a>', text, result.url, result.url)
    if result.output:
        text = format_html("{}<pre>{}</pre>", text, result.output)
    messages.add_message(request, level, text)
    return redirect("admin:press_article_changelist")
