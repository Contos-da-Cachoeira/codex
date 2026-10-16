"""Navegação, acesso e layout das guildas em Chrome com SQLite isolado.

Execute da raiz: codex/.venv/Scripts/python.exe tools/guild_design_smoke.py
As contas, personagens e notícias abaixo existem apenas no banco do teste.
"""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'codex'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
os.environ['AUTO_SSH_DB_TUNNEL'] = '0'

import django
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from playwright.sync_api import expect, sync_playwright

from core.constants.guildas import GUILDAS
from guildas.models import Guilda, GuildaMembro, GuildaNoticia
from guildas.views import GUILDA_PUBLIC_KEY_BY_ID, GUILDA_SLUG_BY_ID
from personagens.consts import STATUS_APROVACAO, STATUS_PERSONAGEM
from personagens.models import Personagem


def normalized(value):
    return ' '.join(value.split())


class GuildDesignSmoke(StaticLiveServerTestCase):
    def assert_no_horizontal_overflow(self, page):
        dimensions = page.evaluate('''() => ({
            viewport: document.documentElement.clientWidth,
            content: document.documentElement.scrollWidth,
        })''')
        self.assertLessEqual(dimensions['content'], dimensions['viewport'] + 1,
                             f'Overflow em {page.url}: {dimensions}')

    def assert_hero_content_fits(self, page):
        hero = page.locator('.guild-hero').bounding_box()
        for selector in ('.guild-hero h1', '.guild-crest img'):
            bounds = page.locator(selector).bounding_box()
            self.assertGreaterEqual(bounds['x'], hero['x'] - 2, f'{selector} cortado em {page.url}')
            self.assertGreaterEqual(bounds['y'], hero['y'] - 2, f'{selector} cortado em {page.url}')
            self.assertLessEqual(bounds['x'] + bounds['width'], hero['x'] + hero['width'] + 2,
                                 f'{selector} cortado em {page.url}')
            self.assertLessEqual(bounds['y'] + bounds['height'], hero['y'] + hero['height'] + 2,
                                 f'{selector} cortado em {page.url}')
        title = page.locator('.guild-hero h1')
        self.assertTrue(title.evaluate('(title) => title.scrollWidth <= title.clientWidth + 2'),
                        f'Título maior que sua área em {page.url}')

    def authenticated_context(self, browser, user):
        self.client.force_login(user)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        context.add_cookies([{
            'name': settings.SESSION_COOKIE_NAME,
            'value': self.client.cookies[settings.SESSION_COOKIE_NAME].value,
            'url': self.live_server_url,
        }])
        return context

    def test_public_design_navigation_and_restricted_content(self):
        # Guard against accidentally running this script against a real database.
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')
        member = User.objects.create_user('guild-design-member')
        outsider = User.objects.create_user('guild-design-outsider')
        admin = User.objects.create_user('guild-design-admin', is_staff=True)
        markers = {}
        for guild_id, slug in GUILDA_SLUG_BY_ID.items():
            secret = f'SEGREDO-GUILDA-FICTICIA-{guild_id}'
            news = f'NOTICIA-GUILDA-FICTICIA-{guild_id}'
            character_name = f'PERSONAGEM-GUILDA-FICTICIA-{guild_id}'
            guild, _ = Guilda.objects.update_or_create(guilda_id=guild_id, defaults={
                'slug': slug, 'ativa': True, 'descricao_interna': secret,
                'total_membros': 1, 'total_personagens': 1,
            })
            GuildaNoticia.objects.create(guilda=guild, titulo=news,
                                        conteudo='Boletim interno fictício.', publicado=True)
            owner = member if guild_id in (1, 7) else User.objects.create_user(f'guild-design-player-{guild_id}')
            Personagem.objects.create(usuario=owner, nome=character_name, classe=1,
                                      guilda=guild_id,
                                      status_aprovacao=STATUS_APROVACAO.APROVADO,
                                      status=STATUS_PERSONAGEM.ATIVO)
            markers[guild_id] = (secret, news, character_name)
            # Even a stale administrative membership must not create a shared
            # private guild for the independent mercenary choice.
            if guild_id in (1, 7):
                GuildaMembro.objects.get_or_create(guilda=guild, usuario=member)

        output = Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Downloads'
        output.mkdir(parents=True, exist_ok=True)
        errors = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1100})
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            response = page.goto(self.live_server_url + '/guildas/', wait_until='networkidle')
            self.assertEqual(response.status, 200)
            self.assert_no_horizontal_overflow(page)
            for slug in GUILDA_SLUG_BY_ID.values():
                expect(page.locator(f'[data-guild-theme="{slug}"]').first).to_be_visible()
                expect(page.locator(f'a[href="/guildas/{slug}/"]').first).to_be_visible()
            page.screenshot(path=str(output / 'codex-guild-design-index-desktop.png'),
                            full_page=True, animations='disabled')
            page.set_viewport_size({'width': 390, 'height': 844})
            self.assert_no_horizontal_overflow(page)
            page.screenshot(path=str(output / 'codex-guild-design-index-mobile.png'),
                            full_page=True, animations='disabled')

            for guild_id, slug in GUILDA_SLUG_BY_ID.items():
                info = GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guild_id]]
                page.set_viewport_size({'width': 1920, 'height': 1100})
                page.goto(self.live_server_url + '/guildas/', wait_until='networkidle')
                page.locator(f'a[href="/guildas/{slug}/"]').first.click()
                page.wait_for_url(self.live_server_url + f'/guildas/{slug}/')
                page.wait_for_load_state('networkidle')
                self.assertEqual(page.request.get(page.url).status, 200)
                public_page = page.locator(f'.guild-page[data-guild-theme="{slug}"]')
                expect(public_page).to_be_visible()
                expect(page.get_by_role('heading', level=1)).to_have_text(info['nome'])
                crest = public_page.locator('.guild-crest img').first
                expect(crest).to_be_visible()
                expect(crest).to_have_attribute('src', f'/static/{info["imagem"]}')
                self.assertTrue(crest.evaluate('(image) => image.complete && image.naturalWidth > 0'),
                                f'Brasão não carregou: {slug}')
                text = normalized(public_page.inner_text())
                for key in ('vantagem', 'vantagem_efeito', 'marca_nome', 'marca_efeito',
                            'saida', 'desvantagem'):
                    if info.get(key):
                        self.assertIn(normalized(info[key]), text, f'{slug}: conteúdo ausente de {key}')
                html = page.content()
                for guild_markers in markers.values():
                    for marker in guild_markers:
                        self.assertNotIn(marker, html)
                self.assertNotIn('Notícias internas', text)
                self.assertNotIn('Personagens aprovados', text)
                self.assert_no_horizontal_overflow(page)
                self.assert_hero_content_fits(page)
                page.screenshot(path=str(output / f'codex-guild-design-{slug}-desktop.png'),
                                full_page=True, animations='disabled')
                page.set_viewport_size({'width': 1440, 'height': 1000})
                self.assert_no_horizontal_overflow(page)
                self.assert_hero_content_fits(page)
                page.set_viewport_size({'width': 390, 'height': 844})
                self.assert_no_horizontal_overflow(page)
                self.assert_hero_content_fits(page)
                expect(crest).to_be_visible()
                page.screenshot(path=str(output / f'codex-guild-design-{slug}-mobile.png'),
                                full_page=True, animations='disabled')

            for user in (outsider, member, admin):
                private_context = self.authenticated_context(browser, user)
                private_page = private_context.new_page()
                private_page.on('pageerror', lambda error: errors.append(str(error)))
                for guild_id in (1, 2, 7):
                    slug = GUILDA_SLUG_BY_ID[guild_id]
                    response = private_page.goto(self.live_server_url + f'/guildas/{slug}/',
                                                 wait_until='networkidle')
                    self.assertEqual(response.status, 200)
                    html = private_page.content()
                    allowed = guild_id != 7 and (user == admin or (user == member and guild_id == 1))
                    for marker in markers[guild_id]:
                        if allowed:
                            self.assertIn(marker, html)
                        else:
                            self.assertNotIn(marker, html)
                    self.assert_no_horizontal_overflow(private_page)
                private_context.close()
            self.assertFalse(errors, errors)
            browser.close()
        print('PASS: índice e sete guildas; brasões e regras públicas; desktop 1920/1440 e celular 390 sem overflow; conteúdo interno restrito; mercenários sem área coletiva.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1, interactive=False).run_tests(['__main__.GuildDesignSmoke'])))
