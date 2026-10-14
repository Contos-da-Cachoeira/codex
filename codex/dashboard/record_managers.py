"""Shared context for the user, character and event management catalogs."""
from urllib.parse import urlencode

from django.urls import reverse

from core.forms import LarpEventoForm


FILTER_KEYS = ('q', 'role_filter', 'character_q', 'character_status_filter',
               'character_approval_filter', 'larp_q', 'larp_visibility_filter')
MANAGERS = {'users': ('user_roles_modal', 'selected_user'),
            'characters': ('character_modal', 'selected_character'),
            'larps': ('larp_modal', 'selected_larp')}


def record_url(request, kind, selected=None, new=False, clear=False):
    tab, parameter = MANAGERS[kind]
    params = {}
    for key in FILTER_KEYS:
        value = request.POST.get('return_' + key, '') if request.method == 'POST' else request.GET.get(key, '')
        if value and value != 'ALL':
            params[key] = value
    if clear:
        for key in {'users': ('q', 'role_filter'), 'characters': ('character_q', 'character_status_filter', 'character_approval_filter'),
                    'larps': ('larp_q', 'larp_visibility_filter')}[kind]:
            params.pop(key, None)
    if selected:
        params[parameter] = selected
    if new:
        params['new_larp'] = '1'
    query = urlencode(params)
    return reverse('admin_dashboard') + ('?' + query if query else '') + '#' + tab


def _photo(asset=None, fallback=None):
    return {'image_asset': asset, 'image_url': fallback.url if fallback else ''}


def _manager(request, kind, title, description, rows, group_labels, detail_template):
    groups = []
    for key, label in group_labels:
        members = [row for row in rows if row['group_key'] == key]
        if members:
            groups.append({'key': key, 'label': label, 'rows': members, 'cover': members[0]})
    ordered = [row for group in groups for row in group['rows']]
    parameter = MANAGERS[kind][1]
    selected_id = request.GET.get(parameter) or request.POST.get('selected_record')
    selected = next((row for row in ordered if str(row['id']) == selected_id), next(iter(ordered), None))
    for row in rows:
        row['select_url'] = record_url(request, kind, row['id'])
        row['save_url'] = row['select_url']
        row['selected'] = row is selected
    for group in groups:
        group['open'] = bool(selected and selected in group['rows'])
    return {'kind': kind, 'title': title, 'description': description, 'groups': groups, 'rows': rows,
            'selected': selected, 'parameter': parameter, 'tab': MANAGERS[kind][0], 'detail_template': detail_template,
            'clear_url': record_url(request, kind, clear=True), 'count': len(rows)}


def record_managers(request, users, characters, events, event_form=None):
    user_rows = []
    for item in users:
        account = item['account']
        profile = getattr(account, 'profile', None)
        user_rows.append({**item, 'title': account.username,
                          'subtitle': (profile.nome_completo_jogador if profile else '') or account.email or 'Sem e-mail',
                          'group_key': item['role_key'], 'status_label': item['role_label'], 'profile': profile,
                          **_photo(profile.image_asset if profile else None, profile.avatar if profile else None)})
    character_rows = [{**item, 'title': item['nome'], 'subtitle': item['usuario'],
                       'group_key': item['status_aprovacao'], 'status_label': item['classe_display'] or 'Sem classe',
                       **_photo(item['character'].image_asset)} for item in characters]
    event_rows = []
    larp_q = request.GET.get('larp_q', request.POST.get('return_larp_q', '')).strip()
    visibility = request.GET.get('larp_visibility_filter', request.POST.get('return_larp_visibility_filter', 'ALL'))
    for item in events:
        event = item['event']
        if larp_q and larp_q.casefold() not in (event.titulo + ' ' + event.local).casefold():
            continue
        if visibility in {'public', 'private'} and event.visivel_publicamente != (visibility == 'public'):
            continue
        event_rows.append({**item, 'title': event.titulo, 'subtitle': event.local,
                           'group_key': 'public' if event.visivel_publicamente else 'private',
                           'status_label': 'Publicado' if event.visivel_publicamente else 'Oculto',
                           'edit_form': event_form if event_form and event_form.instance.pk == event.pk else LarpEventoForm(instance=event),
                           **_photo(fallback=event.capa)})
    managers = {
        'users_manager': _manager(request, 'users', 'Gerenciar usuários', 'Consulte os dados do jogador e gerencie o tipo da conta.',
                                  user_rows, [('SUPERUSER', 'Superadministradores'), ('ADMIN', 'Administradores'), ('COMMON', 'Usuários comuns')],
                                  'dashboard/includes/user_record.html'),
        'characters_manager': _manager(request, 'characters', 'Gerenciar personagens', 'Consulte a ficha, revise a aprovação e edite os dados do personagem.',
                                       character_rows, [(1, 'Aguardando aprovação'), (2, 'Aprovados'), (3, 'Recusados')],
                                       'dashboard/includes/character_record.html'),
        'larps_manager': _manager(request, 'larps', 'Gerenciar LARPs', 'Crie eventos, edite as informações e controle a publicação.',
                                  event_rows, [('public', 'Publicados'), ('private', 'Ocultos')],
                                  'dashboard/includes/larp_record.html'),
        'record_return_filters': [(key, request.POST.get('return_' + key, '') if request.method == 'POST' else request.GET.get(key, '')) for key in FILTER_KEYS],
        'larp_q_value': larp_q, 'larp_visibility_filter': visibility,
        'new_larp_url': record_url(request, 'larps', new=True),
        'new_larp_form': event_form if event_form and not event_form.instance.pk else LarpEventoForm(),
    }
    larps = managers['larps_manager']
    larps['new'] = request.GET.get('new_larp') == '1' or bool(event_form and not event_form.instance.pk)
    if event_form:
        if event_form.instance.pk:
            larps['selected'] = next((row for row in event_rows if row['id'] == event_form.instance.pk), larps['selected'])
            if larps['selected']:
                larps['selected']['editing'] = True
            for row in larps['rows']:
                row['selected'] = row is larps['selected']
            for group in larps['groups']:
                group['open'] = larps['selected'] in group['rows']
        managers['record_initial_tab'] = 'larp_modal'
    elif request.GET.get('new_larp') == '1' or request.GET.get('selected_larp'):
        managers['record_initial_tab'] = 'larp_modal'
    elif request.GET.get('selected_character'):
        managers['record_initial_tab'] = 'character_modal'
    elif request.GET.get('selected_user'):
        managers['record_initial_tab'] = 'user_roles_modal'
    return managers
