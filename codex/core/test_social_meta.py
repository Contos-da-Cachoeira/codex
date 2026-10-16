from html.parser import HTMLParser

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from core.models import LarpEvento
from personagens.models import Personagem
from wiki.models import WikiEntry


class Metadata(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('property') or attrs.get('name')
            self.tags.setdefault(key, []).append(attrs.get('content'))


@override_settings(MEDIA_URL='/media/')
class SocialMetadataTests(TestCase):
    def metadata(self, path, **headers):
        response = self.client.get(path, HTTP_HOST='testserver', **headers)
        self.assertEqual(response.status_code, 200)
        return Metadata(response.content.decode().split('</head>', 1)[0]).tags

    def test_home_has_absolute_preview_urls_before_any_javascript(self):
        self.assertIsNotNone(settings.SECURE_PROXY_SSL_HEADER)
        proxy_header, https_value = settings.SECURE_PROXY_SSL_HEADER
        tags = self.metadata('/?utm_source=whatsapp', **{proxy_header: https_value})
        self.assertEqual(tags['og:url'], ['https://testserver/'])
        self.assertEqual(tags['og:image'], ['https://testserver/static/core/img/share-card.png?v=1'])
        self.assertEqual(tags['twitter:image'], tags['og:image'])
        self.assertEqual(tags['og:title'], ['Codex · Contos da Cachoeira'])
        self.assertEqual(tags['og:image:width'], ['1200'])
        self.assertEqual(tags['og:image:height'], ['630'])

    def test_each_published_wiki_category_uses_its_own_uploaded_image(self):
        for category, detail in (('classes', 'classe'), ('itens', 'item'), ('regras', 'regra'),
                                 ('magias', 'magia'), ('talentos', 'talento'), ('cenario', 'cenario')):
            with self.subTest(category=category):
                entry = WikiEntry.objects.create(category=category, slug='share-test', name='Novo conteúdo',
                    visible=True, image=f'wiki/{category}.png', data={'descricao': 'Descrição pública.'})
                tags = self.metadata(reverse(f'wiki_{detail}_detalhe', args=[entry.slug]))
                self.assertEqual(tags['og:title'], [entry.name])
                self.assertEqual(tags['og:description'], ['Descrição pública.'])
                self.assertEqual(tags['og:image'], [f'http://testserver/media/wiki/{category}.png'])
                self.assertNotIn('og:image:width', tags)

    def test_wiki_static_image_fallback_and_text_without_image(self):
        entry = WikiEntry.objects.create(category='itens', slug='sem-foto', visible=True,
            name='Item "Especial" <script>', data={'descricao': '<b>Guildas &amp; personagens</b>',
                'imagem': 'core/img/classes/Mago-ink.png'})
        url = reverse('wiki_item_detalhe', args=[entry.slug])
        tags = self.metadata(url)
        self.assertEqual(tags['og:image'], ['http://testserver/static/core/img/classes/Mago-ink.png'])
        self.assertEqual(tags['og:title'], ['Item "Especial"'])
        self.assertEqual(tags['og:description'], ['Guildas & personagens'])
        entry.data = {'descricao': 'Agora sem imagem.'}
        entry.save()
        tags = self.metadata(url)
        self.assertNotIn('og:image', tags)
        self.assertNotIn('twitter:image', tags)
        self.assertEqual(tags['twitter:card'], ['summary'])

    def test_guild_uses_public_information_even_for_an_admin(self):
        from guildas.models import Guilda
        guild = Guilda.objects.get(guilda_id=2)
        guild.descricao_interna = 'SEGREDO DA GUILDA'
        guild.save()
        user = User.objects.create_user('share-admin', is_staff=True)
        self.client.force_login(user)
        tags = self.metadata(reverse('detalhe_guilda', args=['circulo-do-fogo']))
        self.assertEqual(tags['og:title'], ['Círculo do Fogo'])
        self.assertEqual(tags['og:image'], ['http://testserver/static/core/img/guildas/circulo-do-fogo.png'])
        self.assertNotIn('SEGREDO DA GUILDA', str(tags))

    def test_only_the_public_event_view_uses_its_cover_and_story(self):
        now = timezone.now()
        event = LarpEvento.objects.create(titulo='Aventura pública', historia='<p>Uma nova aventura.</p>',
            local='Cachoeira', data_evento=now, data_limite_inscricao=now, visivel_publicamente=True,
            capa='larps/capas/aventura.png')
        url = reverse('detalhe_larp', args=[event.slug])
        tags = self.metadata(url)
        self.assertEqual(tags['og:title'], [event.titulo])
        self.assertEqual(tags['og:description'], ['Uma nova aventura.'])
        self.assertEqual(tags['og:image'], ['http://testserver/media/larps/capas/aventura.png'])
        user = User.objects.create_user('event-admin', is_staff=True)
        self.client.force_login(user)
        self.assertNotIn('og:image', self.metadata(url))
        event.visivel_publicamente = False
        event.save()
        self.assertNotIn('og:title', self.metadata(url))
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_lists_have_no_generic_cover_and_restricted_pages_have_no_social_metadata(self):
        for url in ('/wiki/', '/wiki/documentos/', '/guildas/', '/larps/'):
            with self.subTest(url=url):
                tags = self.metadata(url)
                self.assertIn('og:title', tags)
                self.assertNotIn('og:image', tags)
        self.assertNotIn('og:title', self.metadata(reverse('login')))
        user = User.objects.create_user('private-player')
        character = Personagem.objects.create(usuario=user, nome='Ficha restrita', classe=1)
        url = reverse('detalhe_personagem', args=[character.slug])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(user)
        self.assertNotIn('og:title', self.metadata(url))
        user.is_staff = True
        user.save()
        self.assertNotIn('og:title', self.metadata(reverse('admin_dashboard')))

    def test_cover_and_favicons_are_valid_pngs_and_linked_in_the_html(self):
        for filename, size in (('share-card.png', (1200, 630)), ('favicon-32.png', (32, 32)),
                               ('apple-touch-icon.png', (180, 180))):
            with self.subTest(filename=filename):
                image_path = finders.find(f'core/img/{filename}')
                self.assertIsNotNone(image_path)
                with Image.open(image_path) as image:
                    self.assertEqual(image.format, 'PNG')
                    self.assertEqual(image.size, size)
                    image.verify()
        response = self.client.get('/')
        self.assertContains(response, '/static/core/img/favicon-32.png?v=1')
        self.assertContains(response, '/static/core/img/apple-touch-icon.png?v=1')
