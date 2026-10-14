from django.contrib.messages import get_messages
from django.http import JsonResponse
from django.template.loader import render_to_string


PANELS = {
    'user_roles_modal': ('dashboard/includes/records_panel.html', 'users_manager'),
    'character_modal': ('dashboard/includes/records_panel.html', 'characters_manager'),
    'larp_modal': ('dashboard/includes/records_panel.html', 'larps_manager'),
    'wiki_panel': ('wiki/admin_panel.html', None),
    'theme_modal': ('dashboard/includes/theme_panel.html', None),
    'social_modal': ('dashboard/includes/social_panel.html', None),
}


def panel_response(request, context):
    panel = request.headers.get('X-Admin-Panel')
    if panel not in PANELS:
        return None
    template, manager_key = PANELS[panel]
    panel_context = dict(context)
    state = {}
    invalid = False
    if manager_key:
        manager = context[manager_key]
        panel_context['manager'] = manager
        state = {'kind': manager['kind'], 'selected': 'new' if manager.get('new') else str(manager['selected']['id']) if manager['selected'] else 'empty'}
        if panel == 'larp_modal':
            form = context['new_larp_form'] if manager.get('new') else manager['selected']['edit_form'] if manager['selected'] else None
            invalid = bool(form and form.is_bound and form.errors)
    elif panel == 'wiki_panel':
        entry = context.get('wiki_entry') or context.get('wiki_selected')
        state = {'mode': context.get('wiki_mode', ''), 'selected': str(entry.pk) if entry and entry.pk else '',
                 'category': entry.category if entry else ''}
        form = context.get('wiki_form')
        invalid = bool(form and form.is_bound and form.errors)
    payload = {'panel': panel, 'html': render_to_string(template, panel_context, request=request),
               'state': state, 'invalid': invalid,
               'messages': [{'text': str(message), 'tags': message.tags} for message in get_messages(request)]}
    if panel == 'theme_modal':
        layout = context['layout_config']
        payload['theme'] = {field.name: getattr(layout, field.name) for field in layout._meta.fields if field.name.endswith('_color')}
    response = JsonResponse(payload)
    response['X-Admin-Panel'] = panel
    response['Cache-Control'] = 'no-store'
    return response
