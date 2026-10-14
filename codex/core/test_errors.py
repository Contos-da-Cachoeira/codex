from django.http import Http404, HttpResponse, JsonResponse
from django.test import TestCase, override_settings
from django.urls import include, path


def missing_content(request):
    raise Http404("Internal detail that should not appear on the error page")


def missing_json(request):
    return JsonResponse({"error": "missing"}, status=404)


def existing_page(request):
    return HttpResponse("Existing page")


urlpatterns = [
    path("_404-tests/content/", missing_content),
    path("_404-tests/json/", missing_json),
    path("_404-tests/existing/", existing_page),
    path("", include("codex.urls")),
]


@override_settings(ROOT_URLCONF=__name__, ALLOWED_HOSTS=["testserver"])
class NotFoundPageTests(TestCase):
    def test_unknown_address_and_missing_content_show_custom_page_in_both_modes(self):
        for debug in (True, False):
            for url in (
                "/a-page-that-does-not-exist/",
                "/_404-tests/content/",
                "/wiki/classes/a-class-that-does-not-exist/",
            ):
                with self.subTest(debug=debug, url=url), override_settings(DEBUG=debug):
                    response = self.client.get(url, HTTP_ACCEPT="text/html")
                    self.assertContains(response, "Página não encontrada", status_code=404)
                    self.assertTemplateUsed(response, "404.html")
                    self.assertEqual(response["X-Frame-Options"], "DENY")
                    self.assertContains(response, 'href="/"', status_code=404)
                    self.assertContains(response, 'href="/wiki/"', status_code=404)
                    self.assertContains(response, 'name="robots" content="noindex"', status_code=404)
                    self.assertNotContains(response, "Internal detail", status_code=404)
                    self.assertNotContains(response, "URLconf", status_code=404)

    def test_json_404_responses_are_preserved(self):
        for debug in (True, False):
            with self.subTest(debug=debug), override_settings(DEBUG=debug):
                response = self.client.get("/_404-tests/json/")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json(), {"error": "missing"})
                self.assertTemplateNotUsed(response, "404.html")

    @override_settings(DEBUG=True, STATIC_URL="/static/", MEDIA_URL="https://example.com/media/")
    def test_debug_file_and_background_errors_are_preserved(self):
        for url, headers in (
            ("/static/missing.css", {}),
            ("/media/missing.png", {}),
            ("/_404-tests/content/", {"HTTP_ACCEPT": "application/json"}),
            ("/_404-tests/content/", {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}),
            ("/_404-tests/content/", {"HTTP_X_ADMIN_PANEL": "wiki_panel"}),
            ("/_404-tests/content/", {"HTTP_SEC_FETCH_DEST": "image"}),
        ):
            with self.subTest(url=url, headers=headers):
                response = self.client.get(url, **headers)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateNotUsed(response, "404.html")

    @override_settings(DEBUG=True, APPEND_SLASH=True)
    def test_existing_pages_and_slash_redirects_keep_working(self):
        self.assertContains(self.client.get("/_404-tests/existing/"), "Existing page")
        self.assertRedirects(
            self.client.get("/_404-tests/existing"),
            "/_404-tests/existing/",
            status_code=301,
        )

    def test_head_uses_404_without_a_response_body(self):
        response = self.client.head("/a-page-that-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertEqual(response.content, b"")
