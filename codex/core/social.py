"""Prévias de links apenas para o conteúdo público já exibido pelo site."""
from html import unescape
import re
from urllib.parse import urlsplit

from django.templatetags.static import static
from django.utils.html import strip_tags
from django.utils.text import Truncator


SITE_NAME = 'Codex · Contos da Cachoeira'
DESCRIPTION = 'Crie seu personagem, conheça as guildas e prepare-se para as aventuras de LARP nos Contos da Cachoeira.'
PUBLIC_PAGES = {
    'listar_guildas': ('Guildas', 'Conheça as guildas dos Contos da Cachoeira, suas histórias e seus ideais.'),
    'listar_larps': ('LARPs', 'Confira os eventos públicos de LARP dos Contos da Cachoeira.'),
    'wiki_home': ('Wiki', 'Consulte classes, talentos, magias, itens, regras e o cenário dos Contos da Cachoeira.'),
    'wiki_documentos': ('Documentos', 'Leia ou baixe o Manual LARP e o Cenário dos Contos da Cachoeira.'),
    **{f'wiki_{key}_lista': (label, f'Consulte {label.lower()} na Wiki dos Contos da Cachoeira.')
       for key, label in (('regras', 'Regras'), ('classes', 'Classes'), ('itens', 'Itens'),
                          ('talentos', 'Talentos'), ('magias', 'Magias'), ('cenario', 'Cenário'))},
}
WIKI_DETAILS = {f'wiki_{key}_detalhe': field for key, field in (
    ('regra', 'regra'), ('classe', 'classe'), ('item', 'item'),
    ('talento', 'talento'), ('magia', 'magia'), ('cenario', 'entry'))}


def _text(value):
    return Truncator(re.sub(r'\s+', ' ', strip_tags(unescape(str(value or '')))).strip()).chars(220)


def _content_image(content):
    return content.get('image_url') or (static(content['imagem']) if content.get('imagem') else '')


def public_metadata(context):
    request = context.get('request')
    if request is None or request.method not in {'GET', 'HEAD'} or not request.resolver_match:
        return {}
    route = request.resolver_match.url_name
    image, dimensions = '', None
    if route == 'home':
        title, description = SITE_NAME, DESCRIPTION
        image, dimensions = static('core/img/share-card.png') + '?v=1', ('1200', '630')
    elif route in PUBLIC_PAGES:
        title, description = PUBLIC_PAGES[route]
    elif route in WIKI_DETAILS or route == 'detalhe_guilda':
        content = context.get(WIKI_DETAILS.get(route, 'info_publica'))
        if not content:
            return {}
        title = content.get('nome') or content.get('titulo') or SITE_NAME
        description = next((content[key] for key in ('resumo', 'descricao', 'lema', 'efeito', 'texto')
                            if isinstance(content.get(key), str) and content[key].strip()), '')
        image = _content_image(content)
    elif route == 'detalhe_larp':
        event = context.get('evento')
        if not event or not event.visivel_publicamente or context.get('is_admin'):
            return {}
        title, description = event.titulo, event.historia
        image = event.capa.url if event.capa else ''
    elif route == 'wiki_documento_leitor':
        document = context.get('document')
        if not document:
            return {}
        title, description, image = document['title'], document['description'], static(document['cover'])
    else:
        # Fichas, contas, inscrições e páginas administrativas continuam restritas.
        return {}
    if image:
        image = request.build_absolute_uri(image)
        if urlsplit(image).scheme not in {'http', 'https'}:
            image = ''
    return {
        'title': _text(title), 'description': _text(description), 'site_name': SITE_NAME,
        'page_url': request.build_absolute_uri(request.path),
        'image_url': image, 'image_alt': _text(title), 'dimensions': dimensions,
    }
