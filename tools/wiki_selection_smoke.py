"""Check instant wiki selection in an isolated database and headless browser.

Run from the repository root with the project Python. Requires Playwright and Chrome.
No production data, browser profile, or application server is used.
"""
import json
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent / 'codex'
sys.path.insert(0, str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
import django
django.setup()
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import Client, override_settings
from playwright.sync_api import sync_playwright
from wiki.editor import panel_url
from wiki.models import WikiEntry

call_command('migrate', verbosity=0)
admin = User.objects.create_user('wiki-browser-test', is_staff=True)
client = Client()
client.force_login(admin)
classes = list(WikiEntry.objects.filter(category='classes')[:3])
item = WikiEntry.objects.filter(category='itens').first()
with override_settings(ALLOWED_HOSTS=['testserver']):
    response = client.get(panel_url())
    assert response.status_code == 200
    html = response.content

document_requests = []
data_requests = []


def serve(route):
    request = route.request
    url = urlparse(request.url)
    if request.resource_type == 'document':
        document_requests.append(request.url)
    if request.resource_type in {'fetch', 'xhr'}:
        data_requests.append(request.url)
    if url.netloc != 'testserver':
        route.continue_()
    elif url.path == '/area-admin/':
        route.fulfill(body=html, content_type='text/html')
    elif url.path.startswith('/static/') and (path := finders.find(url.path[len('/static/'):])):
        route.fulfill(body=Path(path).read_bytes(), content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
    else:
        route.fulfill(status=404, body='')


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/*', serve)
    page.goto('http://testserver' + panel_url(), wait_until='networkidle')
    page.locator('#wiki_panel').wait_for(state='visible')
    page.evaluate("window.wikiOriginalCatalog = document.querySelector('[data-wiki-catalog-scroll]')")

    def assert_selected(entry):
        page.locator(f'[data-wiki-detail] [data-wiki-item="{entry.pk}"]').wait_for(state='visible')
        assert page.locator('[data-wiki-detail] h3').inner_text() == entry.name
        assert page.locator('[data-wiki-select][aria-current="true"]').get_attribute('data-wiki-select') == str(entry.pk)
        assert page.locator('[data-wiki-detail] input[name="wiki_id"]').input_value() == str(entry.pk)
        assert f'wiki_id={entry.pk}' in page.locator('[data-wiki-detail] a', has_text='Editar').get_attribute('href')
        assert page.locator('[data-wiki-detail] input[name="csrfmiddlewaretoken"]').input_value()

    def select(entry):
        row = page.locator(f'[data-wiki-select="{entry.pk}"]')
        row.scroll_into_view_if_needed()
        scroll_before = page.locator('[data-wiki-catalog-scroll]').evaluate('(element) => element.scrollTop')
        row.click()
        assert_selected(entry)
        assert page.locator('[data-wiki-catalog-scroll]').evaluate('(element) => element.scrollTop') == scroll_before

    select(classes[1])
    select(classes[2])
    assert page.url == 'http://testserver/area-admin/'
    page.evaluate('(ids) => ids.forEach(id => document.querySelector(`[data-wiki-select="${id}"]`).click())',
                  [classes[1].pk, classes[2].pk, classes[1].pk])
    assert_selected(classes[1])
    page.locator('[data-wiki-group="itens"] summary').click()
    select(item)
    assert page.locator('[data-wiki-group="classes"]').get_attribute('open') is not None
    assert page.locator('[data-wiki-group="itens"]').get_attribute('open') is not None
    assert page.evaluate("window.wikiOriginalCatalog === document.querySelector('[data-wiki-catalog-scroll]')")
    assert len(document_requests) == 1, document_requests
    assert not [url for url in data_requests if url.startswith('http://testserver/area-admin/?wiki_selected')], data_requests
    assert not errors, errors
    print(json.dumps({'document_loads': len(document_requests), 'selection_requests': 0,
                      'catalog_preserved': True, 'clean_address_and_rapid_clicks': 'passed'}, ensure_ascii=False))
    browser.close()
