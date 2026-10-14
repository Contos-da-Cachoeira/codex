from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from core.models import LarpEvento, Profile
from personagens.models import Personagem


class RecordManagerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user('admin', is_staff=True)
        cls.player = User.objects.create_user('jogador', email='jogador@example.com')
        cls.other = User.objects.create_user('outro')
        cls.superuser = User.objects.create_user('super', is_staff=True, is_superuser=True)
        Profile.objects.update_or_create(user=cls.player, defaults={'nome_completo_jogador': 'Jogador de teste', 'telefone': '12345'})
        cls.character = Personagem.objects.create(usuario=cls.player, nome='Aventureiro', historia='História preservada', classe=1, guilda=1, xp_atual=10, ouro=20)
        cls.other_character = Personagem.objects.create(usuario=cls.other, nome='Outro aventureiro', xp_atual=30)
        cls.event = LarpEvento.objects.create(titulo='LARP de teste', local='Praça', historia='Uma aventura',
            data_evento=timezone.now() + timedelta(days=7), data_limite_inscricao=timezone.now() + timedelta(days=6), criado_por=cls.admin)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse('admin_dashboard')

    def test_catalogs_group_records_and_show_selected_details(self):
        response = self.client.get(self.url, {'selected_user': self.player.pk, 'selected_character': self.character.pk, 'selected_larp': self.event.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-record-manager="users"')
        self.assertContains(response, 'data-record-manager="characters"')
        self.assertContains(response, 'data-record-manager="larps"')
        self.assertEqual(response.context['users_manager']['selected']['id'], self.player.pk)
        self.assertEqual(response.context['characters_manager']['selected']['id'], self.character.pk)
        self.assertEqual(response.context['larps_manager']['selected']['id'], self.event.pk)
        self.assertContains(response, 'Jogador de teste')
        self.assertContains(response, 'História preservada')
        self.assertContains(response, 'Uma aventura')
        self.assertNotContains(response, f'name="role_{self.superuser.pk}"')

    def test_selected_user_role_update_does_not_change_other_accounts(self):
        response = self.client.post(self.url, {'action': 'bulk_update_roles', 'record_manager': 'users',
            'user_ids': self.player.pk, f'role_{self.player.pk}': 'ADMIN', 'return_q': 'jogador'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'selected_user={self.player.pk}', response.url)
        self.assertIn('q=jogador', response.url)
        self.assertTrue(response.url.endswith('#user_roles_modal'))
        self.player.refresh_from_db()
        self.other.refresh_from_db()
        self.assertTrue(self.player.is_staff)
        self.assertEqual(self.player.profile.role, 'ADMIN')
        self.assertFalse(self.other.is_staff)

    def test_superuser_role_is_protected(self):
        self.client.post(self.url, {'action': 'bulk_update_roles', 'record_manager': 'users',
            'user_ids': self.superuser.pk, f'role_{self.superuser.pk}': 'COMMON'})
        self.superuser.refresh_from_db()
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)

    def test_character_update_only_changes_selected_character(self):
        pk = self.character.pk
        response = self.client.post(self.url, {'action': 'bulk_update_personagens', 'record_manager': 'characters',
            'personagem_ids': pk, f'status_{pk}': 1, f'status_aprovacao_{pk}': 2, f'classe_{pk}': 2,
            f'guilda_{pk}': 2, f'xp_atual_{pk}': 100, f'ouro_{pk}': 50, 'return_character_q': 'Aventureiro'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'selected_character={pk}', response.url)
        self.character.refresh_from_db()
        self.other_character.refresh_from_db()
        self.assertEqual((self.character.classe, self.character.guilda, self.character.xp_atual, self.character.ouro, self.character.status_aprovacao), (2, 2, 100, 50, 2))
        self.assertEqual(self.character.historia, 'História preservada')
        self.assertEqual(self.other_character.xp_atual, 30)

    def event_payload(self, **extra):
        return {'action': 'save_admin_larp', 'titulo': 'Novo LARP', 'local': 'Floresta', 'historia': 'Nova história',
                'data_evento': (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
                'data_limite_inscricao': (timezone.now() + timedelta(days=9)).strftime('%Y-%m-%dT%H:%M'), **extra}

    def test_create_and_edit_event_with_cover_inside_admin(self):
        stream = BytesIO()
        Image.new('RGB', (8, 8), 'blue').save(stream, format='PNG')
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            response = self.client.post(self.url, self.event_payload(capa=SimpleUploadedFile('capa.png', stream.getvalue(), content_type='image/png')))
            self.assertEqual(response.status_code, 302)
            event = LarpEvento.objects.get(titulo='Novo LARP')
            self.assertEqual(event.criado_por, self.admin)
            self.assertTrue(event.capa)
            self.assertIn(f'selected_larp={event.pk}', response.url)
            response = self.client.post(self.url, self.event_payload(event_id=event.pk, titulo='LARP editado', visivel_publicamente='on'))
            self.assertEqual(response.status_code, 302)
            event.refresh_from_db()
            self.assertEqual(event.titulo, 'LARP editado')
            self.assertTrue(event.visivel_publicamente)
            self.assertEqual(event.criado_por, self.admin)
            self.assertTrue(event.capa)

    def test_invalid_event_form_stays_in_selected_panel_without_saving(self):
        response = self.client.post(self.url, self.event_payload(event_id=self.event.pk,
            data_limite_inscricao=(timezone.now() + timedelta(days=12)).strftime('%Y-%m-%dT%H:%M')))
        self.assertEqual(response.status_code, 200)
        selected = response.context['larps_manager']['selected']
        self.assertEqual(selected['id'], self.event.pk)
        self.assertTrue(selected['editing'])
        self.assertTrue(selected['edit_form'].errors)
        self.assertContains(response, 'data-admin-initial-tab="larp_modal"')
        self.event.refresh_from_db()
        self.assertEqual(self.event.titulo, 'LARP de teste')

    def test_event_visibility_and_filters(self):
        response = self.client.post(self.url, {'action': 'bulk_update_larp_visibility', 'record_manager': 'larps',
            'larp_ids': self.event.pk, f'larp_visivel_{self.event.pk}': 'on'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'selected_larp={self.event.pk}', response.url)
        self.event.refresh_from_db()
        self.assertTrue(self.event.visivel_publicamente)
        response = self.client.get(self.url, {'larp_q': 'Praça', 'larp_visibility_filter': 'public'})
        self.assertEqual(response.context['larps_manager']['count'], 1)
        response = self.client.get(self.url, {'larp_q': 'inexistente'})
        self.assertIsNone(response.context['larps_manager']['selected'])

    def test_non_admin_cannot_access_or_mutate_managers(self):
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        for action, extra in [('save_admin_larp', self.event_payload()),
                              ('bulk_update_roles', {'user_ids': self.other.pk, f'role_{self.other.pk}': 'ADMIN'}),
                              ('bulk_update_personagens', {'personagem_ids': self.character.pk, f'xp_atual_{self.character.pk}': 999})]:
            self.assertEqual(self.client.post(self.url, {**extra, 'action': action}).status_code, 302)
        self.assertFalse(LarpEvento.objects.filter(titulo='Novo LARP').exists())
        self.character.refresh_from_db()
        self.assertEqual(self.character.xp_atual, 10)

    def test_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url, self.event_payload()).status_code, 403)

    def test_fragment_only_returns_requested_panel_and_requires_admin(self):
        response = self.client.get(self.url, {'selected_character': self.character.pk}, headers={'X-Admin-Panel': 'character_modal'})
        payload = response.json()
        self.assertEqual(payload['panel'], 'character_modal')
        self.assertEqual(payload['state']['selected'], str(self.character.pk))
        self.assertIn('data-record-manager="characters"', payload['html'])
        self.assertNotIn('data-record-manager="users"', payload['html'])
        self.assertNotIn('<!DOCTYPE', payload['html'])
        self.assertIn('no-store', response['Cache-Control'])
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(self.url, headers={'X-Admin-Panel': 'character_modal'}).status_code, 403)

    def test_background_save_returns_updated_character_panel(self):
        pk = self.character.pk
        response = self.client.post(self.url, {'action': 'bulk_update_personagens', 'record_manager': 'characters',
            'personagem_ids': pk, f'status_{pk}': 1, f'status_aprovacao_{pk}': 2, f'classe_{pk}': 1,
            f'guilda_{pk}': 1, f'xp_atual_{pk}': 125, f'ouro_{pk}': 50}, follow=True, headers={'X-Admin-Panel': 'character_modal'})
        payload = response.json()
        self.assertEqual(payload['state']['selected'], str(pk))
        self.assertFalse(payload['invalid'])
        self.assertIn('125', payload['html'])
        self.assertTrue(payload['messages'])

    def test_invalid_event_background_save_keeps_bound_errors(self):
        response = self.client.post(self.url, self.event_payload(event_id=self.event.pk,
            data_limite_inscricao=(timezone.now() + timedelta(days=12)).strftime('%Y-%m-%dT%H:%M')),
            headers={'X-Admin-Panel': 'larp_modal'})
        payload = response.json()
        self.assertTrue(payload['invalid'])
        self.assertIn('Novo LARP', payload['html'])
        self.event.refresh_from_db()
        self.assertEqual(self.event.titulo, 'LARP de teste')

    def test_wiki_background_create_returns_selected_content(self):
        response = self.client.post(self.url, {'action': 'wiki_save', 'wiki_category': 'itens', 'name': 'Item em segundo plano',
            'slug': 'item-em-segundo-plano', 'descricao': 'Conteúdo salvo sem navegação.'}, follow=True,
            headers={'X-Admin-Panel': 'wiki_panel'})
        payload = response.json()
        self.assertEqual(payload['panel'], 'wiki_panel')
        self.assertEqual(payload['state']['mode'], '')
        self.assertTrue(payload['state']['selected'])
        self.assertIn('Conteúdo salvo sem navegação.', payload['html'])
