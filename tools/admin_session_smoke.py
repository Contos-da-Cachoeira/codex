"""Exercise saves against an isolated Django server, without real accounts or data."""
import os
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'codex'
sys.path.insert(0, str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from django.utils import timezone
from playwright.sync_api import sync_playwright
from core.models import LarpEvento, Profile
from personagens.models import Personagem
from wiki.models import WikiEntry


class AdminSessionSmoke(StaticLiveServerTestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin-test', is_staff=True)
        self.player = User.objects.create_user('ana-test')
        self.other = User.objects.create_user('bruno-test')
        Profile.objects.update_or_create(user=self.player, defaults={'nome_completo_jogador': 'Ana — teste', 'xp_disponivel': 10})
        self.character = Personagem.objects.create(usuario=self.player, nome='Personagem em teste', classe=1, guilda=1, xp_atual=10)
        self.other_character = Personagem.objects.create(usuario=self.other, nome='Segundo personagem', classe=2)
        self.event = LarpEvento.objects.create(titulo='Evento em teste', local='Local de teste', historia='História de teste',
            data_evento=timezone.now() + timedelta(days=20), data_limite_inscricao=timezone.now() + timedelta(days=19))
        self.client.force_login(self.admin)

    def test_clean_address_and_background_saves(self):
        base = self.live_server_url + '/area-admin/'
        cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        character_pk, user_pk, event_pk = self.character.pk, self.player.pk, self.event.pk
        valid_deadline = (timezone.now() + timedelta(days=15)).strftime('%Y-%m-%dT%H:%M')
        invalid_deadline = (timezone.now() + timedelta(days=25)).strftime('%Y-%m-%dT%H:%M')
        event_date = (timezone.now() + timedelta(days=20)).strftime('%Y-%m-%dT%H:%M')
        documents, errors = [], []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width': 1600, 'height': 1000})
            context.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': cookie, 'url': self.live_server_url}])
            page = context.new_page()
            page.on('request', lambda request: documents.append(request.url) if request.resource_type == 'document' else None)
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + f'?selected_user={user_pk}#home_components_modal', wait_until='networkidle')
            self.assertEqual(page.url, base)
            self.assertEqual(page.get_by_role('tab', name='Página inicial', exact=True).get_attribute('aria-selected'), 'true')

            def panel_json(response, tab):
                return response.headers.get('x-admin-panel') == tab and 'application/json' in response.headers.get('content-type', '')

            def select(kind, pk):
                manager = page.locator(f'[data-record-manager="{kind}"]')
                row = manager.locator(f'[data-record-select="{pk}"]')
                row.evaluate('(element) => element.closest("details").open = true')
                row.click()
                self.assertEqual(page.url, base)
                return manager

            page.get_by_role('tab', name='Usuários', exact=True).click()
            users = select('users', user_pk)
            users.locator('[data-record-detail] [data-record-edit]').click()
            users.locator(f'[data-record-detail] select[name="role_{user_pk}"]').select_option('ADMIN')
            with page.expect_response(lambda response: panel_json(response, 'user_roles_modal')):
                users.get_by_role('button', name='Salvar tipo da conta').click()
            users.locator('[data-record-detail] .admin-records-eyebrow').get_by_text('Admin', exact=True).wait_for()
            self.assertEqual(page.url, base)

            page.get_by_role('tab', name='Personagens', exact=True).click()
            characters = select('characters', self.other_character.pk)
            characters.locator('[data-record-detail] [data-record-edit]').click()
            characters.locator(f'[name="xp_atual_{self.other_character.pk}"]').fill('77')
            characters = select('characters', character_pk)
            characters.locator('[data-record-detail] [data-record-edit]').click()
            characters.locator(f'[name="xp_atual_{character_pk}"]').fill('125')
            page.get_by_role('tab', name='Página inicial', exact=True).click()
            self.assertEqual(page.url, base)
            page.get_by_role('tab', name='Personagens', exact=True).click()
            self.assertEqual(characters.locator(f'[name="xp_atual_{character_pk}"]').input_value(), '125')
            with page.expect_response(lambda response: panel_json(response, 'character_modal')):
                characters.get_by_role('button', name='Salvar personagem').click()
                page.get_by_role('tab', name='Página inicial', exact=True).click()
            self.assertEqual(page.get_by_role('tab', name='Página inicial', exact=True).get_attribute('aria-selected'), 'true')
            page.get_by_role('tab', name='Personagens', exact=True).click()
            characters.locator('[data-record-read-fields]').get_by_text('125', exact=True).wait_for()
            select('characters', self.other_character.pk)
            self.assertEqual(characters.locator(f'[name="xp_atual_{self.other_character.pk}"]').input_value(), '77')
            characters.locator('[data-record-detail] [data-record-cancel]').click()
            select('characters', character_pk)

            # Filtering is a background request and does not alter the address.
            with page.expect_response(lambda response: panel_json(response, 'character_modal')):
                characters.locator('[name="character_q"]').fill('Personagem em teste')
                characters.get_by_role('button', name='Filtrar', exact=True).click()
            page.wait_for_function("document.querySelectorAll('[data-record-manager=characters] [data-record-select]').length === 1")
            self.assertEqual(page.url, base)

            page.get_by_role('tab', name='LARPs', exact=True).click()
            larps = select('larps', event_pk)
            larps.locator('[data-record-detail] [data-record-edit]').click()
            larps.locator('[data-record-detail] [name="titulo"]').fill('Evento atualizado')
            larps.locator('[data-record-detail] [name="data_limite_inscricao"]').fill(invalid_deadline)
            with page.expect_response(lambda response: panel_json(response, 'larp_modal')):
                larps.get_by_role('button', name='Salvar evento', exact=True).click()
            larps.locator('[data-record-edit-fields] .errorlist').wait_for()
            self.assertEqual(larps.locator('[data-record-detail] [name="titulo"]').input_value(), 'Evento atualizado')
            larps.locator('[data-record-detail] [name="data_limite_inscricao"]').fill(valid_deadline)
            with page.expect_response(lambda response: panel_json(response, 'larp_modal')):
                larps.get_by_role('button', name='Salvar evento', exact=True).click()
            larps.locator('[data-record-detail] h3').get_by_text('Evento atualizado', exact=True).wait_for()

            larps.locator('[data-record-new]').click()
            for name, value in {'titulo': 'Evento novo sem recarga', 'local': 'Vila', 'historia': 'História nova',
                                'data_evento': event_date, 'data_limite_inscricao': valid_deadline}.items():
                larps.locator(f'[data-record-detail] [name="{name}"]').fill(value)
            with page.expect_response(lambda response: panel_json(response, 'larp_modal')):
                larps.locator('[data-record-detail] form').evaluate('(form) => { form.requestSubmit(); form.requestSubmit(); }')
            larps.locator('[data-record-detail] h3').get_by_text('Evento novo sem recarga', exact=True).wait_for()

            page.get_by_role('tab', name='Wiki', exact=True).click()
            wiki = page.locator('[data-wiki-manager]')
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                wiki.locator('[data-wiki-create]').click()
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                page.get_by_role('navigation', name='Seção do novo conteúdo').get_by_role('link', name='Itens', exact=True).click()
            wiki = page.locator('[data-wiki-manager]')
            for name, value in {'name': 'Item sem recarga', 'slug': 'item-sem-recarga', 'descricao': 'Dados de teste.'}.items():
                wiki.locator(f'[name="{name}"]').fill(value)
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                wiki.get_by_role('button', name='Salvar conteúdo', exact=True).click()
            page.locator('[data-wiki-detail] h3').get_by_text('Item sem recarga', exact=True).wait_for()
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                page.locator('[data-wiki-detail]').get_by_role('button', name='Publicar', exact=True).click()
            page.locator('[data-wiki-detail]').get_by_text('Publicado para os jogadores', exact=True).wait_for()
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                page.locator('[data-wiki-detail]').get_by_role('link', name='Editar', exact=True).click()
            page.locator('[data-wiki-detail] [name="descricao"]').fill('Descrição atualizada em segundo plano.')
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                page.locator('[data-wiki-detail]').get_by_role('button', name='Salvar conteúdo', exact=True).click()
            page.locator('[data-wiki-detail]').get_by_text('Descrição atualizada em segundo plano.', exact=True).wait_for()
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                page.locator('[data-wiki-detail]').get_by_role('link', name='Excluir', exact=True).click()
            with page.expect_response(lambda response: panel_json(response, 'wiki_panel')):
                page.locator('[data-wiki-detail]').get_by_role('button', name='Confirmar exclusão', exact=True).click()
            page.wait_for_function("![...document.querySelectorAll('[data-wiki-select] strong')].some(element => element.textContent === 'Item sem recarga')")

            page.get_by_role('tab', name='Aparência', exact=True).click()
            theme = page.locator('#theme_modal')
            theme.locator('[name="primary_color"]').fill('#112233')
            theme.locator('[name="site_muted_text_color"]').fill('#aabbcc')
            with page.expect_response(lambda response: panel_json(response, 'theme_modal')):
                theme.get_by_role('button', name='Salvar cores', exact=True).click()
            page.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() === '#112233'")
            page.wait_for_function("getComputedStyle(document.documentElement).getPropertyValue('--site-muted').trim().toLowerCase() === '#aabbcc'")
            page.get_by_role('tab', name='Redes sociais', exact=True).click()
            social = page.locator('#social_modal')
            social.locator('[name="social_instagram_url"]').fill('https://example.com/team')
            with page.expect_response(lambda response: panel_json(response, 'social_modal')):
                social.get_by_role('button', name='Salvar redes sociais', exact=True).click()

            # A network error must keep the edited values available for retry.
            page.get_by_role('tab', name='Personagens', exact=True).click()
            characters.locator('[data-record-detail] [data-record-edit]').click()
            characters.locator(f'[name="xp_atual_{character_pk}"]').fill('333')
            page.route('**/area-admin/**', lambda route: route.abort() if route.request.method == 'POST' else route.continue_())
            characters.get_by_role('button', name='Salvar personagem').click()
            page.locator('[data-admin-feedback]').get_by_text('Não foi possível comunicar com o servidor.', exact=False).wait_for()
            self.assertEqual(characters.locator(f'[name="xp_atual_{character_pk}"]').input_value(), '333')
            self.assertTrue(characters.get_by_role('button', name='Salvar personagem').is_enabled())
            page.unroute('**/area-admin/**')
            self.assertEqual(page.url, base)
            self.assertEqual(len(documents), 1, documents)
            self.assertFalse(errors, errors)
            page.reload(wait_until='networkidle')
            self.assertEqual(page.get_by_role('tab', name='Personagens', exact=True).get_attribute('aria-selected'), 'true')
            self.assertEqual(page.url, base)
            browser.close()
        self.character.refresh_from_db()
        self.player.refresh_from_db()
        self.event.refresh_from_db()
        self.assertEqual(self.character.xp_jogador, 125)
        self.assertTrue(self.player.is_staff)
        self.assertEqual(self.event.titulo, 'Evento atualizado')
        self.assertEqual(LarpEvento.objects.filter(titulo='Evento novo sem recarga').count(), 1)
        self.assertFalse(WikiEntry.objects.filter(slug='item-sem-recarga').exists())
        print('PASS: clean address; saves, filters, wiki navigation and validation without document reload; network errors retain inputs.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1, interactive=False).run_tests(['__main__.AdminSessionSmoke'])))
