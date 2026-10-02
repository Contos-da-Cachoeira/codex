from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import SimpleTestCase, RequestFactory
from django.urls import resolve, reverse
from django.utils.html import escape
from wiki.views import _itens_ordenados, _classes_ordenadas, _magias_ordenadas, _talentos_ordenados, _regras_ordenadas


class WikiPresentationTests(SimpleTestCase):
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
