from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from personagens.models import Personagem, MovimentoXP
from personagens.rules import set_player_xp
from .models import Profile, LarpEvento, LarpInscricao


class EventManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('event-admin', is_staff=True)
        cls.event = LarpEvento.objects.create(titulo='Encontro de guildas', local='Parque', historia='Uma aventura.',
            visivel_publicamente=True, data_evento=timezone.now()+timedelta(days=10),
            data_limite_inscricao=timezone.now()+timedelta(days=9))
        cls.players, cls.registrations = [], []
        for number in range(3):
            player = User.objects.create_user(f'event-player-{number}')
            Profile.objects.create(user=player)
            set_player_xp(player, 250, cls.admin, 'Saldo fictício inicial')
            character = Personagem.objects.create(usuario=player, nome=f'Personagem {number}',classe=6,guilda=1,ouro=Decimal('2.5'))
            registration = LarpInscricao.objects.create(evento=cls.event, usuario=player, personagem=character,
                nome_completo_jogador=f'Jogador {number}',telefone='123',cpf='123',fobia_gatilho='Cuidado fictício.' if number == 0 else '')
            cls.players.append(player)
            cls.registrations.append(registration)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse('planilha_larp', args=[self.event.slug])

    def row_payload(self, registration, fields=('xp','ouro','taxa_paga','presenca'), **values):
        prefix = f'character-{registration.personagem_id}-'
        current = {'xp':'250','ouro':'2.5','xp_anterior':'250','ouro_anterior':'2.5','taxa_anterior':'0','presenca_anterior':'0'}
        return {'action':'update_balances','include_payments':'1','registration_ids':[registration.pk],
                f'changed_fields_{registration.pk}':list(fields), **{prefix+name:value for name,value in (current|values).items()}}

    def save(self, data):
        return self.client.post(self.url, data, HTTP_X_EVENT_MANAGEMENT='1')

    def test_management_pages_and_metrics(self):
        overview = self.client.get(reverse('detalhe_larp',args=[self.event.slug]))
        self.assertTemplateUsed(overview,'core/gerenciar_larp.html')
        self.assertContains(overview,'Gerenciar participantes')
        response = self.client.get(self.url)
        self.assertEqual(response.context['metrics'],{'total':3,'paid':0,'pending':3,'present':0,'alerts':1,'paid_percent':0,'present_percent':0})
        self.assertContains(response,'data-participant-template')
        self.assertContains(response,'XP é do jogador')
        self.assertContains(response,'class="em-guild-symbol"',count=3)
        self.assertContains(response,'core/img/guildas/artistas-da-revolucao.png',count=3)
        character = self.registrations[0].personagem
        character.guilda = None
        character.save(update_fields=['guilda'])
        response = self.client.get(self.url)
        self.assertContains(response,'class="em-guild-symbol"',count=2)
        self.assertContains(response,'aria-label="Sem símbolo de guilda"',count=1)

    def test_save_payment_presence_and_balances_for_selected_participant_only(self):
        registration = self.registrations[0]
        response = self.save(self.row_payload(registration,xp='270',ouro='3.5',taxa_paga='on',presenca='on'))
        self.assertEqual(response.status_code,200,response.content)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['metrics']['paid'],1)
        registration.refresh_from_db()
        self.assertTrue(registration.taxa_paga)
        self.assertTrue(registration.presenca_confirmada)
        self.assertEqual(Profile.objects.get(user=registration.usuario).xp_disponivel,270)
        self.assertEqual(Personagem.objects.get(pk=registration.personagem_id).ouro,Decimal('3.5'))
        other = self.registrations[1]
        self.assertEqual(Profile.objects.get(user=other.usuario).xp_disponivel,250)
        self.assertEqual(Personagem.objects.get(pk=other.personagem_id).ouro,Decimal('2.5'))

    def test_payment_only_edit_preserves_xp_spent_while_page_was_open(self):
        registration = self.registrations[0]
        set_player_xp(registration.usuario,225,self.admin,'Outra operação')
        response = self.save(self.row_payload(registration,fields=('taxa_paga',),taxa_paga='on'))
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['rows'][0]['xp'],225)
        self.assertEqual(Profile.objects.get(user=registration.usuario).xp_disponivel,225)

    def test_stale_xp_rejects_entire_batch_and_returns_current_values(self):
        first, second = self.registrations[:2]
        set_player_xp(first.usuario,225,self.admin,'Compra concorrente')
        data = self.row_payload(first,xp='300',taxa_paga='on')
        data.update(self.row_payload(second,xp='280'))
        data['registration_ids'] = [first.pk,second.pk]
        count = MovimentoXP.objects.count()
        response = self.save(data)
        self.assertEqual(response.status_code,409,response.content)
        self.assertEqual(response.json()['conflicts'][0]['xp'],225)
        self.assertEqual(MovimentoXP.objects.count(),count)
        self.assertEqual(Profile.objects.get(user=second.usuario).xp_disponivel,250)
        first.refresh_from_db()
        self.assertFalse(first.taxa_paga)

    def test_gold_conflict_does_not_overwrite_new_balance(self):
        registration = self.registrations[0]
        Personagem.objects.filter(pk=registration.personagem_id).update(ouro=Decimal('4.5'))
        response = self.save(self.row_payload(registration,fields=('ouro',),ouro='3.5'))
        self.assertEqual(response.status_code,409)
        self.assertEqual(Personagem.objects.get(pk=registration.personagem_id).ouro,Decimal('4.5'))

    def test_retry_after_lost_response_is_idempotent(self):
        registration = self.registrations[0]
        data = self.row_payload(registration,xp='270',ouro='3.5',taxa_paga='on')
        self.assertEqual(self.save(data).status_code,200)
        movements = MovimentoXP.objects.count()
        self.assertEqual(self.save(data).status_code,200)
        self.assertEqual(MovimentoXP.objects.count(),movements)

    def test_validation_errors_preserve_all_other_rows(self):
        first, second = self.registrations[:2]
        data = self.row_payload(first,ouro='0.1')
        data.update(self.row_payload(second,xp='270'))
        data['registration_ids'] = [first.pk,second.pk]
        response = self.save(data)
        self.assertEqual(response.status_code,422,response.content)
        self.assertIn('ouro',response.json()['errors'][str(first.pk)])
        self.assertEqual(Profile.objects.get(user=second.usuario).xp_disponivel,250)

    def test_registration_from_other_event_is_rejected(self):
        other = LarpEvento.objects.create(titulo='Outro',local='Praça',historia='História',
            data_evento=timezone.now()+timedelta(days=5),data_limite_inscricao=timezone.now()+timedelta(days=4))
        first = self.registrations[0]
        foreign = LarpInscricao.objects.create(evento=other,usuario=first.usuario,personagem=first.personagem)
        response = self.save(self.row_payload(foreign,xp='999'))
        self.assertEqual(response.status_code,400)
        self.assertEqual(Profile.objects.get(user=first.usuario).xp_disponivel,250)

    def test_ajax_requires_original_values_for_changed_fields(self):
        registration = self.registrations[0]
        data = self.row_payload(registration,fields=('xp',),xp='270')
        del data[f'character-{registration.personagem_id}-xp_anterior']
        self.assertEqual(self.save(data).status_code,409)
        self.assertEqual(Profile.objects.get(user=registration.usuario).xp_disponivel,250)

    def test_non_admin_cannot_read_or_save_management_data(self):
        self.client.force_login(self.players[0])
        response = self.save(self.row_payload(self.registrations[0],xp='999'))
        self.assertEqual(response.status_code,403)
        self.assertNotContains(self.client.get(reverse('detalhe_larp',args=[self.event.slug])),'Cuidado fictício.')
        self.assertEqual(self.client.get(self.url).status_code,302)
        self.assertEqual(Profile.objects.get(user=self.players[0]).xp_disponivel,250)

    def test_save_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(self.url,self.row_payload(self.registrations[0],xp='999'),HTTP_X_EVENT_MANAGEMENT='1')
        self.assertEqual(response.status_code,403)

    def event_payload(self, **values):
        return {'action':'edit_event','titulo':'Evento revisado','local':'Nova praça','historia':'Nova história.',
                'data_evento':(timezone.now()+timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
                'data_limite_inscricao':(timezone.now()+timedelta(days=9)).strftime('%Y-%m-%dT%H:%M'),**values}

    def test_event_editor_returns_summary_and_validation_without_redirect(self):
        url = reverse('detalhe_larp',args=[self.event.slug])
        invalid = self.event_payload(data_limite_inscricao=(timezone.now()+timedelta(days=12)).strftime('%Y-%m-%dT%H:%M'))
        response = self.client.post(url,invalid,HTTP_X_EVENT_MANAGEMENT='1')
        self.assertEqual(response.status_code,422)
        self.assertIn('data_limite_inscricao',response.json()['errors'])
        self.event.refresh_from_db()
        self.assertEqual(self.event.titulo,'Encontro de guildas')
        response = self.client.post(url,self.event_payload(),HTTP_X_EVENT_MANAGEMENT='1')
        self.assertEqual(response.status_code,200)
        self.assertIn('Evento revisado',response.json()['title'])
        self.assertIn('Nova praça',response.json()['summary'])
        self.assertIn('data-event-editor',response.json()['editor'])
        self.event.refresh_from_db()
        self.assertEqual(self.event.local,'Nova praça')
        self.assertFalse(self.registrations[0].taxa_paga)
