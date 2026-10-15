"""Catálogo publicado usado pela wiki e pelas novas solicitações de talentos.

Os identificadores do manual são estáveis. Preços antigos ficam na compra;
ocultar ou remover uma entrada interrompe novas solicitações, sem apagar aquisições.
"""
from .models import WikiEntry
from .constants.classes import CLASSES_WIKI
from .constants.talentos import TALENTOS_WIKI
from .catalog_cache import request_cached


@request_cached
def talent_catalog(include_hidden=False):
    known = {item['slug']: key for key, item in TALENTOS_WIKI.items()}
    entries = WikiEntry.objects.filter(category='talentos')
    if not include_hidden:
        entries = entries.filter(visible=True)
    return {
        entry.data.get('chave') or known.get(entry.slug) or f'WIKI_{entry.pk}':
        {**entry.as_content(), 'entry_id': entry.pk, 'stackavel': bool(entry.data.get('stackavel')),
         'custo_xp': int(entry.data.get('custo_xp', 0)), 'revisao': entry.updated_at.isoformat()}
        for entry in entries
    }


@request_cached
def spells_by_class(include_hidden=False):
    class_ids = {item['nome']: index for index, item in enumerate(CLASSES_WIKI.values(), 1)}
    entries = WikiEntry.objects.filter(category='magias')
    if not include_hidden:
        entries = entries.filter(visible=True)
    result = {}
    for entry in entries:
        for name in entry.data.get('quem_usa', []):
            if name in class_ids:
                result.setdefault(class_ids[name], []).append(entry.name)
    return {key: sorted(set(names)) for key, names in result.items()}


@request_cached
def all_spells(include_hidden=False):
    entries = WikiEntry.objects.filter(category='magias')
    if not include_hidden:
        entries = entries.filter(visible=True)
    return sorted(entries.values_list('name', flat=True))


@request_cached
def class_catalog():
    entries = {entry.data.get('chave'): entry.as_content()
               for entry in WikiEntry.objects.filter(category='classes')}
    return {index: {**item, **entries.get(key, {})}
            for index, (key, item) in enumerate(CLASSES_WIKI.items(), 1)}
