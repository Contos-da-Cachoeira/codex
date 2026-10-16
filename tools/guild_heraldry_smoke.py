"""Home e seleção dos sete brasões no navegador, com SQLite isolado.

Execute da raiz: codex/.venv/Scripts/python.exe tools/guild_heraldry_smoke.py
"""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'codex'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
os.environ['AUTO_SSH_DB_TUNNEL'] = '0'

import django
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from playwright.sync_api import expect, sync_playwright

from core.constants.guildas import GUILDAS
from core.models import Profile
from guildas.views import GUILDA_PUBLIC_KEY_BY_ID, GUILDA_SLUG_BY_ID


class GuildHeraldrySmoke(StaticLiveServerTestCase):
    def assert_page_fits(self, page):
        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),
                             page.evaluate('document.documentElement.clientWidth') + 1,
                             f'Overflow em {page.url}')

    def assert_all_seals_fit(self, component):
        seals = component.locator('.guild-heraldry-seal')
        expect(seals).to_have_count(7)
        bounds = component.bounding_box()
        for seal in seals.all():
            expect(seal).to_be_visible()
            box = seal.bounding_box()
            self.assertGreaterEqual(box['x'], bounds['x'] - 2)
            self.assertGreaterEqual(box['y'], bounds['y'] - 2)
            self.assertLessEqual(box['x'] + box['width'], bounds['x'] + bounds['width'] + 2)
            self.assertLessEqual(box['y'] + box['height'], bounds['y'] + bounds['height'] + 2)
            image = seal.locator('img')
            image.scroll_into_view_if_needed()
            expect(image).to_be_visible()
            image.page.wait_for_function(
                '(image) => image.complete && image.naturalWidth > 0', arg=image.element_handle())
        expect(component.locator('.guild-heraldry-orbit:not(.guild-heraldry-orbit-cross)')).to_be_visible()
        expect(component.locator('.guild-heraldry-orbit-cross')).to_be_visible()

    def test_home_links_and_guild_selection(self):
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')
        owner = User.objects.create_user('heraldry-browser-owner')
        Profile.objects.create(user=owner, xp_disponivel=100)
        self.client.force_login(owner)
        output = Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Downloads'
        errors = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            anonymous = browser.new_context(viewport={'width': 1920, 'height': 1100})
            home = anonymous.new_page()
            home.on('pageerror', lambda error: errors.append(str(error)))
            response = home.goto(self.live_server_url + '/', wait_until='networkidle')
            self.assertEqual(response.status, 200)
            home_heraldry = home.locator('.guild-heraldry')
            expect(home_heraldry).to_have_count(1)
            for width, height, suffix in ((1920, 1100, 'desktop'), (390, 844, 'mobile'), (320, 768, 'mobile-320')):
                home.set_viewport_size({'width': width, 'height': height})
                self.assert_page_fits(home)
                self.assert_all_seals_fit(home_heraldry)
                for guild_id, slug in GUILDA_SLUG_BY_ID.items():
                    info = GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guild_id]]
                    link = home_heraldry.locator(f'a[href="/guildas/{slug}/"]')
                    expect(link).to_have_count(1)
                    expect(link.locator('img')).to_have_attribute('src', '/static/' + info['imagem'])
                    expect(link).to_have_attribute('aria-label', info['nome'])
                home.screenshot(path=str(output / f'codex-home-heraldry-{suffix}.png'),
                                full_page=True, animations='disabled')
            home_heraldry.locator('a[href="/guildas/mercenarios-independentes/"]').click()
            home.wait_for_url(self.live_server_url + '/guildas/mercenarios-independentes/')
            expect(home.get_by_role('heading', level=1)).to_have_text('Mercenários Independentes')
            anonymous.close()

            context = browser.new_context(viewport={'width': 1920, 'height': 1100})
            context.add_cookies([{
                'name': settings.SESSION_COOKIE_NAME,
                'value': self.client.cookies[settings.SESSION_COOKIE_NAME].value,
                'url': self.live_server_url,
            }])
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            requests = []
            page.on('request', lambda request: requests.append(request.url))
            response = page.goto(self.live_server_url + '/personagens/novo/', wait_until='networkidle')
            self.assertEqual(response.status, 200)
            page.locator('[name=nome]').fill('Ayla dos Sete Caminhos')
            page.locator('[name=descricao_personagem]').fill('Uma viajante que conhece as histórias da Cachoeira.')
            page.locator('[data-character-next=class]').click()
            page.locator('.character-class-card').filter(has=page.locator('input[value="6"]')).click()
            page.locator('[data-character-next=guild]').click()
            component = page.locator('.guild-heraldry--select')
            track = component.locator('[data-character-guild-track]')
            detail = page.locator('[data-character-guild-details]')
            expect(component).to_be_visible()
            expect(page.locator('[data-character-guild-prev], [data-character-guild-next]')).to_have_count(0)
            expect(track.locator('input[name=guilda]')).to_have_count(7)
            self.assert_all_seals_fit(component)
            page.wait_for_load_state('networkidle')
            requests.clear()

            def choose(value):
                card = component.locator('.character-guild-card').filter(
                    has=page.locator(f'input[name=guilda][value="{value}"]'))
                card.click()
                expect(card.locator('input')).to_be_checked()
                expect(track.locator('input[name=guilda]:checked')).to_have_count(1)
                info = GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[value]]
                expect(detail.locator('h3')).to_have_text(info['nome'])
                expect(detail.get_by_text(info['vantagem'], exact=True)).to_be_visible()
                expect(detail.get_by_text(info.get('marca_efeito') or info['desvantagem'], exact=True)).to_be_visible()
                if info.get('saida'):
                    expect(detail).to_contain_text(info['saida'])

            for width, height, suffix in ((1920, 1100, 'desktop'), (390, 844, 'mobile'), (320, 768, 'mobile-320')):
                page.set_viewport_size({'width': width, 'height': height})
                self.assert_page_fits(page)
                self.assert_all_seals_fit(component)
                self.assertTrue(track.evaluate(
                    'track => track.scrollWidth <= track.clientWidth + 1 && track.scrollLeft === 0'))
                for value in GUILDA_PUBLIC_KEY_BY_ID:
                    choose(value)
                    self.assert_page_fits(page)
                # Native radio keyboard navigation must update the selection
                # and its public information without loading a new page.
                choose(1)
                first = track.locator('input[name=guilda][value="1"]')
                first.focus()
                expect(first).to_be_focused()
                first.press('ArrowRight')
                second = track.locator('input[name=guilda][value="2"]')
                expect(second).to_be_checked()
                expect(detail.locator('h3')).to_have_text(GUILDAS['CIRCULO_DO_FOGO']['nome'])
                second.press('ArrowLeft')
                expect(first).to_be_checked()
                expect(detail.locator('h3')).to_have_text(GUILDAS['ARTISTAS_DA_REVOLUCAO']['nome'])
                choose(7 if width == 320 else 3)
                page.screenshot(path=str(output / f'codex-creation-heraldry-{suffix}.png'),
                                full_page=True, animations='disabled')
            self.assertEqual(requests, [], 'Selecionar guildas realizou pedidos de rede.')
            self.assertFalse(errors, errors)
            browser.close()
        print('PASS: Home com sete links e ovais; criação com sete opções e benefícios locais; teclado dos radios; desktop1920/celular390/320 sem rolagem horizontal ou recarga.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1, interactive=False).run_tests(['__main__.GuildHeraldrySmoke'])))
