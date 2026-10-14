"""Wiki management embedded in the existing, admin-protected dashboard."""
from urllib.parse import urlencode

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.templatetags.static import static

from .forms import FIELDS, LABELS, WikiEntryForm
from .models import WikiEntry


def panel_url(**params):
    query = urlencode({key: value for key, value in params.items() if value})
    return reverse('admin_dashboard') + ('?' + query if query else '') + '#wiki_panel'


def _entry(pk):
    try:
        pk = int(pk)
    except (ValueError, TypeError):
        raise Http404('Conteúdo não encontrado.')
    return get_object_or_404(WikiEntry, pk=pk)


def _image_url(entry):
    if entry.image:
        return entry.image.url
    return static(entry.data['imagem']) if entry.data.get('imagem') else ''


def _information(entry):
    fields = []
    keys = FIELDS[entry.category].split()
    keys = [key for key in keys if key in {'descricao', 'resumo'}] + [key for key in keys if key not in {'descricao', 'resumo'}]
    for key in keys:
        value = entry.data.get(key)
        if value is None or value == '' or value == []:
            continue
        kind = 'sections' if key == 'secoes' else 'list' if isinstance(value, list) else 'text'
        if isinstance(value, bool):
            value = 'Sim' if value else 'Não'
        fields.append({'label': LABELS.get(key, key.replace('_', ' ').capitalize()),
                       'value': value, 'kind': kind, 'wide': key in {'descricao', 'resumo', 'secoes', 'habilidade_detalhes', 'itens', 'extra'}})
    return fields


def wiki_panel(request):
    """Return panel context, or a redirect after a successful POST."""
    params = request.POST if request.method == 'POST' and request.POST.get('action', '').startswith('wiki_') else request.GET
    query = params.get('wiki_q', '').strip()
    section = params.get('wiki_section', '')
    filters = {'wiki_q': query, 'wiki_section': section}
    list_url = panel_url(**filters)
    context = {
        'wiki_categories': WikiEntry.CATEGORIES,
        'wiki_q': query, 'wiki_section': section, 'wiki_list_url': list_url,
        'wiki_create_url': panel_url(wiki_action='new', **filters),
        'wiki_creation_sections': [
            (key, label, panel_url(wiki_action='new', wiki_category=key, **filters))
            for key, label in WikiEntry.CATEGORIES if key != 'magia_geral'
        ],
    }
    mode = request.GET.get('wiki_action', '')
    entry = None
    form = None
    if request.method == 'POST' and params.get('action') in {'wiki_save', 'wiki_visibility', 'wiki_delete'}:
        action = params['action']
        entry = _entry(params.get('wiki_id')) if params.get('wiki_id') else WikiEntry()
        if action in {'wiki_visibility', 'wiki_delete'}:
            if not entry.pk:
                raise Http404('Conteúdo não encontrado.')
            if action == 'wiki_delete':
                entry.delete()
                messages.success(request, 'Conteúdo excluído da wiki.')
            else:
                entry.visible = not entry.visible
                entry.save(update_fields=['visible', 'updated_at'])
                messages.success(request, 'Visibilidade atualizada.')
            return redirect(list_url if action == 'wiki_delete' else panel_url(wiki_selected=entry.pk, **filters))
        mode = 'edit' if entry.pk else 'new'
        category = entry.category or params.get('wiki_category', '')
        if category not in dict(WikiEntry.CATEGORIES):
            raise Http404('Seção inválida.')
        form = WikiEntryForm(request.POST, request.FILES, instance=entry, category=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conteúdo da wiki salvo.')
            return redirect(panel_url(wiki_selected=entry.pk, **filters))
    elif mode in {'edit', 'delete'}:
        entry = _entry(request.GET.get('wiki_id'))
    elif mode == 'new':
        entry = WikiEntry(category=request.GET.get('wiki_category', ''))
    elif mode:
        raise Http404('Ação inválida.')

    entries = WikiEntry.objects.all()
    if section:
        entries = entries.filter(category=section)
    if query:
        entries = entries.filter(name__icontains=query)
    entries = list(entries)
    selected = entry if mode else (_entry(params['wiki_selected']) if params.get('wiki_selected') else next(iter(entries), None))
    rows = [
        {'entry': item, 'image_url': _image_url(item),
         'information': _information(item),
         'edit_url': panel_url(wiki_action='edit', wiki_id=item.pk, **filters),
         'delete_url': panel_url(wiki_action='delete', wiki_id=item.pk, **filters),
         'selected': bool(selected and item.pk == selected.pk),
         'select_url': panel_url(wiki_selected=item.pk, **filters)} for item in entries
    ]
    groups = []
    for key, label in WikiEntry.CATEGORIES:
        group_rows = [row for row in rows if row['entry'].category == key]
        if group_rows:
            groups.append({'label': label, 'key': key, 'rows': group_rows,
                           'image_url': next((row['image_url'] for row in group_rows if row['image_url']), ''),
                           'open': bool(section or (selected and selected.category == key))})
    context.update(wiki_rows=rows, wiki_groups=groups, wiki_count=len(rows), wiki_selected=selected,
                   wiki_back_url=panel_url(wiki_selected=selected.pk, **filters) if selected and selected.pk else list_url)
    if selected and selected.pk:
        context.update(wiki_image_url=_image_url(selected), wiki_information=_information(selected),
                       wiki_edit_url=panel_url(wiki_action='edit', wiki_id=selected.pk, **filters),
                       wiki_delete_url=panel_url(wiki_action='delete', wiki_id=selected.pk, **filters))

    if mode in {'edit', 'new'} and not (mode == 'new' and not entry.category):
        if entry.category not in dict(WikiEntry.CATEGORIES):
            raise Http404('Seção inválida.')
        if form is None:
            form = WikiEntryForm(instance=entry, category=entry.category)
        context.update(wiki_form=form, wiki_content=entry.as_content(),
                       wiki_category_name=dict(WikiEntry.CATEGORIES)[entry.category])
    if mode:
        context.update(wiki_mode=mode, wiki_entry=entry, wiki_active=True)
    else:
        context['wiki_active'] = bool(query or section or params.get('wiki_selected') or params.get('action', '').startswith('wiki_'))
    return context
