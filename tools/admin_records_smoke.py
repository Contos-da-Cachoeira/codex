"""Render and exercise admin catalogs with synthetic data and an isolated browser.

Requires Playwright and installed Chrome. Uses an in-memory database, no live sessions.
"""
import json
import mimetypes
import os
import sys
from datetime import timedelta
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
from django.utils import timezone
from playwright.sync_api import sync_playwright
from core.models import ImageAsset, LarpEvento, Profile
from personagens.models import Personagem
from wiki.constants.classes import CLASSES_WIKI

call_command('migrate', verbosity=0)
admin = User.objects.create_user('admin-teste', is_staff=True)
players, characters, events = [], [], []
for index, (name, class_key, class_id) in enumerate([('Ana', 'BARDO', 2), ('Bruno', 'GUERREIRO', 6), ('Clara', 'MAGO', 8)]):
    user = User.objects.create_user(name.lower(), email=f'{name.lower()}@example.com')
    Profile.objects.update_or_create(user=user, defaults={'nome_completo_jogador': f'{name} — conta de teste', 'apelido_cla': 'Aventureiros', 'fobia_gatilho': 'Informação de exemplo.'})
    asset = ImageAsset.objects.create(owner=user, url='/static/' + CLASSES_WIKI[class_key]['imagem'])
    character = Personagem.objects.create(usuario=user, nome=['Melodia da Cachoeira', 'Guardião da Floresta', 'Estrela do Crepúsculo'][index],
        classe=class_id, guilda=index + 1, image_asset=asset, status_aprovacao=index + 1, xp_atual=75 + index * 25, ouro=30,
        historia='Um aventureiro que partiu em busca dos mistérios da Cachoeira.', objetivos='Proteger seus aliados e explorar novas terras.',
        aparencia='Trajes de viagem e equipamentos de sua classe.', personalidade='Determinado, curioso e leal aos amigos.')
    event = LarpEvento.objects.create(titulo=['Contos da Cachoeira', 'O segredo da floresta', 'Encontro dos aventureiros'][index],
        local=['Parque Central', 'Floresta do Sol', 'Praça da Vila'][index], historia='Uma nova aventura reúne as guildas.\nEscolhas e alianças definirão o destino da jornada.',
        data_evento=timezone.now() + timedelta(days=10 + index), data_limite_inscricao=timezone.now() + timedelta(days=8 + index),
        visivel_publicamente=index != 1, criado_por=admin)
    players.append(user); characters.append(character); events.append(event)

client = Client()
client.force_login(admin)
with override_settings(ALLOWED_HOSTS=['testserver']):
    html = client.get('/area-admin/').content
    empty_html = client.get('/area-admin/', {'larp_q': 'sem-nenhum-evento'}).content
output = ROOT / 'media' / 'admin-records-qa'
output.mkdir(parents=True, exist_ok=True)
document_requests = []


def serve(route):
    request = route.request
    url = urlparse(request.url)
    if request.resource_type == 'document':
        document_requests.append(request.url)
    if url.netloc != 'testserver':
        route.continue_()
    elif url.path == '/area-admin/':
        route.fulfill(body=empty_html if 'sem-nenhum-evento' in url.query else html, content_type='text/html')
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
    page.goto('http://testserver/area-admin/#user_roles_modal', wait_until='networkidle')
    page.evaluate("window.originalCatalogs = [...document.querySelectorAll('[data-record-scroll]')]")

    def select(manager, pk):
        row = manager.locator(f'[data-record-select="{pk}"]')
        row.evaluate('(element) => element.closest("details").open = true')
        row.scroll_into_view_if_needed()
        previous_scroll = manager.locator('[data-record-scroll]').evaluate('(element) => element.scrollTop')
        row.click()
        manager.locator(f'[data-record-detail] [data-record-id="{pk}"]').wait_for(state='visible')
        assert manager.locator('[data-record-select][aria-current="true"]').get_attribute('data-record-select') == str(pk)
        assert manager.locator('[data-record-scroll]').evaluate('(element) => element.scrollTop') == previous_scroll

    for kind, tab, records, field, value in [
        ('users', 'Usuários', players, f'role_{players[0].pk}', 'ADMIN'),
        ('characters', 'Personagens', characters, f'xp_atual_{characters[0].pk}', '125'),
        ('larps', 'LARPs', events, 'titulo', 'Título em edição'),
    ]:
        page.get_by_role('tab', name=tab, exact=True).click()
        manager = page.locator(f'[data-record-manager="{kind}"]')
        select(manager, records[0].pk)
        catalog = manager.locator('.admin-records-catalog').bounding_box()
        detail = manager.locator('.admin-records-detail').bounding_box()
        assert catalog['x'] + catalog['width'] < detail['x']
        page.screenshot(path=str(output / f'{kind}.png'), full_page=True)
        manager.locator('[data-record-detail] [data-record-edit]').click()
        field_locator = manager.locator(f'[data-record-detail] [name="{field}"]')
        if kind == 'users':
            field_locator.select_option(value)
        else:
            field_locator.fill(value)
        select(manager, records[1].pk)
        select(manager, records[0].pk)
        assert manager.locator(f'[data-record-detail] [name="{field}"]').input_value() == value
        manager.locator('[data-record-detail] [data-record-cancel]').click()
        assert manager.locator('[data-record-read-fields]').is_visible()
        assert not manager.locator('[data-record-detail] [data-record-edit-fields]').is_visible()
        select(manager, records[1].pk)
        assert page.url == 'http://testserver/area-admin/'

    larps = page.locator('[data-record-manager="larps"]')
    larps.locator('[data-record-new]').click()
    larps.locator('[data-record-detail] input[name="titulo"]').fill('Novo evento em rascunho')
    select(larps, events[0].pk)
    larps.locator('[data-record-new]').click()
    assert larps.locator('[data-record-detail] input[name="titulo"]').input_value() == 'Novo evento em rascunho'
    larps.locator('[data-record-detail] [data-record-cancel]').click()
    assert len(document_requests) == 1, document_requests
    assert page.evaluate("window.originalCatalogs.every(element => element.isConnected)")
    page.set_viewport_size({'width': 390, 'height': 844})
    for kind, tab in [('users', 'Usuários'), ('characters', 'Personagens'), ('larps', 'LARPs')]:
        page.get_by_role('tab', name=tab, exact=True).click()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), kind
    page.screenshot(path=str(output / 'mobile.png'), full_page=True)
    page.goto('http://testserver/area-admin/?larp_q=sem-nenhum-evento#larp_modal', wait_until='networkidle')
    larps.locator('[data-record-new]').click()
    larps.locator('[data-record-detail] [data-record-cancel]').click()
    assert larps.locator('[data-record-detail]').inner_text() == 'Selecione um registro na lista ou ajuste os filtros.'
    assert not errors, errors
    print(json.dumps({'catalogs': 3, 'selection_document_loads': 1, 'drafts_and_clean_address': 'passed',
                      'mobile_no_overflow': True, 'empty_catalog_cancel': 'passed', 'screenshots': str(output)}, ensure_ascii=False))
    browser.close()
