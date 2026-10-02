from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.text import slugify

from .constants.classes import CLASSES_WIKI
from .constants.itens import ITENS_WIKI
from .constants.magias import MAGIAS_WIKI, REGRAS_GERAIS_MAGIA
from .constants.regras import REGRAS
from .constants.talentos import TALENTOS_WIKI


def _regras_ordenadas():
    return sorted(REGRAS, key=lambda item: (item.get('ordem', 999), item.get('titulo', '')))


def _classes_ordenadas():
    classes = []
    for chave, dados in CLASSES_WIKI.items():
        classe = dados.copy()
        classe['chave'] = chave
        classe['slug'] = slugify(chave.replace('_', '-'))
        classes.append(classe)

    return sorted(classes, key=lambda item: item.get('nome', ''))


def _itens_ordenados():
    itens = []
    for chave, dados in ITENS_WIKI.items():
        item = dados.copy()
        item['chave'] = chave
        item['slug'] = dados.get('slug') or slugify(chave.replace('_', '-'))
        item['imagem'] = 'wiki/img/itens/{}.png'.format(item['slug'])
        item['raridade'] = dados.get('raridade', 'Comum')
        item['alquimico'] = bool(dados.get('alquimico', False))
        itens.append(item)

    return sorted(itens, key=lambda item: item.get('nome', ''))


def _talentos_ordenados():
    talentos = []
    for chave, dados in TALENTOS_WIKI.items():
        talento = dados.copy()
        talento['chave'] = chave
        talento['slug'] = dados.get('slug') or slugify(chave.replace('_', '-'))
        talento['imagem'] = 'wiki/img/talentos/{}.png'.format(talento['slug'])
        talento['custo_xp'] = dados.get('custo_xp', 0)
        talento['stackavel'] = bool(dados.get('stackavel', False))
        talentos.append(talento)

    return sorted(talentos, key=lambda item: (item.get('custo_xp', 0), item.get('nome', '')))


def _magias_ordenadas():
    magias = []
    for chave, dados in MAGIAS_WIKI.items():
        magia = dados.copy()
        magia['chave'] = chave
        magia['slug'] = dados.get('slug') or slugify(chave.replace('_', '-'))
        magia['imagem'] = 'wiki/img/magias/{}.png'.format(magia['slug'])
        magia['quem_usa'] = dados.get('quem_usa', [])
        magia['tipo'] = dados.get('tipo', 'Geral')
        magias.append(magia)

    return sorted(magias, key=lambda item: item.get('nome', ''))


def wiki_home(request):
    return redirect('wiki_classes_lista')


def regras_lista(request):
    context = {
        'regras': _regras_ordenadas(),
    }
    return render(request, 'wiki/regras_lista.html', context)


def regra_detalhe(request, slug):
    regra = next((item for item in REGRAS if item.get('slug') == slug), None)
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
        'regras_gerais_magia': REGRAS_GERAIS_MAGIA,
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
