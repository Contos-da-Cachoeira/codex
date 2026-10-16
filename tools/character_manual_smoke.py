"""Creation, exact spell choices and portrait previews in an isolated browser/DB."""
import os
import sys
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent / 'codex'
sys.path.insert(0, str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.test.runner import DiscoverRunner
from PIL import Image
from playwright.sync_api import sync_playwright, expect
from core.models import Profile
from core.constants.guildas import GUILDAS
from personagens.models import Personagem
from personagens.views import GUILDA_PUBLIC_KEY_BY_ID


class CreationSmoke(StaticLiveServerTestCase):
    serialized_rollback = True  # Preserve the published wiki catalog between browser cases.
    def test_guild_and_special_class_choices(self):
        owner = User.objects.create_user('creation-options-browser')
        Profile.objects.create(user=owner,xp_disponivel=300)
        self.client.force_login(owner)
        output = Path(os.environ['USERPROFILE'])/'Downloads'
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome',headless=True)
            context = browser.new_context(viewport={'width':1500,'height':1100})
            context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':self.client.cookies[settings.SESSION_COOKIE_NAME].value,'url':self.live_server_url}])
            page = context.new_page()
            errors, documents = [], []
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:documents.append(request.url) if request.resource_type=='document' else None)
            page.goto(self.live_server_url+'/personagens/novo/',wait_until='networkidle')
            page.locator('[name=nome]').fill('Elara')
            page.locator('[name=descricao_personagem]').fill('Uma estudiosa que busca os segredos da Cachoeira.')
            page.locator('[data-character-next=class]').click()

            def choose_class(value):
                page.locator('.character-class-card').filter(has=page.locator(f'input[value="{value}"]')).click()

            def choose_spells(count):
                for index in range(count): page.locator('.magia-checkbox').nth(index).check()

            choose_class(4)
            divinity = page.get_by_label('Divindade do cenário',exact=True)
            divinity.fill('Solaris')
            self.assertGreaterEqual(divinity.evaluate("input=>parseFloat(getComputedStyle(input).borderTopLeftRadius)"),8)
            choose_spells(3)
            page.screenshot(path=str(output/'codex-creation-cleric-desktop.png'),full_page=True,animations='disabled')
            page.locator('[data-character-next=guild]').click()
            detail = page.locator('[data-character-guild-details]')
            def choose_guild(value):
                page.locator('.character-guild-card').filter(has=page.locator(f'input[value="{value}"]')).click()
            for value,key in GUILDA_PUBLIC_KEY_BY_ID.items():
                choose_guild(value)
                info = GUILDAS[key]
                expect(detail.locator('h3')).to_have_text(info['nome'])
                expect(detail.get_by_text(info['vantagem'],exact=True)).to_be_visible()
                expect(detail.get_by_text(info.get('marca_efeito') or info['desvantagem'],exact=True)).to_be_visible()
            choose_guild(3)
            page.screenshot(path=str(output/'codex-creation-guild-desktop.png'),full_page=True,animations='disabled')
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_function("() => { const track = document.querySelector('[data-character-guild-track]').getBoundingClientRect(); const card = document.querySelector('.character-guild-card.is-selected').getBoundingClientRect(); return card.left >= track.left - 1 && card.right <= track.right + 1; }")
            choose_guild(2)
            expect(detail.locator('h3')).to_have_text(GUILDAS['CIRCULO_DO_FOGO']['nome'])
            choose_guild(3)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(output/'codex-creation-guild-mobile.png'),full_page=True,animations='disabled')

            page.locator('[data-character-tab=class]').click()
            choose_class(9)
            expect(divinity).to_be_visible()
            self.assertEqual(divinity.input_value(),'Solaris')
            choose_class(5)
            expect(divinity).to_be_disabled()
            affinity = page.get_by_label('Afinidade com a natureza',exact=True)
            affinity.fill('Lobo')
            self.assertGreaterEqual(affinity.evaluate("input=>parseFloat(getComputedStyle(input).borderTopLeftRadius)"),8)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(output/'codex-creation-druid-mobile.png'),full_page=True,animations='disabled')
            choose_class(8)
            choose_spells(4)
            page.locator('[data-character-next=guild]').click()
            expect(page.locator('[data-character-panel=class]')).to_be_visible()
            ancient = page.locator('[name=feitico_antigo]')
            chosen = ancient.nth(1).input_value()
            ancient.nth(1).check()
            expect(page.locator('[name=feitico_antigo]:checked')).to_have_count(1)
            self.assertLessEqual(ancient.nth(1).evaluate('input=>input.getBoundingClientRect().width'),24)
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(output/'codex-creation-mage-mobile.png'),full_page=True,animations='disabled')
            page.set_viewport_size({'width':1500,'height':1100})
            page.wait_for_function("() => { const track = document.querySelector('[data-character-class-track]').getBoundingClientRect(); const card = document.querySelector('.character-class-card.is-selected').getBoundingClientRect(); return card.left >= track.left - 1 && card.right <= track.right + 1; }")
            page.screenshot(path=str(output/'codex-creation-mage-desktop.png'),full_page=True,animations='disabled')
            choose_class(6)
            expect(ancient.nth(1)).to_be_disabled()
            choose_class(8)
            choose_spells(4)
            expect(ancient.nth(1)).to_be_checked()
            page.locator('[data-character-next=guild]').click()
            page.locator('[data-character-next=talent]').click()
            page.locator('[data-talent-choice]').select_option('FEITICO_ANTIGO')
            available = page.locator('[data-talent-value=magia] option').evaluate_all('(options)=>options.map(option=>option.value)')
            self.assertNotIn(chosen,available)
            self.assertIn(ancient.first.input_value(),available)
            extra = next(value for value in available if value)
            page.locator('[data-talent-value=magia]').select_option(extra)
            page.locator('[data-talent-value=justificativa]').fill('Estudou um grimório durante uma longa viagem.')
            page.locator('[data-add-creation-talent]').click()
            self.assertEqual(len(documents),1)

            # Force a server validation error: bound guild, spells and radio choice must survive.
            with page.expect_navigation(wait_until='networkidle'):
                page.locator('#personagem-form').evaluate('(form)=>HTMLFormElement.prototype.submit.call(form)')
            page.locator('[data-character-tab=guild]').click()
            expect(detail.locator('h3')).to_have_text(GUILDAS['FLORESTA_DO_SOL']['nome'])
            page.locator('[data-character-tab=class]').click()
            expect(page.locator('[name=feitico_antigo]:checked')).to_have_value(chosen)
            expect(page.locator('.magia-checkbox:checked')).to_have_count(4)
            page.locator('[data-character-tab=portrait]').click()
            page.locator('[name=ciencia_concordancia]').check()
            page.get_by_role('button',name='Salvar personagem',exact=True).click()
            page.wait_for_url('**/personagens/')
            self.assertFalse(errors,errors)
            browser.close()
        character = Personagem.objects.get(usuario=owner)
        self.assertEqual(character.classe,8)
        self.assertEqual(character.guilda,3)
        self.assertEqual(character.feitico_antigo,chosen)
        self.assertEqual(len(character.magias_pretendidas),4)
        self.assertEqual(character.compras_talentos.get().magia,extra)
        print('PASS: seven guild benefits; styled Cleric/Paladin/Druid fields; single ancient choice and talent exclusion; retained server validation; mobile; saved Mage.')

    def test_creation_and_portrait(self):
        owner = User.objects.create_user('manual-browser')
        Profile.objects.create(user=owner, xp_disponivel=100)
        self.client.force_login(owner)
        buffer = BytesIO()
        Image.new('RGB', (200, 200), 'royalblue').save(buffer, format='PNG')
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media), sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width':1400, 'height':1050})
            context.add_cookies([{'name':settings.SESSION_COOKIE_NAME, 'value':self.client.cookies[settings.SESSION_COOKIE_NAME].value, 'url':self.live_server_url}])
            page = context.new_page()
            errors, documents = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda r: documents.append(r.url) if r.resource_type == 'document' else None)
            page.goto(self.live_server_url + '/personagens/novo/', wait_until='networkidle')
            page.locator('[name=nome]').fill('Aria')
            page.locator('[name=descricao_personagem]').fill('Uma artista que percorre as guildas.')
            page.locator('[data-character-next=class]').click()
            page.locator('.character-class-card').filter(has=page.locator('input[value="2"]')).click()
            choices = page.locator('.magia-checkbox')
            for i in range(3): choices.nth(i).check()
            self.assertEqual(page.locator('#spell-count').inner_text(), '3 de 3 magias escolhidas')
            page.locator('[data-character-next=guild]').click()
            self.assertTrue(page.locator('[data-character-panel=guild]').is_visible())
            page.locator('[data-character-tab=class]').click()
            choices.nth(3).check()
            page.locator('[data-character-next=guild]').click()
            self.assertTrue(page.locator('[data-character-panel=class]').is_visible())
            choices.nth(3).uncheck()
            page.locator('[data-character-next=guild]').click()
            page.locator('.character-guild-card').filter(has=page.locator('input[value="1"]')).click()
            page.locator('[data-character-next=talent]').click()
            self.assertTrue(page.locator('[data-character-panel=talent]').is_visible())
            self.assertFalse(page.locator('[data-portrait-options]').is_visible())
            page.locator('[data-talent-choice]').select_option('ARMADURA_ADICIONAL')
            page.locator('[data-talent-value=justificativa]').fill('Treinou o uso de armadura durante suas viagens.')
            page.locator('[data-add-creation-talent]').click()
            page.locator('[data-add-creation-talent]').click()
            self.assertIn('2 de 5 compras · 50 XP', page.locator('[data-talent-summary]').inner_text())
            page.get_by_role('button', name='Remover Armadura adicional 2', exact=True).click()
            self.assertIn('1 de 5 compras · 25 XP', page.locator('[data-talent-summary]').inner_text())
            self.assertEqual(len(documents), 1)
            page.screenshot(path=str(Path(os.environ['USERPROFILE']) / 'Downloads/codex-creation-talents-desktop.png'), full_page=True, animations='disabled')
            page.set_viewport_size({'width':390,'height':844})
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
            page.screenshot(path=str(Path(os.environ['USERPROFILE']) / 'Downloads/codex-creation-talents-mobile.png'), full_page=True, animations='disabled')
            page.set_viewport_size({'width':1400,'height':1050})
            page.locator('[data-character-next=portrait]').click()
            self.assertTrue(page.locator('[data-portrait-options]').is_visible())
            page.locator('[data-character-panel=portrait] [data-character-prev=talent]').click()
            self.assertIn('1 de 5 compras · 25 XP', page.locator('[data-talent-summary]').inner_text())
            page.locator('[data-character-next=portrait]').click()
            self.assertEqual(page.locator('[data-name-preview]').inner_text(), 'A')
            self.assertIn('Bardo-ink.png', page.locator('[data-class-preview]').get_attribute('src'))
            page.locator('[name=portrait_mode][value=name]').check()
            page.locator('[name=portrait_mode][value=photo]').check()
            page.locator('[name=ciencia_concordancia]').check()
            page.get_by_role('button', name='Salvar personagem', exact=True).click()
            self.assertEqual(len(documents), 1)  # Foto vazia não envia o formulário.
            page.locator('[data-profile-image-picker]').click()
            page.locator('dialog [data-file]').set_input_files({'name':'portrait.png', 'mimeType':'image/png', 'buffer':buffer.getvalue()})
            page.locator('dialog [data-apply]').click()
            page.locator('dialog').wait_for(state='detached')
            self.assertTrue(page.locator('[name=portrait_mode][value=photo]').is_checked())
            self.assertTrue(page.locator('[name=image_asset]').input_value())
            page.locator('[data-remove-character-image]').click()
            self.assertTrue(page.locator('[name=portrait_mode][value=name]').is_checked())
            page.locator('[name=portrait_mode][value=class]').check()
            page.screenshot(path=str(Path(os.environ['USERPROFILE']) / 'Downloads/codex-character-preview-desktop.png'), full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), 390)
            page.screenshot(path=str(Path(os.environ['USERPROFILE']) / 'Downloads/codex-character-preview-mobile.png'), full_page=True, animations='disabled')
            page.get_by_role('button', name='Salvar personagem', exact=True).click()
            page.wait_for_url('**/personagens/')
            self.assertFalse(errors, errors)
            browser.close()
        character = Personagem.objects.get(usuario=owner)
        self.assertEqual(len(character.magias_pretendidas), 3)
        self.assertEqual(character.portrait_mode, 'class')
        self.assertEqual(character.talentos_iniciais, [])
        self.assertEqual(character.compras_talentos.get().status, 'pending')
        owner.refresh_from_db()
        self.assertEqual(owner.profile.xp_disponivel, 100)
        print('PASS: Bardo 3/3; 4 choices blocked; last-step previews; upload/removal; mobile; saved class portrait.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1, interactive=False).run_tests(['__main__.CreationSmoke'])))
