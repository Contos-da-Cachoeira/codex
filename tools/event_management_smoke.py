"""Gestão de eventos no navegador, usando apenas contas fictícias e SQLite em memória."""
import os
import sys
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent.parent / 'codex'
sys.path.insert(0, str(ROOT))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wiki.test_settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'  # Asserções sequenciais no banco isolado do LiveServer.
import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.test.runner import DiscoverRunner
from django.utils import timezone
from PIL import Image
from playwright.sync_api import sync_playwright, expect
from core.models import Profile, LarpEvento, LarpInscricao
from personagens.models import Personagem
from personagens.rules import set_player_xp


class EventManagementSmoke(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        media = TemporaryDirectory()
        cls.addClassCleanup(media.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media.name, MEDIA_URL='/media/')
        media_settings.enable()
        cls.addClassCleanup(media_settings.disable)
        super().setUpClass()

    def test_overview_participants_conflicts_and_mobile(self):
        admin = User.objects.create_user('event-browser-admin',is_staff=True)
        event = LarpEvento.objects.create(titulo='O despertar da Cachoeira',local='Parque das Águas',
            historia='As guildas se reúnem para investigar uma antiga fonte de magia. Uma nova jornada começa ao cair da tarde.',
            data_evento=timezone.now()+timedelta(days=10),data_limite_inscricao=timezone.now()+timedelta(days=9),visivel_publicamente=True)
        names = ['Ana de Oliveira','Lúcia Martins','Bruno Almeida','Carlos Silva','Daniela Reis','Eduardo Santos']
        chars = ['Ayla','Selene','Thorin','Kael','Liora','Dorian']
        registrations = []
        for index,(name,char) in enumerate(zip(names,chars)):
            player = User.objects.create_user(f'player-{index}')
            Profile.objects.create(user=player)
            set_player_xp(player,300,admin,'Saldo fictício do teste')
            character = Personagem.objects.create(usuario=player,nome=char,classe=index+1,guilda=index+1 if index < 5 else 7,
                status_aprovacao=2,portrait_mode='class',ouro=5)
            registrations.append(LarpInscricao.objects.create(evento=event,usuario=player,personagem=character,
                nome_completo_jogador=name,telefone='(11) 99999-0000',cpf='000',taxa_paga=index%2==0,
                presenca_confirmada=index==0,fobia_gatilho='Cuidado fictício: evitar locais altos.' if index==0 else ''))
        first, second = registrations[:2]
        other = Personagem.objects.create(usuario=second.usuario,nome='Outro personagem',classe=6,guilda=2,ouro=7)
        self.client.force_login(admin)
        output = Path(os.environ['USERPROFILE'])/'Downloads'
        cover = BytesIO(); Image.new('RGB',(900,340),'#193558').save(cover,format='PNG')
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome',headless=True)
            context = browser.new_context(viewport={'width':1600,'height':1100})
            context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':self.client.cookies[settings.SESSION_COOKIE_NAME].value,'url':self.live_server_url}])
            page = context.new_page()
            errors, documents = [], []
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:documents.append(request.url) if request.resource_type=='document' else None)
            base = self.live_server_url+f'/larps/{event.slug}/'
            page.goto(base,wait_until='networkidle')
            page.screenshot(path=str(output/'codex-events-overview-desktop.png'),full_page=True,animations='disabled')
            page.locator('[data-open-event-edit]').click()
            editor = page.locator('[data-event-editor]')
            editor.locator('[name=titulo]').fill('A jornada das guildas')
            editor.locator('[name=capa]').set_input_files({'name':'cover.png','mimeType':'image/png','buffer':cover.getvalue()})
            expect(editor.locator('[data-event-cover-preview]')).to_be_visible()
            editor.locator('[name=data_limite_inscricao]').fill((timezone.localtime()+timedelta(days=12)).strftime('%Y-%m-%dT%H:%M'))
            with page.expect_response(lambda response:response.request.method=='POST' and response.url==base):
                editor.get_by_role('button',name='Salvar evento',exact=True).click()
            expect(editor.locator('[name=data_limite_inscricao]')).to_have_attribute('aria-invalid','true')
            self.assertEqual(editor.locator('[name=capa]').evaluate('(input)=>input.files.length'),1)
            self.assertEqual(editor.locator('[name=titulo]').input_value(),'A jornada das guildas')
            deadline = (timezone.localtime()+timedelta(days=9)).replace(second=0,microsecond=0)
            editor.locator('[name=data_limite_inscricao]').fill(deadline.strftime('%Y-%m-%dT%H:%M'))
            with page.expect_response(lambda response:response.request.method=='POST' and response.url==base):
                editor.get_by_role('button',name='Salvar evento',exact=True).click()
            expect(page.locator('h1')).to_have_text('A jornada das guildas')
            event.refresh_from_db()
            try:
                page.wait_for_function("document.querySelector('[data-event-summary] img.em-cover')?.naturalWidth === 900",timeout=5000)
            except Exception:
                print('Cover diagnostic:',event.capa.url,Path(event.capa.path).exists(),
                    page.locator('[data-event-summary] img.em-cover').evaluate('(image)=>({src:image.src,width:image.naturalWidth})'))
                raise
            self.assertEqual(event.data_limite_inscricao,deadline)
            self.assertEqual(len(documents),1)
            page.get_by_role('link',name='Gerenciar participantes',exact=True).click()
            page.wait_for_url(base+'planilha/')
            page.wait_for_load_state('networkidle')
            documents.clear()
            guild_symbols = page.locator('[data-participant-row] > td:first-child img.em-guild-symbol')
            expect(guild_symbols).to_have_count(len(registrations))
            for symbol in guild_symbols.all():
                expect(symbol).to_be_visible()
                self.assertTrue(symbol.evaluate('(image) => image.complete && image.naturalWidth > 0'))
            mercenary_symbol = page.locator(f'[data-participant-row="{registrations[-1].pk}"] .em-guild-symbol')
            expect(mercenary_symbol).to_have_attribute('alt', 'Mercenários Independentes')
            expect(mercenary_symbol).to_have_attribute('src', '/static/core/img/guildas/mercenarios-independentes.png')
            second_row = page.locator(f'[data-participant-row="{second.pk}"]')
            second_row.locator('[data-open-participant]').click()
            expect(page.locator('[data-participant-detail] h3')).to_have_text('Selene')
            page.screenshot(path=str(output/'codex-events-participants-desktop.png'),full_page=True,animations='disabled')
            page.locator('[data-participant-search]').fill('lucia')
            expect(page.locator('[data-participant-row]:visible')).to_have_count(1)
            second_row.locator('[data-event-field=xp]').fill('310')
            second_row.locator('[data-event-field=ouro]').fill('1.5')
            second_row.locator('[data-event-field=taxa_paga]').check()
            second_row.locator('[data-event-field=presenca]').check()
            page.locator('[data-participant-save]').click()
            expect(page.locator('[data-participant-save]')).to_be_disabled()
            expect(page.locator('[data-event-feedback]')).to_have_text('Alterações salvas.')
            second.refresh_from_db()
            self.assertTrue(second.taxa_paga and second.presenca_confirmada)
            self.assertEqual(Profile.objects.get(user=second.usuario).xp_disponivel,310)
            self.assertEqual(Personagem.objects.get(pk=second.personagem_id).ouro,Decimal('1.5'))
            self.assertEqual(Personagem.objects.get(pk=other.pk).ouro,Decimal('7'))
            page.locator('[data-participant-filter=payment]').select_option('pending')
            expect(page.locator('[data-participant-no-results]')).to_be_visible()
            page.locator('[data-clear-participant-filters]').click()
            first_row = page.locator(f'[data-participant-row="{first.pk}"]')
            first_row.locator('[data-event-field=xp]').fill('500')
            first_row.locator('[data-event-field=ouro]').fill('10.5')
            page.locator('[data-participant-search]').fill('lucia')
            second_row.locator('[data-event-field=ouro]').fill('2.5')
            expect(page.locator('[data-participant-dirty]')).to_contain_text('1 fora do filtro')
            page.route('**/planilha/',lambda route:route.abort() if route.request.method=='POST' else route.continue_())
            page.locator('[data-participant-save]').click()
            expect(page.locator('[data-event-feedback]')).to_contain_text('Não foi possível comunicar')
            self.assertEqual(second_row.locator('[data-event-field=ouro]').input_value(),'2.5')
            self.assertEqual(first_row.locator('[data-event-field=xp]').input_value(),'500')
            page.unroute('**/planilha/')
            set_player_xp(first.usuario,275,admin,'Alteração concorrente fictícia')
            set_player_xp(second.usuario,285,admin,'Alteração concorrente fictícia')
            page.locator('[data-participant-save]').click()
            expect(page.locator('[data-refresh-participant-conflicts]')).to_be_visible()
            self.assertEqual(second_row.locator('[data-event-field=ouro]').input_value(),'2.5')
            page.locator('[data-refresh-participant-conflicts]').click()
            self.assertEqual(first_row.locator('[data-event-field=xp]').input_value(),'275')
            self.assertEqual(second_row.locator('[data-event-field=ouro]').input_value(),'2.5')
            page.locator('[data-participant-save]').click()
            expect(page.locator('[data-event-feedback]')).to_have_text('Alterações salvas.')
            expect(page.locator('[data-participant-save]')).to_be_disabled()
            self.assertEqual(Profile.objects.get(user=first.usuario).xp_disponivel,275)
            self.assertEqual(Profile.objects.get(user=second.usuario).xp_disponivel,285)
            self.assertEqual(Personagem.objects.get(pk=second.personagem_id).ouro,Decimal('2.5'))
            self.assertEqual(documents,[])
            page.locator('[data-clear-participant-filters]').click()
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_function("document.querySelector('[data-sidebar]').getBoundingClientRect().right <= 1")
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            symbol_bounds = first_row.locator('.em-guild-symbol').bounding_box()
            player_bounds = first_row.locator('.em-player-cell .em-person').bounding_box()
            self.assertLessEqual(symbol_bounds['x'] + symbol_bounds['width'], player_bounds['x'])
            page.screenshot(path=str(output/'codex-events-participants-mobile.png'),full_page=True,animations='disabled')
            first_row.locator('[data-open-participant]').click()
            dialog = page.locator('[data-participant-dialog]')
            expect(dialog).to_be_visible()
            expect(dialog.locator('h3')).to_have_text('Ayla')
            dialog.locator('summary').click()
            expect(dialog.get_by_text('Cuidado fictício: evitar locais altos.',exact=True)).to_be_visible()
            page.screenshot(path=str(output/'codex-events-participant-mobile-detail.png'),animations='disabled')
            dialog.get_by_role('button',name='Fechar detalhes',exact=True).click()
            page.goto(base,wait_until='networkidle')
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(output/'codex-events-overview-mobile.png'),full_page=True,animations='disabled')
            empty = LarpEvento.objects.create(titulo='Evento sem inscritos',local='Praça',historia='Em preparação.',
                data_evento=timezone.now()+timedelta(days=5),data_limite_inscricao=timezone.now()+timedelta(days=4))
            page.goto(self.live_server_url+f'/larps/{empty.slug}/planilha/',wait_until='networkidle')
            expect(page.get_by_text('Ainda não há inscrições neste LARP.',exact=True)).to_be_visible()
            self.assertFalse(errors,errors)
            browser.close()
        print('PASS: visão geral/edição/capa; filtros e seleção sem recarga; pagamentos/presença/XP/ouro; rede/conflito sem perda de outras edições; celular e estado vazio.')


if __name__ == '__main__':
    raise SystemExit(bool(DiscoverRunner(verbosity=1,interactive=False).run_tests(['__main__.EventManagementSmoke'])))
