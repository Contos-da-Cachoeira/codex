from urllib.parse import urlsplit

from django.conf import settings
from django.http import Http404
from django.views.defaults import page_not_found


class DevelopmentNotFoundMiddleware:
    """Show the site's 404 page for browser navigation with DEBUG enabled too."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.DEBUG or response.status_code != 404:
            return response

        # Keep file errors and background requests in their original format.
        asset_paths = (
            urlsplit(settings.STATIC_URL).path,
            urlsplit(settings.MEDIA_URL).path,
        )
        if (
            response.get("Content-Type", "").split(";", 1)[0] != "text/html"
            or not request.accepts("text/html")
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.headers.get("X-Admin-Panel")
            or request.headers.get("Sec-Fetch-Dest", "") not in ("", "document", "iframe")
            or any(prefix and request.path.startswith(prefix) for prefix in asset_paths)
        ):
            return response

        return page_not_found(request, Http404())
