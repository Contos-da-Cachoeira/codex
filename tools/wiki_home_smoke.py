"""Check the public Wiki home in an isolated database and headless browser.

Run from the repository root with the project Python. Requires Playwright and Chrome.
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
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import Client, override_settings
from playwright.sync_api import sync_playwright
from wiki.models import WikiEntry

call_command('migrate', verbosity=0)
secret = WikiEntry.objects.create(category='itens', name='Segredo não publicado', slug='segredo', data={})
pages = {}
client = Client()
with override_settings(ALLOWED_HOSTS=['testserver']):
    for url in ('/wiki/', '/wiki/itens/', '/wiki/classes/', '/wiki/regras/', '/wiki/itens/pocao-da-salamandra/'):
        response = client.get(url)
        assert response.status_code == 200
        pages[url] = response.content
    public_entries = list(WikiEntry.objects.filter(visible=True).exclude(category='magia_geral'))
    class_count = sum(entry.category == 'classes' for entry in public_entries)
    item_count = sum(entry.category == 'itens' for entry in public_entries)
    WikiEntry.objects.update(visible=False)
    pages['/empty-wiki/'] = client.get('/wiki/').content

artifacts = ROOT / 'media' / 'wiki-home-qa'
artifacts.mkdir(parents=True, exist_ok=True)
documents, errors = [], []


def serve(route):
    request = route.request
    url = urlparse(request.url)
    if request.resource_type == 'document':
        documents.append(request.url)
    if url.netloc != 'testserver':
        route.continue_()
    elif url.path in pages:
        route.fulfill(body=pages[url.path], content_type='text/html')
    elif url.path.startswith('/static/') and (file := finders.find(url.path[len('/static/'):])):
        route.fulfill(body=Path(file).read_bytes(), content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream')
    else:
        route.fulfill(status=404, body='<h1>Detalhe do conteúdo</h1>', content_type='text/html')


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/*', serve)
    page.goto('http://testserver/wiki/', wait_until='networkidle')
    search = page.get_by_role('searchbox', name='Buscar na Wiki')
    entries = page.locator('.wh-entry:visible')
    assert page.locator('.wh-section').count() == 5
    assert page.locator('.wh-entry').count() == len(public_entries)
    assert entries.count() == 12
    assert secret.name not in page.content()
    assert not page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    page.screenshot(path=str(artifacts / 'home-desktop.png'), full_page=True)

    page.locator('[data-wiki-more]').click()
    assert entries.count() == 24
    page.locator('[data-wiki-filter="classes"]').click()
    assert entries.count() == class_count
    assert page.locator('[data-wiki-filter="classes"]').get_attribute('aria-pressed') == 'true'
    search.fill('clerigo')
    assert entries.count() == 1
    assert entries.first.locator('h3').inner_text() == 'Clérigo'
    search.fill('mago arcano')
    assert entries.count() == 1
    search.fill('um termo que não existe')
    assert entries.count() == 0
    assert page.locator('[data-wiki-empty]').is_visible()
    page.get_by_role('button', name='Limpar filtros').click()
    assert entries.count() == 12
    assert search.input_value() == ''
    page.locator('[data-wiki-filter="itens"]').click()
    assert entries.count() == min(12, item_count)
    page.locator('[data-wiki-more]').click()
    assert entries.count() == item_count
    assert page.locator('[data-wiki-more]').is_hidden()
    search.fill('salamandra')
    assert entries.count() == 1
    assert entries.first.get_attribute('href') == '/wiki/itens/pocao-da-salamandra/'
    assert len(documents) == 1, documents
    assert page.url == 'http://testserver/wiki/'
    page.screenshot(path=str(artifacts / 'home-filtered.png'), full_page=True)
    with page.expect_navigation() as detail_navigation:
        entries.first.click()
    assert detail_navigation.value.status == 200
    assert page.url.endswith('/wiki/itens/pocao-da-salamandra/')

    page.goto('http://testserver/wiki/', wait_until='networkidle')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert not page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    page.screenshot(path=str(artifacts / 'home-mobile.png'), full_page=True)
    page.screenshot(path=str(artifacts / 'home-mobile-viewport.png'))
    page.locator('[data-wiki-filter="magias"]').click()
    search.fill('bola fogo')
    assert entries.count() == 1
    assert entries.first.locator('h3').inner_text() == 'Bola de Fogo'

    page.set_viewport_size({'width': 768, 'height': 1024})
    search.fill('')
    assert not page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
    page.screenshot(path=str(artifacts / 'home-tablet.png'), full_page=True)

    # The shared search still works on existing section pages.
    page.goto('http://testserver/wiki/itens/', wait_until='networkidle')
    page.locator('[data-wiki-search]').fill('pocao salamandra')
    assert page.locator('[data-wiki-item]:visible').count() == 1
    page.goto('http://testserver/wiki/regras/', wait_until='networkidle')
    page.locator('[data-wiki-search]').fill('personagem ficha')
    assert page.locator('[data-wiki-item]:visible').count() == 1

    page.goto('http://testserver/empty-wiki/', wait_until='networkidle')
    assert page.get_by_text('Conteúdos em preparação', exact=True).is_visible()
    assert page.locator('[data-wiki-empty]').is_hidden()
    assert not page.evaluate('document.documentElement.scrollWidth > window.innerWidth')

    no_js = browser.new_context(java_script_enabled=False)
    no_js.route('**/*', serve)
    fallback = no_js.new_page()
    fallback.goto('http://testserver/wiki/', wait_until='networkidle')
    assert fallback.locator('.wh-entry:visible').count() == len(public_entries)
    assert fallback.locator('[data-wiki-controls]').is_hidden()
    assert not errors, errors
    browser.close()

print(json.dumps({'instant_search_and_filters': 'passed', 'pagination_and_detail_links': 'passed',
                  'desktop_mobile_and_no_javascript': 'passed', 'javascript_errors': errors}, ensure_ascii=False))
