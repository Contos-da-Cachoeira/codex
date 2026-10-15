"""Browser regressions for the manual audit, using an isolated in-memory database."""
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / 'codex'
sys.path.insert(0, str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
# Playwright mantém um loop interno; as consultas de asserção abaixo são
# sequenciais, no banco SQLite compartilhado e isolado do LiveServerTestCase.
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.runner import DiscoverRunner
from playwright.sync_api import sync_playwright, expect
from core.models import Profile
from personagens.models import Personagem, CompraTalento
from personagens.forms import CompraTalentoForm
from personagens.rules import approve_purchase, activate_purchases
from wiki.models import WikiEntry


class AuditSmoke(StaticLiveServerTestCase):
    def test_multiclass_gold_wiki_and_scenario(self):
        admin = User.objects.create_user('audit-browser-admin',is_staff=True)
        owner = User.objects.create_user('audit-browser-player')
        Profile.objects.create(user=owner,xp_disponivel=500)
        character = Personagem.objects.create(usuario=owner,nome='Guerreiro aprendiz',classe=6,guilda=2,
                            historia='Jornada arcana interpretada.',status_aprovacao=2,ouro=20)
        def buy(key, **kwargs):
            form = CompraTalentoForm({'talento':key,'justificativa':'Jornada de aprendizado.',**kwargs},character=character)
            self.assertTrue(form.is_valid(),form.errors)
            purchase = form.save()
            approve_purchase(purchase.pk,admin)
            return purchase
        conj = buy('CONJURAR',magia='Exorcismo',foco='Amuleto')
        activate_purchases(character.pk,[conj.pk])
        spell = buy('MAGIA_OUTRA_CLASSE',magia='Bola de Fogo')
        activate_purchases(character.pk,[conj.pk,spell.pk])
        self.client.force_login(admin)
        output = Path(os.environ['USERPROFILE'])/'Downloads'
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome',headless=True)
            context = browser.new_context(viewport={'width':1440,'height':1000})
            context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':self.client.cookies[settings.SESSION_COOKIE_NAME].value,'url':self.live_server_url}])
            page = context.new_page()
            errors, documents = [], []
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:documents.append(request.url) if request.resource_type == 'document' else None)
            talent_url = self.live_server_url+f'/personagens/{character.slug}/talentos/'
            page.goto(talent_url,wait_until='networkidle')
            request = page.locator('#talent-request')
            request.locator('[name=talento]').select_option('MULTICLASSE')
            request.locator('[name=segunda_classe]').select_option('8')
            expect(request.locator('[name=magia]')).to_be_visible()
            expect(request.locator('[name=divindade]')).not_to_be_visible()
            request.locator('[name=magia]').select_option('Necromancia')
            request.locator('[name=detalhes]').fill('Jornada arcana ao longo de várias sessões.')
            request.locator('[name=justificativa]').fill('O guerreiro estudou os conhecimentos de seus companheiros.')
            for purchase in (conj,spell):
                request.locator(f'[name=talentos_relacionados][value="{purchase.pk}"]').check()
            request.get_by_role('button',name='Enviar para a comissão').click()
            page.wait_for_load_state('networkidle')
            multi = CompraTalento.objects.get(personagem=character,talento='MULTICLASSE')
            approval = page.locator('article').filter(has=page.locator(f'[name=purchase][value="{multi.pk}"]'))
            approval.get_by_role('button',name='Aprovar e descontar XP').click()
            page.wait_for_load_state('networkidle')
            for purchase in (conj,spell,multi):
                page.locator(f'[name=active][value="{purchase.pk}"]').check()
            page.get_by_role('button',name='Salvar talentos ativos').click()
            page.wait_for_load_state('networkidle')
            self.assertEqual(character.compras_talentos.filter(ativo=True).count(),3)
            page.goto(self.live_server_url+f'/personagens/{character.slug}/',wait_until='networkidle')
            expect(page.get_by_text('Multiclasse: Mago',exact=True)).to_be_visible()
            page.screenshot(path=str(output/'codex-audit-multiclass.png'),full_page=True)
            page.goto(self.live_server_url+f'/area-admin/?selected_character={character.pk}#character_modal',wait_until='networkidle')
            record = page.locator(f'[data-record-id="{character.pk}"]')
            record.get_by_role('button',name='Editar personagem').click()
            record.locator(f'[name=ouro_{character.pk}]').fill('1.5')
            documents.clear()
            record.get_by_role('button',name='Salvar personagem',exact=True).click()
            expect(record.get_by_role('button',name='Editar personagem')).to_be_visible()
            character.refresh_from_db()
            self.assertEqual(character.ouro,Decimal('1.5'))
            self.assertEqual(documents,[])
            entry = WikiEntry.objects.get(category='talentos',slug='armadura-adicional')
            page.goto(self.live_server_url+f'/area-admin/?wiki_action=edit&wiki_id={entry.pk}#wiki_panel',wait_until='networkidle')
            page.locator('[name=custo_xp]').fill('35')
            page.get_by_role('button',name='Salvar conteúdo',exact=True).click()
            expect(page.locator('[data-wiki-item] h3').filter(has_text='Armadura adicional')).to_be_visible()
            page.goto(talent_url,wait_until='networkidle')
            expect(page.locator('#talent-request [name=talento]')).to_contain_text('Armadura adicional — 35 XP')
            page.goto(self.live_server_url+'/wiki/',wait_until='networkidle')
            expect(page.locator('.wh-section').filter(has_text='Cenário')).to_be_visible()
            page.screenshot(path=str(output/'codex-audit-wiki-desktop.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_function("document.querySelector('[data-sidebar]').getBoundingClientRect().right <= 1")
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(output/'codex-audit-wiki-mobile.png'),full_page=True,animations='disabled')
            page.goto(self.live_server_url+'/wiki/cenario/',wait_until='networkidle')
            page.get_by_role('link',name='Consultar').first.click()
            expect(page.locator('article h1')).to_be_visible()
            self.assertFalse(errors,errors)
            browser.close()
        print('PASS: Multiclasse solicitada/aprovada/ativa; ficha consolidada; 1,5 DO salvo sem recarga; preço da wiki integrado; cenário e celular.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1,interactive=False).run_tests(['__main__.AuditSmoke'])))
