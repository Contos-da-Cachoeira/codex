from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase
from django.template.loader import get_template, render_to_string

from core.models import SiteLayoutConfig
from dashboard.views import admin_dashboard, admin_user_profile
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import LarpEvento
from core.views import inscricao_larp, detalhe_larp, planilha_larp


class AdminUserProfileTests(SimpleTestCase):
    def test_birth_date_fields_reject_future_dates(self):
        from accounts.forms import RegisterForm, AccountPersonalDataForm
        from personagens.forms import PersonagemCreateForm, LarpInscricaoEventoForm
        self.assertNotIn('data_nascimento', RegisterForm.base_fields)
        self.assertNotIn('data_nascimento', PersonagemCreateForm.base_fields)
        for form_class in (AccountPersonalDataForm, LarpInscricaoEventoForm):
            field = form_class.base_fields['data_nascimento']
            self.assertEqual(field.clean('1995-06-15').isoformat(), '1995-06-15')
            with self.assertRaises(ValidationError):
                field.clean(timezone.localdate() + timedelta(days=1))
            with self.assertRaises(ValidationError):
                field.clean('')

    def test_birth_date_templates_compile(self):
        for name in ('accounts/register.html', 'accounts/account_personal_data.html',
                     'personagens/criar_personagem.html'):
            get_template(name)

    def test_common_user_cannot_view_profiles(self):
        request = RequestFactory().get('/area-admin/usuarios/1/')
        request.user = SimpleNamespace(is_authenticated=True, is_staff=False, is_superuser=False)
        with patch('dashboard.views.get_object_or_404') as lookup:
            response = admin_user_profile(request, 1)
        self.assertEqual(response.status_code, 302)
        lookup.assert_not_called()

    def test_anonymous_user_must_log_in(self):
        request = RequestFactory().get('/area-admin/usuarios/1/')
        request.user = SimpleNamespace(is_authenticated=False)
        response = admin_user_profile(request, 1)
        self.assertEqual(response.status_code, 302)
        self.assertIn('next=', response.url)

    def test_profile_template_handles_missing_profile(self):
        account = SimpleNamespace(username='demo', is_superuser=False, is_active=True,
                                  get_full_name='Demo User', email='', last_login=None)
        html = render_to_string('dashboard/admin_user_profile.html', {
            'account': account, 'player_profile': None, 'characters': [], 'registrations': [],
        })
        self.assertIn('Demo User', html)
        self.assertIn('Nenhum personagem cadastrado.', html)


class HomeComponentTests(SimpleTestCase):
    def test_image_drag_accepts_decimal_positions(self):
        from core.forms import ImageAssetForm
        form = ImageAssetForm(dict(url='https://example.com/image.jpg', x='37.123456', y='68.987654', zoom='1.25', ratio='1.7777777778'))
        self.assertTrue(form.is_valid(), form.errors)
        asset = form.save(commit=False)
        self.assertAlmostEqual(asset.x, 37.123456)
        self.assertAlmostEqual(asset.y, 68.987654)
        html = render_to_string('core/includes/image_asset.html', {'asset': asset})
        self.assertIn('37.123456%', html)

    def test_banner_buttons_and_unsafe_urls(self):
        import json
        from dashboard.home_components import parse_components
        data = dict(kind='banner', title='Aventura', content='Texto', is_visible=True,
                    button_label='Participar', button_url='/larps/')
        section = parse_components(json.dumps([data]))[0]
        html = render_to_string('dashboard/home_component.html', {'component': section})
        self.assertIn('home-split-banner', html)
        self.assertIn('href="/larps/"', html)
        for url in ('javascript:alert(1)', '//evil.example', '/\\evil.example'):
            with self.assertRaises(ValidationError):
                parse_components(json.dumps([dict(data, button_url=url)]))
        section = parse_components(json.dumps([dict(data, kind='callout')]))[0]
        html = render_to_string('dashboard/home_component.html', {'component': section})
        self.assertIn('home-callout', html)
        self.assertNotIn('home-banner-art', html)

    def test_image_url_and_crop_validation(self):
        from core.forms import ImageAssetForm
        data = dict(url='https://example.com/image.jpg', x=50, y=50, zoom=1.5, ratio=1)
        self.assertTrue(ImageAssetForm(data).is_valid())
        for invalid in (dict(zoom=4), dict(x=-1), dict(url='javascript:alert(1)'), dict(ratio=0)):
            self.assertFalse(ImageAssetForm(dict(data, **invalid)).is_valid())

    def test_uploaded_image_validation(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from core.forms import ImageAssetForm
        buffer = BytesIO()
        Image.new('RGB', (20, 20), 'blue').save(buffer, format='PNG')
        data = dict(x=50, y=50, zoom=1, ratio=1)
        form = ImageAssetForm(data, {'file': SimpleUploadedFile('test.png', buffer.getvalue(), content_type='image/png')})
        self.assertTrue(form.is_valid(), form.errors)
        invalid = ImageAssetForm(data, {'file': SimpleUploadedFile('test.png', b'not an image')})
        self.assertFalse(invalid.is_valid())

    def test_parse_order_visibility_and_invalid_type(self):
        import json
        from dashboard.home_components import parse_components
        data = [dict(kind='community', title='Guildas', content='', is_visible=True),
                dict(kind='text', title='Oculto', content='Texto', is_visible=False)]
        sections = parse_components(json.dumps(data))
        self.assertEqual([s.display_order for s in sections], [1, 2])
        self.assertFalse(sections[1].is_visible)
        data[0]['kind'] = 'invalid'
        with self.assertRaises(ValidationError):
            parse_components(json.dumps(data))

    def test_preview_does_not_save(self):
        from dashboard.views import home_preview
        request = RequestFactory().post('/area-admin/home/previa/', {'components_json': '[]'})
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
        with patch('dashboard.views.home') as renderer, patch('core.models.HomeDynamicSection.save') as save:
            from django.http import HttpResponse
            renderer.return_value = HttpResponse('preview')
            response = home_preview(request)
            renderer.assert_called_once_with(request, components=[], preview=True)
            save.assert_not_called()
            self.assertEqual(response.status_code, 200)

    def test_preview_rejects_common_user(self):
        from dashboard.views import home_preview
        request = RequestFactory().post('/area-admin/home/previa/', {'components_json': '[]'})
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=False, is_staff=False)
        self.assertEqual(home_preview(request).status_code, 403)

    def test_shared_home_template_hides_invisible_components_and_escapes_text(self):
        from core.models import HomeDynamicSection
        html = render_to_string('dashboard/home.html', {'home_components': [
            HomeDynamicSection(title='Shown', content='<script>alert(1)</script>', kind='text', is_visible=True),
            HomeDynamicSection(title='HiddenTitle', kind='text', is_visible=False),
        ]})
        self.assertIn('Shown', html)
        self.assertNotIn('HiddenTitle', html)
        self.assertIn('&lt;script&gt;', html)
        get_template('dashboard/home_editor.html')

    def test_save_publishes_parsed_components_atomically(self):
        request = RequestFactory().post('/area-admin/', {
            'action': 'update_home_components',
            'components_json': '[{"kind":"text","title":"Published","content":"Hello","is_visible":true}]',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
        with patch('dashboard.views.HomePageConfig.load'), patch('dashboard.views.SiteLayoutConfig.load'), \
                patch('dashboard.views.transaction.atomic'), patch('dashboard.views.HomeDynamicSection.objects') as manager:
            response = admin_dashboard(request)
            self.assertEqual(response.status_code, 200)
            manager.bulk_create.assert_called_once()
            self.assertEqual(manager.bulk_create.call_args.args[0][0].title, 'Published')


class ThemeSettingsTests(SimpleTestCase):
    def setUp(self):
        self.config = SiteLayoutConfig(header_title='Custom title')
        self.fields = [field for field in self.config._meta.fields if field.name.endswith('_color')]

    def submit(self, data, admin=True):
        request = RequestFactory().post('/area-admin/', data)
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=admin, is_staff=False)
        with patch('dashboard.views.HomePageConfig.load'), \
                patch('dashboard.views.SiteLayoutConfig.load', return_value=self.config), \
                patch('dashboard.views.messages'), \
                patch.object(self.config, 'full_clean', side_effect=self.config.clean_fields), \
                patch.object(self.config, 'save') as save:
            response = admin_dashboard(request)
        return response, save

    def test_save_custom_palette_and_render_variables(self):
        data = {field.name: '#123abc' for field in self.fields}
        response, save = self.submit(dict(data, action='update_theme_config'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('open_theme_modal=1', response.url)
        save.assert_called_once()
        for field in self.fields:
            self.assertEqual(getattr(self.config, field.name), '#123ABC')
        html = render_to_string('core/base.html', {'layout_config': self.config})
        self.assertIn('--site-background: #123ABC;', html)
        self.assertIn('--codex-background: var(--site-background);', html)
        self.assertIn('--color-primary: #123ABC;', html)
        self.assertIn('color: var(--color-primary-content) !important;', html)

    def test_reset_uses_model_defaults_and_preserves_other_settings(self):
        for field in self.fields:
            setattr(self.config, field.name, '#123ABC')
        response, save = self.submit({'action': 'reset_theme_config'})
        self.assertIn('open_theme_modal=1', response.url)
        save.assert_called_once()
        for field in self.fields:
            self.assertEqual(getattr(self.config, field.name), field.get_default())
        self.assertEqual(self.config.header_title, 'Custom title')
        self.assertEqual(set(save.call_args.kwargs['update_fields']), {field.name for field in self.fields})

    def test_invalid_palette_is_not_saved(self):
        data = {field.name: '#123ABC' for field in self.fields}
        response, save = self.submit(dict(data, action='update_theme_config', primary_color='#ZZZZZZ'))
        self.assertEqual(response.status_code, 302)
        save.assert_not_called()

    def test_regular_user_cannot_reset(self):
        response, save = self.submit({'action': 'reset_theme_config'}, admin=False)
        self.assertEqual(response.status_code, 302)
        save.assert_not_called()


class LarpDeadlineTests(SimpleTestCase):
    def test_spreadsheet_url_is_registered(self):
        from django.urls import reverse, resolve
        url = reverse('planilha_larp', kwargs={'slug': 'larp-test-1'})
        self.assertEqual(url, '/larps/larp-test-1/planilha/')
        self.assertEqual(resolve(url).func, planilha_larp)

    def test_delete_event_requires_admin(self):
        for admin in (False, True):
            with self.subTest(admin=admin):
                event = MagicMock(slug='test', visivel_publicamente=True)
                request = RequestFactory().post('/larp/test/', {'action': 'delete_event'})
                request.user = SimpleNamespace(is_authenticated=True, is_superuser=admin, is_staff=False)
                with patch('core.views.get_object_or_404', return_value=event), patch('core.views.messages'), patch('core.views.LarpEventoForm'):
                    response = detalhe_larp(request, slug='test')
                self.assertEqual(response.status_code, 302)
                if admin:
                    event.delete.assert_called_once()
                    self.assertIn('#larp_modal', response.url)
                else:
                    event.delete.assert_not_called()

    def test_regular_user_cannot_edit_event(self):
        event = LarpEvento(slug='test', visivel_publicamente=True)
        request = RequestFactory().post('/larp/test/', {'action': 'edit_event', 'titulo': 'Changed'})
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=False, is_staff=False)
        with patch('core.views.get_object_or_404', return_value=event), \
                patch('core.views.messages'), patch('core.views.LarpEventoForm') as form:
            response = detalhe_larp(request, slug='test')
            self.assertEqual(response.status_code, 302)
            form.assert_not_called()

    def test_edit_event_does_not_change_payments(self):
        event = MagicMock(slug='test', visivel_publicamente=True)
        request = RequestFactory().post('/larp/test/', {'action': 'edit_event'})
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
        with (
            patch('core.views.get_object_or_404', return_value=event),
            patch('core.views.messages'),
            patch('core.views.LarpEventoForm') as form,
        ):
            form.return_value.is_valid.return_value = True
            response = detalhe_larp(request, slug='test')
            self.assertEqual(response.status_code, 302)
            form.return_value.save.assert_called_once()

    def test_event_balance_validation(self):
        from core.forms import EventCharacterBalanceForm
        self.assertTrue(EventCharacterBalanceForm({'xp': '100', 'ouro': '0'}).is_valid())
        for invalid in ('-1', '1.5', '', 'abc', '2147483648'):
            self.assertFalse(EventCharacterBalanceForm({'xp': invalid, 'ouro': '10'}).is_valid())

    def test_balance_update_only_changes_event_participant(self):
        event = MagicMock(slug='test', visivel_publicamente=True)
        character = MagicMock(pk=42, xp_atual=10, ouro=20)
        registration = SimpleNamespace(personagem=character, personagem_id=42)
        event.inscricoes.select_related.return_value.order_by.return_value = [registration]
        request = RequestFactory().post('/larp/test/', {
            'action': 'update_balances', 'character-42-xp': '150', 'character-42-ouro': '50',
            'character-99-xp': '999', 'character-99-ouro': '999',
        })
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
        with patch('core.views.get_object_or_404', return_value=event), patch('core.views.messages'), \
                patch('core.views.LarpEventoForm'), patch('core.views.transaction.atomic'):
            response = planilha_larp(request, 'test')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(character.xp_atual, 150)
        self.assertEqual(character.ouro, 50)
        character.save.assert_called_once_with(update_fields=['xp_atual', 'ouro', 'data_atualizacao'])

    def test_larp_templates_compile(self):
        for template in ('core/planilha_larp.html', 'core/listar_larps.html', 'core/detalhe_larp.html',
                         'core/inscricao_larp.html', 'dashboard/admin_dashboard.html'):
            with self.subTest(template=template):
                get_template(template)

    def test_deadline_must_not_exceed_event_date(self):
        now = timezone.now()
        event = LarpEvento(data_evento=now, data_limite_inscricao=now + timedelta(hours=1))
        with self.assertRaises(ValidationError):
            event.clean()
        event.data_limite_inscricao = now
        event.clean()

    def test_registration_deadline_boundary(self):
        now = timezone.now()
        event = LarpEvento(data_evento=now + timedelta(days=1), data_limite_inscricao=now)
        with patch('core.models.timezone.now', return_value=now):
            self.assertTrue(event.inscricoes_abertas)
        with patch('core.models.timezone.now', return_value=now + timedelta(seconds=1)):
            self.assertFalse(event.inscricoes_abertas)

    def test_expired_registration_rejects_get_and_post(self):
        now = timezone.now()
        event = LarpEvento(slug='test-event', visivel_publicamente=True,
                           data_evento=now + timedelta(days=1), data_limite_inscricao=now - timedelta(seconds=1))
        for method in ('get', 'post'):
            request = getattr(RequestFactory(), method)('/larp/')
            request.user = SimpleNamespace(is_authenticated=True, is_staff=False, is_superuser=False)
            with patch('core.views.get_object_or_404', return_value=event), \
                    patch('core.views.LarpInscricao.objects.filter') as registrations, \
                    patch('core.views.messages'), \
                    patch('core.views.LarpInscricaoEventoForm') as form:
                registrations.return_value.first.return_value = None
                response = inscricao_larp(request, slug=event.slug, token='test')
                self.assertEqual(response.status_code, 302)
                form.assert_not_called()
