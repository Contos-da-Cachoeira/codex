from types import SimpleNamespace
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from core.constants.guildas import GUILDAS
from guildas.views import GUILDA_PUBLIC_KEY_BY_ID, GUILDA_SLUG_BY_ID


class GuildPresentationTests(SimpleTestCase):
    def test_all_guild_pages_keep_private_content_restricted(self):
        for guild_id, key in GUILDA_PUBLIC_KEY_BY_ID.items():
            slug = GUILDA_SLUG_BY_ID[guild_id]
            context = {
                'guilda': SimpleNamespace(slug=slug, descricao_interna='SEGREDO_INTERNO_TESTE'),
                'info_publica': GUILDAS[key],
                'user': AnonymousUser(),
                'pode_ver_privado': False,
                'noticias': [SimpleNamespace(titulo='NOTICIA_PRIVADA_TESTE', conteudo='Conteúdo interno')],
            }
            with self.subTest(guild=slug):
                html = render_to_string(f'guildas/detalhes/{slug}.html', context)
                self.assertIn(GUILDAS[key]['nome'], html)
                self.assertNotIn('SEGREDO_INTERNO_TESTE', html)
                self.assertNotIn('NOTICIA_PRIVADA_TESTE', html)
                self.assertNotIn('Personagens aprovados', html)
                context['pode_ver_privado'] = True
                html = render_to_string(f'guildas/detalhes/{slug}.html', context)
                self.assertIn('SEGREDO_INTERNO_TESTE', html)
                self.assertIn('NOTICIA_PRIVADA_TESTE', html)
                self.assertIn('Personagens aprovados', html)
