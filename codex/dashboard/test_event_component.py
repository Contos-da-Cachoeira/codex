import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import HomeDynamicSection, LarpEvento, LarpInscricao
from personagens.models import Personagem
from .home_components import parse_components, serialize_components


class EventComponentTests(TestCase):
    def setUp(self):
        self.section = HomeDynamicSection.objects.create(kind='event', title='Próximo LARP', content='')
        self.now = timezone.now()

    def event(self, title, days, visible=True):
        return LarpEvento.objects.create(titulo=title, historia='Uma nova aventura.', local='Parque',
            data_evento=self.now + timedelta(days=days),
            data_limite_inscricao=self.now + timedelta(days=days-1), visivel_publicamente=visible)

    def test_nearest_public_future_event_is_selected(self):
        self.event('Passado', -1)
        self.event('Oculto', 1, visible=False)
        self.event('Mais distante', 8)
        next_event = self.event('Próximo encontro', 3)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['next_event'], next_event)
        self.assertContains(response, 'Próximo encontro')
        self.assertNotContains(response, 'Mais distante')
        self.assertNotContains(response, 'Oculto')
        self.assertContains(response, 'Entrar para se inscrever')

    def test_empty_state_and_hidden_component(self):
        self.assertContains(self.client.get(reverse('home')), 'Nenhum próximo LARP anunciado')
        self.section.is_visible = False
        self.section.save()
        self.assertNotContains(self.client.get(reverse('home')), 'Nenhum próximo LARP anunciado')

    def test_closed_registration_keeps_event_without_signup(self):
        event = self.event('Inscrições encerradas', 2)
        event.data_limite_inscricao = self.now - timedelta(hours=1)
        event.save()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['next_event'], event)
        self.assertContains(response, 'Ver detalhes')
        self.assertNotContains(response, 'Entrar para se inscrever')

    def test_registered_user_sees_confirmation(self):
        user = User.objects.create_user('player')
        character = Personagem.objects.create(usuario=user, nome='Aventureira')
        event = self.event('Encontro', 3)
        LarpInscricao.objects.create(evento=event, usuario=user, personagem=character)
        self.client.force_login(user)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Inscrição confirmada')
        self.assertContains(response, 'Aventureira')
        self.assertNotContains(response, '>Inscrever-se</a>')

    def test_editor_round_trip_and_preview(self):
        payload = json.dumps([dict(kind='event', title='Evento', content='', is_visible=True)])
        self.assertEqual(parse_components(payload)[0].kind, 'event')
        self.assertTrue(any(item['kind'] == 'event' for item in serialize_components()))
        admin = User.objects.create_user('admin', is_staff=True)
        self.client.force_login(admin)
        self.event('Encontro da prévia', 4)
        before = HomeDynamicSection.objects.count()
        response = self.client.post(reverse('home_preview'), {'components_json': payload})
        self.assertContains(response, 'Encontro da prévia')
        self.assertEqual(HomeDynamicSection.objects.count(), before)
