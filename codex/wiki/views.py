from django.http import Http404
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse

from .models import WikiEntry


def _published(category):
    return [entry.as_content() for entry in WikiEntry.objects.filter(category=category, visible=True)]


def _regras_ordenadas():
    return sorted(_published('regras'), key=lambda item: (item.get('ordem', 999), item.get('titulo', '')))


def _classes_ordenadas():
    return _published('classes')


def _itens_ordenados():
    return _published('itens')


def _talentos_ordenados():
    return sorted(_published('talentos'), key=lambda item: (item.get('custo_xp', 0), item.get('nome', '')))


def _magias_ordenadas():
    return _published('magias')


def wiki_home(request):
    sections = []
    entries = []

    def image_url(item):
        return item.get('image_url') or (static(item['imagem']) if item.get('imagem') else '')

    for name, plural, singular, description, items in [
        ('Regras', 'regras', 'regra', 'Entenda o jogo, os combates e as possibilidades da sua aventura.', _regras_ordenadas()),
        ('Classes', 'classes', 'classe', 'Encontre seu estilo de jogo e conheça as habilidades de cada classe.', _classes_ordenadas()),
        ('Talentos', 'talentos', 'talento', 'Explore novas habilidades e planeje a evolução do personagem.', _talentos_ordenados()),
        ('Magias', 'magias', 'magia', 'Consulte invocações, efeitos e quem pode usar cada magia.', _magias_ordenadas()),
        ('Itens', 'itens', 'item', 'Prepare seu inventário com equipamentos e recursos alquímicos.', _itens_ordenados()),
        ('Cenário', 'cenario', 'cenario', 'Explore a história, as divindades e os lugares dos Contos da Cachoeira.', _published('cenario')),
    ]:
        images = [image_url(item) for item in items]
        sections.append({'key': plural, 'name': name, 'description': description, 'count': len(items),
                         'image_url': next((url for url in images if url), ''),
                         'url': reverse(f'wiki_{plural}_lista')})
        for item, image in zip(items, images):
            entries.append({'name': item.get('nome') or item.get('titulo'), 'section': name,
                            'category': plural, 'image_url': image,
                            'detail': item.get('tipo') or item.get('categoria') or item.get('raridade', ''),
                            'keywords': ' '.join(str(item.get(key, '')) for key in ('tipo', 'categoria', 'raridade', 'quem_usa')),
                            'description': item.get('resumo') or item.get('descricao', ''),
                            'url': reverse(f'wiki_{singular}_detalhe', args=[item['slug']])})
    hero_image = next((entry['image_url'] for entry in entries
                       if entry['category'] == 'classes' and entry['image_url']), '')
    return render(request, 'wiki/home.html', {
        'sections': sections, 'entries': entries, 'hero_image': hero_image,
    })


def regras_lista(request):
    context = {
        'regras': _regras_ordenadas(),
    }
    return render(request, 'wiki/regras_lista.html', context)


def cenario_lista(request):
    return render(request, 'wiki/cenario_lista.html', {'entries': _published('cenario')})


def cenario_detalhe(request, slug):
    entry = next((item for item in _published('cenario') if item['slug'] == slug), None)
    if not entry:
        raise Http404('Referência do cenário não encontrada.')
    return render(request, 'wiki/cenario_detalhe.html', {'entry': entry})


def regra_detalhe(request, slug):
    regra = next((item for item in _regras_ordenadas() if item.get('slug') == slug), None)
    if not regra:
        raise Http404('Regra nao encontrada.')

    context = {
        'regra': regra,
    }
    return render(request, 'wiki/regra_detalhe.html', context)


def classes_lista(request):
    context = {
        'classes': _classes_ordenadas(),
    }
    return render(request, 'wiki/classes_lista.html', context)


def classe_detalhe(request, slug):
    classe = next((item for item in _classes_ordenadas() if item.get('slug') == slug), None)
    if not classe:
        raise Http404('Classe nao encontrada.')

    context = {
        'classe': classe,
    }
    return render(request, 'wiki/classe_detalhe.html', context)


def itens_lista(request):
    context = {
        'itens': _itens_ordenados(),
    }
    return render(request, 'wiki/itens_lista.html', context)


def item_detalhe(request, slug):
    item = next((item for item in _itens_ordenados() if item.get('slug') == slug), None)
    if not item:
        raise Http404('Item nao encontrado.')

    context = {
        'item': item,
    }
    return render(request, 'wiki/item_detalhe.html', context)


def talentos_lista(request):
    context = {
        'talentos': _talentos_ordenados(),
    }
    return render(request, 'wiki/talentos_lista.html', context)


def talento_detalhe(request, slug):
    talento = next((item for item in _talentos_ordenados() if item.get('slug') == slug), None)
    if not talento:
        raise Http404('Talento nao encontrado.')

    context = {
        'talento': talento,
    }
    return render(request, 'wiki/talento_detalhe.html', context)


def magias_lista(request):
    context = {
        'magias': _magias_ordenadas(),
        'regras_gerais_magia': next(iter(_published('magia_geral')), {}),
    }
    return render(request, 'wiki/magias_lista.html', context)


def magia_detalhe(request, slug):
    magia = next((item for item in _magias_ordenadas() if item.get('slug') == slug), None)
    if not magia:
        raise Http404('Magia nao encontrada.')

    context = {
        'magia': magia,
    }
    return render(request, 'wiki/magia_detalhe.html', context)
