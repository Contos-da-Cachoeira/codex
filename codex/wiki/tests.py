from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import TestCase, RequestFactory
from django.urls import resolve, reverse
from django.utils.html import escape
from wiki.views import _itens_ordenados, _classes_ordenadas, _magias_ordenadas, _talentos_ordenados, _regras_ordenadas
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from io import BytesIO
from tempfile import TemporaryDirectory
from wiki.models import WikiEntry
from core.models import Profile
from wiki.editor import panel_url


class WikiPresentationTests(TestCase):
    def test_home_covers_counts_and_search_catalog_only_use_published_content(self):
        WikiEntry.objects.update(visible=False)
        visible = WikiEntry.objects.create(
            category='classes', slug='classe-publica', name='Classe pública', visible=True,
            image='wiki/capa-publica.png',
            data={'imagem': 'core/img/classes/Mago-ink.png', 'descricao': 'Descrição pública', 'tipo': 'Suporte'},
        )
        hidden = WikiEntry.objects.create(
            category='classes', slug='classe-secreta', name='Classe secreta',
            image='wiki/capa-secreta.png', data={'descricao': 'Descrição secreta'},
        )
        response = self.client.get(reverse('wiki_home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([entry['name'] for entry in response.context['entries']], [visible.name])
        section = next(section for section in response.context['sections'] if section['key'] == 'classes')
        self.assertEqual(section['count'], 1)
        self.assertEqual(section['image_url'], visible.image.url)
        self.assertEqual(response.context['hero_image'], visible.image.url)
        self.assertContains(response, visible.image.url)
        self.assertNotContains(response, hidden.name)
        self.assertNotContains(response, hidden.image.url)
        self.assertNotContains(response, 'Descrição secreta')

    def test_home_handles_an_empty_library_without_broken_images(self):
        WikiEntry.objects.update(visible=False)
        response = self.client.get(reverse('wiki_home'))
        self.assertContains(response, 'Conteúdos em preparação')
        self.assertEqual(response.context['entries'], [])
        self.assertEqual(response.context['hero_image'], '')
        self.assertTrue(all(section['count'] == 0 for section in response.context['sections']))
        self.assertNotContains(response, 'src=""')

    def test_every_item_has_art_in_catalog_and_detail(self):
        items = _itens_ordenados()
        catalog = render_to_string('wiki/itens_lista.html', {'itens': items})
        for item in items:
            with self.subTest(item=item['slug']):
                self.assertIsNotNone(finders.find(item['imagem']))
                self.assertIn(item['imagem'], catalog)
                detail = render_to_string('wiki/item_detalhe.html', {'item': item})
                self.assertIn(item['imagem'], detail)
                self.assertIn(escape(item['descricao']), detail)

    def test_all_wiki_sections_render_with_navigation(self):
        for section, singular, entries in [
            ('classes', 'classe', _classes_ordenadas()),
            ('magias', 'magia', _magias_ordenadas()),
            ('talentos', 'talento', _talentos_ordenados()),
            ('regras', 'regra', _regras_ordenadas()),
        ]:
            with self.subTest(section=section):
                request = RequestFactory().get(reverse(f'wiki_{section}_lista'))
                request.resolver_match = resolve(request.path)
                html = render_to_string(f'wiki/{section}_lista.html', {section: entries, 'request': request})
                self.assertIn('aria-current="page"', html)
                for entry in entries:
                    render_to_string(f'wiki/{singular}_detalhe.html', {singular: entry})

    def test_magic_and_talent_text_is_preserved_in_full(self):
        from wiki.constants.magias import REGRAS_GERAIS_MAGIA
        groups = [
            ('magias', 'magia', _magias_ordenadas(), ('nome', 'tipo', 'invocacao', 'descricao', 'extra')),
            ('talentos', 'talento', _talentos_ordenados(), ('nome', 'descricao', 'requisito', 'restricao', 'extra')),
            ('classes', 'classe', _classes_ordenadas(), ('nome', 'tipo', 'descricao', 'sabe_usar', 'defesas', 'magia', 'item_inicial', 'habilidade_especial', 'extra')),
        ]
        for plural, singular, entries, fields in groups:
            catalog = render_to_string(f'wiki/{plural}_lista.html', {plural: entries, 'regras_gerais_magia': REGRAS_GERAIS_MAGIA})
            if plural == 'magias':
                for rule in REGRAS_GERAIS_MAGIA['itens']:
                    self.assertIn(escape(rule), catalog)
            for entry in entries:
                with self.subTest(section=plural, slug=entry['slug']):
                    self.assertIn(escape(entry['descricao']), catalog)
                    detail = render_to_string(f'wiki/{singular}_detalhe.html', {singular: entry})
                    for field in fields:
                        if entry.get(field):
                            self.assertIn(escape(entry[field]), detail)
                    for text in entry.get('habilidade_detalhes', []):
                        self.assertIn(escape(text), detail)
                    for name in entry.get('quem_usa', []):
                        self.assertIn(escape(name), detail)

    def test_classes_spells_and_talents_have_art_in_both_pages(self):
        from django.templatetags.static import static
        for plural, singular, entries in [
            ('classes', 'classe', _classes_ordenadas()),
            ('magias', 'magia', _magias_ordenadas()),
            ('talentos', 'talento', _talentos_ordenados()),
        ]:
            catalog = render_to_string(f'wiki/{plural}_lista.html', {plural: entries})
            for entry in entries:
                with self.subTest(section=plural, slug=entry['slug']):
                    self.assertIsNotNone(finders.find(entry['imagem']))
                    art_url = static(entry['imagem'])
                    self.assertIn(art_url, catalog)
                    detail = render_to_string(f'wiki/{singular}_detalhe.html', {singular: entry})
                    self.assertIn(art_url, detail)


class WikiEditorTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('editor', password='password', is_staff=True)
        self.player = User.objects.create_user('jogador', password='password')

    def test_only_admin_can_read_and_mutate_editor(self):
        entry = WikiEntry.objects.filter(category='itens').first()
        for user in [None, self.player]:
            if user:
                self.client.force_login(user)
            for mode in ['', 'new', 'edit', 'delete']:
                url = panel_url(wiki_action=mode, wiki_id=entry.pk)
                self.assertEqual(self.client.get(url).status_code, 302)
            for action in ['wiki_save', 'wiki_delete', 'wiki_visibility']:
                self.assertEqual(self.client.post(reverse('admin_dashboard'), {
                    'action': action, 'wiki_id': entry.pk, 'name': 'Alteração indevida', 'slug': entry.slug,
                }).status_code, 302)
        entry.refresh_from_db()
        self.assertTrue(entry.visible)

    def test_profile_admin_can_edit_without_staff(self):
        Profile.objects.update_or_create(user=self.player, defaults={'role': Profile.UserRole.ADMIN})
        self.client.force_login(self.player)
        self.assertEqual(self.client.get(panel_url()).status_code, 200)

    def test_create_edit_publish_hide_delete(self):
        self.client.force_login(self.admin)
        create = panel_url(wiki_action='new', wiki_category='itens')
        payload = {'name': 'Relíquia de teste', 'slug': 'reliquia-de-teste', 'descricao': 'Texto secreto',
                   'tipo': 'Relíquia', 'valor': '3 DO', 'raridade': 'Raro', 'action': 'wiki_save', 'wiki_category': 'itens'}
        response = self.client.post(create, payload)
        entry = WikiEntry.objects.get(slug=payload['slug'])
        self.assertRedirects(response, panel_url(wiki_selected=entry.pk))
        detail = reverse('wiki_item_detalhe', args=[entry.slug])
        self.assertFalse(entry.visible)
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertNotContains(self.client.get(reverse('wiki_home')), entry.name)
        self.assertNotContains(self.client.get(reverse('wiki_itens_lista')), entry.name)
        self.assertEqual(self.client.get(panel_url(wiki_action='visibility', wiki_id=entry.pk)).status_code, 404)
        entry.refresh_from_db()
        self.assertFalse(entry.visible)
        self.client.post(panel_url(), {'action': 'wiki_visibility', 'wiki_id': entry.pk})
        self.assertContains(self.client.get(detail), 'Texto secreto')
        self.assertContains(self.client.get(reverse('wiki_home')), entry.name)
        payload.update({'descricao': 'Texto revisado', 'visible': 'on', 'wiki_id': entry.pk})
        self.client.post(panel_url(), payload)
        self.assertContains(self.client.get(detail), 'Texto revisado')
        self.client.post(panel_url(), {'action': 'wiki_visibility', 'wiki_id': entry.pk})
        self.assertEqual(self.client.get(detail).status_code, 404)
        delete = panel_url(wiki_action='delete', wiki_id=entry.pk)
        self.assertContains(self.client.get(delete), 'Confirmar exclusão')
        self.assertTrue(WikiEntry.objects.filter(pk=entry.pk).exists())
        self.client.post(delete, {'action': 'wiki_delete', 'wiki_id': entry.pk})
        self.assertFalse(WikiEntry.objects.filter(pk=entry.pk).exists())
        self.assertEqual(self.client.get(detail).status_code, 404)

    def test_hidden_entries_are_absent_from_every_public_section(self):
        for category, singular in [('regras', 'regra'), ('classes', 'classe'), ('talentos', 'talento'),
                                   ('magias', 'magia'), ('itens', 'item')]:
            entry = WikiEntry.objects.filter(category=category).first()
            entry.visible = False
            entry.save()
            self.assertEqual(self.client.get(reverse(f'wiki_{singular}_detalhe', args=[entry.slug])).status_code, 404)
            self.assertNotContains(self.client.get(reverse(f'wiki_{category}_lista')), entry.name)
            home = self.client.get(reverse('wiki_home'))
            self.assertNotIn(reverse(f'wiki_{singular}_detalhe', args=[entry.slug]),
                             [item['url'] for item in home.context['entries']])

    def test_upload_replace_remove_and_invalid_image(self):
        self.client.force_login(self.admin)
        entry = WikiEntry.objects.filter(category='itens').first()
        edit = panel_url(wiki_action='edit', wiki_id=entry.pk)
        payload = {'name': entry.name, 'slug': entry.slug, 'visible': 'on', 'descricao': 'Texto',
                   'action': 'wiki_save', 'wiki_id': entry.pk}
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            for color in ['red', 'blue']:
                stream = BytesIO()
                Image.new('RGB', (8, 8), color).save(stream, format='PNG')
                payload['image'] = SimpleUploadedFile(f'{color}.png', stream.getvalue(), content_type='image/png')
                self.assertEqual(self.client.post(edit, payload).status_code, 302)
                entry.refresh_from_db()
                self.assertIn(color, entry.image.name)
                self.assertContains(self.client.get(reverse('wiki_item_detalhe', args=[entry.slug])), entry.image.url)
                self.assertContains(self.client.get(reverse('wiki_itens_lista')), entry.image.url)
            payload['image'] = SimpleUploadedFile('fake.png', b'not an image', content_type='image/png')
            self.assertEqual(self.client.post(edit, payload).status_code, 200)
            entry.refresh_from_db()
            self.assertIn('blue', entry.image.name)
            del payload['image']
            payload['remove_image'] = 'on'
            self.assertEqual(self.client.post(edit, payload).status_code, 302)
            entry.refresh_from_db()
            self.assertFalse(entry.image)
            self.assertNotIn('imagem', entry.data)

    def test_rule_sections_round_trip_and_duplicate_slug_validation(self):
        self.client.force_login(self.admin)
        entry = WikiEntry.objects.filter(category='regras').first()
        original = entry.data['secoes']
        self.assertContains(self.client.get(panel_url(wiki_action='edit', wiki_id=entry.pk)), original[0]['titulo'])
        payload = {'name': entry.name, 'slug': entry.slug, 'visible': 'on',
                   'secoes': 'Nova seção\nPrimeiro tópico\nSegundo tópico\n\nOutra seção\nOutro tópico',
                   'action': 'wiki_save', 'wiki_id': entry.pk}
        self.assertEqual(self.client.post(panel_url(), payload).status_code, 302)
        entry.refresh_from_db()
        self.assertEqual(entry.data['secoes'][0]['itens'], ['Primeiro tópico', 'Segundo tópico'])
        self.assertContains(self.client.get(reverse('wiki_regra_detalhe', args=[entry.slug])), 'Outro tópico')
        payload.pop('wiki_id')
        payload['wiki_category'] = 'regras'
        self.assertEqual(self.client.post(panel_url(), payload).status_code, 200)

    def test_csrf_is_required_for_mutations(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        entry = WikiEntry.objects.first()
        self.assertEqual(client.post(panel_url(), {'action': 'wiki_visibility', 'wiki_id': entry.pk}).status_code, 403)

    def test_hidden_magic_rules_do_not_render(self):
        entry = WikiEntry.objects.get(category='magia_geral')
        entry.visible = False
        entry.save()
        self.assertNotContains(self.client.get(reverse('wiki_magias_lista')), entry.name)

    def test_wiki_list_and_editor_render_inside_admin_tabs(self):
        self.client.force_login(self.admin)
        response = self.client.get(panel_url())
        self.assertContains(response, 'data-wiki-create', count=1)
        self.assertContains(response, 'data-admin-tab="larp_modal"')
        self.assertContains(response, 'data-admin-tab="wiki_panel"')
        self.assertNotContains(response, 'Abrir editor da wiki')
        self.assertNotContains(response, '/wiki/gerenciar/')
        entry = WikiEntry.objects.first()
        response = self.client.get(panel_url(wiki_action='edit', wiki_id=entry.pk))
        self.assertContains(response, 'Salvar conteúdo')
        self.assertContains(response, 'data-admin-tab="wiki_panel"')
        self.assertContains(response, 'data-admin-initial-tab="wiki_panel"')
        self.assertEqual(response.templates[0].name, 'dashboard/admin_dashboard.html')
        self.assertRedirects(self.client.get(reverse('wiki_admin_list')), panel_url())

    def test_filters_survive_actions_without_affecting_user_filters(self):
        self.client.force_login(self.admin)
        entry = WikiEntry.objects.filter(category='itens').first()
        filters = {'wiki_q': entry.name, 'wiki_section': 'itens'}
        response = self.client.get(panel_url(**filters))
        self.assertEqual([row['entry'] for row in response.context['wiki_rows']], [entry])
        self.assertEqual(response.context['q_value'], '')
        self.assertContains(response, 'data-admin-initial-tab="wiki_panel"')
        response = self.client.post(panel_url(), {'action': 'wiki_visibility', 'wiki_id': entry.pk, **filters})
        self.assertRedirects(response, panel_url(wiki_selected=entry.pk, **filters))

    def test_validation_errors_stay_in_wiki_tab_and_preserve_input(self):
        self.client.force_login(self.admin)
        response = self.client.post(panel_url(), {'action': 'wiki_save', 'wiki_category': 'itens',
                                                  'name': 'Rascunho incompleto', 'slug': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['wiki_form'].errors)
        self.assertContains(response, 'Rascunho incompleto')
        self.assertContains(response, 'data-admin-initial-tab="wiki_panel"')
        self.assertFalse(WikiEntry.objects.filter(name='Rascunho incompleto').exists())

    def test_selection_displays_complete_details_and_grouped_thumbnails(self):
        self.client.force_login(self.admin)
        for category, _ in WikiEntry.CATEGORIES:
            entry = WikiEntry.objects.filter(category=category).first()
            response = self.client.get(panel_url(wiki_selected=entry.pk))
            self.assertEqual(response.context['wiki_selected'], entry)
            self.assertContains(response, f'data-wiki-select="{entry.pk}"')
            self.assertContains(response, 'aria-current="true"')
            group = next(group for group in response.context['wiki_groups'] if group['key'] == category)
            self.assertTrue(group['open'])
            self.assertEqual(sum(len(group['rows']) for group in response.context['wiki_groups']), WikiEntry.objects.count())
            for field in response.context['wiki_information']:
                if field['kind'] == 'text':
                    self.assertContains(response, escape(str(field['value'])))
            if entry.data.get('imagem'):
                self.assertContains(response, entry.data['imagem'])

    def test_hidden_selected_entry_and_image_less_entry_can_be_inspected(self):
        self.client.force_login(self.admin)
        entry = WikiEntry.objects.create(category='itens', name='Rascunho sem imagem', slug='rascunho-sem-imagem',
                                        data={'descricao': '<script>alert(1)</script>', 'alquimico': False})
        response = self.client.get(panel_url(wiki_selected=entry.pk))
        self.assertContains(response, 'Oculto para os jogadores')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertEqual(response.context['wiki_image_url'], '')
        self.assertIn({'label': 'Alquímico', 'value': 'Não', 'kind': 'text', 'wide': False}, response.context['wiki_information'])
        self.assertEqual(self.client.get(reverse('wiki_item_detalhe', args=[entry.slug])).status_code, 404)

    def test_editing_keeps_catalog_and_returns_to_selected_details(self):
        self.client.force_login(self.admin)
        entry = WikiEntry.objects.filter(category='itens').first()
        response = self.client.get(panel_url(wiki_action='edit', wiki_id=entry.pk))
        self.assertTrue(response.context['wiki_groups'])
        self.assertEqual(response.context['wiki_selected'], entry)
        self.assertEqual(response.context['wiki_back_url'], panel_url(wiki_selected=entry.pk))
        response = self.client.post(panel_url(), {'action': 'wiki_save', 'wiki_id': entry.pk,
                                                 'name': entry.name, 'slug': entry.slug, 'descricao': 'Texto atualizado'})
        self.assertRedirects(response, panel_url(wiki_selected=entry.pk))
        self.assertContains(self.client.get(response.url), 'Texto atualizado')

    def test_empty_filtered_catalog_has_no_unrelated_selection(self):
        self.client.force_login(self.admin)
        response = self.client.get(panel_url(wiki_q='nenhuma-entrada-com-este-nome'))
        self.assertIsNone(response.context['wiki_selected'])
        self.assertContains(response, 'Nenhum conteúdo encontrado.')

    def test_create_starts_with_section_choice_then_shows_matching_fields(self):
        self.client.force_login(self.admin)
        count = WikiEntry.objects.count()
        response = self.client.get(panel_url(wiki_action='new'))
        self.assertContains(response, 'Escolha a seção do novo conteúdo.')
        self.assertNotContains(response, 'Salvar conteúdo')
        for category, field in [('regras', 'secoes'), ('classes', 'habilidade_especial'),
                                ('talentos', 'custo_xp'), ('magias', 'invocacao'), ('itens', 'valor')]:
            with self.subTest(category=category):
                response = self.client.get(panel_url(wiki_action='new', wiki_category=category))
                self.assertEqual(response.context['wiki_entry'].category, category)
                self.assertIn(field, response.context['wiki_form'].fields)
                self.assertContains(response, 'Salvar conteúdo')
                self.assertContains(response, 'Seção do novo conteúdo')
        self.assertEqual(WikiEntry.objects.count(), count)
