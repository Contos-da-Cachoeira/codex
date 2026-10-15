from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .forms import ImageAssetForm


@require_POST
def upload_image(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Sua sessão expirou. Entre novamente.'}, status=401)
    form = ImageAssetForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': ' '.join(str(e) for errors in form.errors.values() for e in errors)}, status=400)
    asset = form.save(commit=False)
    asset.owner = request.user
    asset.save()
    return JsonResponse({'id': asset.pk, 'source': asset.source, 'x': asset.x, 'y': asset.y, 'zoom': asset.zoom, 'ratio': asset.ratio})

from personagens.forms import LarpInscricaoEventoForm

from .models import LarpEvento, LarpInscricao, Profile
from .forms import LarpEventoForm
from .event_management import EDITABLE, participant_rows, event_metrics, save_participants


def _is_admin(user):
    if not user.is_authenticated or not getattr(user, 'is_active', True):
        return False
    if user.is_superuser or user.is_staff:
        return True
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role == Profile.UserRole.ADMIN


def listar_larps(request):
    eventos = LarpEvento.objects.annotate(inscricoes_total=Count('inscricoes')).order_by('-data_evento')
    if not _is_admin(request.user):
        eventos = eventos.filter(visivel_publicamente=True)

    eventos = list(eventos)

    inscricoes_do_usuario = set()
    if request.user.is_authenticated:
        inscricoes_usuario = list(
            LarpInscricao.objects.select_related('personagem')
            .filter(usuario=request.user, evento__in=eventos)
        )
        inscricoes_do_usuario = {inscricao.evento_id for inscricao in inscricoes_usuario}
        personagens_por_evento = {
            inscricao.evento_id: inscricao.personagem.nome
            for inscricao in inscricoes_usuario
        }

        for evento in eventos:
            evento.personagem_inscrito_usuario = personagens_por_evento.get(evento.id, '')

    context = {
        'eventos': eventos,
        'is_admin': _is_admin(request.user),
        'inscricoes_do_usuario': inscricoes_do_usuario,
    }
    return render(request, 'core/listar_larps.html', context)


def detalhe_larp(request, slug):
    evento = get_object_or_404(LarpEvento, slug=slug)
    is_admin = _is_admin(request.user)

    if not evento.visivel_publicamente and not is_admin:
        messages.error(request, 'Este LARP nao esta visivel no momento.')
        return redirect('listar_larps')

    inscricoes = None
    total_inscricoes = 0
    total_pagos = 0
    total_alertas = 0
    event_form = None

    if is_admin:
        event_form = LarpEventoForm(instance=evento)
        if request.method == 'POST' and request.POST.get('action') == 'delete_event':
            evento.delete()
            messages.success(request, 'Evento e inscrições excluídos.')
            return redirect(f"{reverse('admin_dashboard')}#larp_modal")
        inscricoes = evento.inscricoes.select_related('usuario__profile__image_asset', 'personagem__image_asset').order_by('nome_completo_jogador', 'id')

        if request.method == 'POST' and request.POST.get('action') == 'edit_event':
            event_form = LarpEventoForm(request.POST, request.FILES, instance=evento)
            if event_form.is_valid():
                event_form.save()
                if request.headers.get('X-Event-Management') == '1':
                    return JsonResponse({'ok': True, 'message': 'Informações do evento salvas.',
                        'title': evento.titulo,
                        'summary': render_to_string('core/includes/event_summary.html', {'evento': evento}, request=request),
                        'editor': render_to_string('core/includes/event_editor.html', {'evento': evento, 'event_form': LarpEventoForm(instance=evento)}, request=request)})
                messages.success(request, 'Informações do evento atualizadas.')
                return redirect('detalhe_larp', slug=evento.slug)
            if request.headers.get('X-Event-Management') == '1':
                return JsonResponse({'ok': False, 'message': 'Confira os campos indicados.',
                    'errors': {name: list(errors) for name, errors in event_form.errors.items()}}, status=422)

        if request.method == 'POST' and request.POST.get('action') == 'update_payments':
            atualizadas = 0
            for inscricao in inscricoes:
                taxa_paga_nova = request.POST.get(f'taxa_paga_{inscricao.id}') == 'on'
                if inscricao.taxa_paga != taxa_paga_nova:
                    inscricao.taxa_paga = taxa_paga_nova
                    inscricao.save(update_fields=['taxa_paga'])
                    atualizadas += 1

            if atualizadas:
                messages.success(request, 'Checklist de pagamento atualizado com sucesso.')
            else:
                messages.info(request, 'Nenhuma alteracao de pagamento foi feita.')
            return redirect('detalhe_larp', slug=evento.slug)

        total_inscricoes = inscricoes.count()
        total_pagos = inscricoes.filter(taxa_paga=True).count()
        total_alertas = sum(bool(item.fobia_gatilho.strip()) for item in inscricoes)
    elif request.method == 'POST':
        if request.headers.get('X-Event-Management') == '1':
            return JsonResponse({'ok': False, 'message': 'Apenas administradores podem gerenciar eventos.'}, status=403)
        messages.error(request, 'Apenas administradores podem atualizar o checklist de pagamento.')
        return redirect('detalhe_larp', slug=evento.slug)

    inscricao_usuario = None
    if request.user.is_authenticated:
        inscricao_usuario = (
            LarpInscricao.objects.select_related('personagem')
            .filter(evento=evento, usuario=request.user)
            .first()
        )

    context = {
        'evento': evento,
        'inscricoes': inscricoes,
        'is_admin': is_admin,
        'total_inscricoes': total_inscricoes,
        'total_pagos': total_pagos,
        'total_alertas': total_alertas,
        'event_form': event_form,
        'total_pendentes': total_inscricoes - total_pagos,
        'inscricao_usuario': inscricao_usuario,
    }
    if is_admin:
        context.update(metrics=event_metrics(list(inscricoes)), event_page='overview',
            signup_url=request.build_absolute_uri(reverse('inscricao_larp', args=[evento.slug, evento.inscricao_token])))
        return render(request, 'core/gerenciar_larp.html', context)
    return render(request, 'core/detalhe_larp.html', context)


@login_required
def inscricao_larp(request, slug, token):
    evento = get_object_or_404(LarpEvento, slug=slug, inscricao_token=token)
    is_admin = _is_admin(request.user)

    if is_admin:
        messages.error(request, 'Administradores nao podem se inscrever em LARP.')
        return redirect('detalhe_larp', slug=evento.slug)

    if not evento.visivel_publicamente and not is_admin:
        messages.error(request, 'Este LARP nao esta visivel para inscricoes no momento.')
        return redirect('listar_larps')

    inscricao_existente = LarpInscricao.objects.filter(evento=evento, usuario=request.user).first()

    if inscricao_existente:
        messages.info(request, 'Voce ja esta inscrito neste LARP.')
        return redirect('listar_larps')

    if not evento.inscricoes_abertas:
        messages.error(request, 'As inscrições para este LARP estão encerradas.')
        return redirect('detalhe_larp', slug=evento.slug)

    form = LarpInscricaoEventoForm(request.POST or None, user=request.user, evento=evento)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Inscricao no LARP realizada com sucesso!')
        return redirect('listar_larps')

    context = {
        'evento': evento,
        'form': form,
        'player_data_status': form.player_data_status,
        'is_admin': is_admin,
    }
    return render(request, 'core/inscricao_larp.html', context)


@login_required
def planilha_larp(request, slug):
    ajax = request.headers.get('X-Event-Management') == '1'
    if not _is_admin(request.user):
        if ajax:
            return JsonResponse({'ok': False, 'message': 'Apenas administradores podem gerenciar participantes.'}, status=403)
        return redirect('home')
    evento = get_object_or_404(LarpEvento, slug=slug)
    inscricoes = list(evento.inscricoes.select_related('usuario__profile__image_asset', 'personagem__image_asset').order_by('nome_completo_jogador', 'id'))
    editing_balances = request.method == 'POST' and request.POST.get('action') == 'update_balances'
    selected, changes = inscricoes, None
    if editing_balances and ajax:
        try:
            ids = {int(value) for value in request.POST.getlist('registration_ids')}
            known = {item.pk for item in inscricoes}
            if not ids or not ids <= known:
                raise ValueError
            selected = [item for item in inscricoes if item.pk in ids]
            changes = {item.pk: request.POST.getlist(f'changed_fields_{item.pk}') for item in selected}
            if any(not fields or not set(fields) <= set(EDITABLE) for fields in changes.values()):
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({'ok': False, 'message': 'Seleção de participantes inválida. Atualize a tela e tente novamente.'}, status=400)
    balance_rows = participant_rows(selected, request.POST if editing_balances else None)
    if editing_balances:
        valid = [row['form'].is_valid() for row in balance_rows]
        if all(valid):
            try:
                saved = save_participants(evento, balance_rows, request.user, changes=changes, include_payments=request.POST.get('include_payments') == '1')
            except ValidationError as error:
                if ajax:
                    conflicts = getattr(error, 'ids', [])
                    current = participant_rows(list(evento.inscricoes.select_related('usuario__profile', 'personagem').filter(pk__in=conflicts)))
                    return JsonResponse({'ok': False, 'message': '; '.join(error.messages), 'conflicts': [
                        {'id': row['registration'].pk, **row['form'].initial} for row in current]}, status=409)
                messages.error(request, '; '.join(error.messages))
            else:
                if ajax:
                    metrics = event_metrics(list(evento.inscricoes.all()))
                    return JsonResponse({'ok': True, 'message': 'Alterações salvas.', 'rows': saved, 'metrics': metrics})
                messages.success(request, 'XP e ouro dos participantes atualizados.')
                return redirect('planilha_larp', slug=evento.slug)
        if ajax:
            return JsonResponse({'ok': False, 'message': 'Confira os valores indicados. Nenhuma alteração foi salva.',
                'errors': {row['registration'].pk: {name: list(errors) for name, errors in row['form'].errors.items()} for row in balance_rows if row['form'].errors}}, status=422)
        messages.error(request, 'Confira os valores da planilha. Nenhum saldo foi alterado.')

    guilds = sorted({(item.personagem.guilda or 0, item.personagem.get_guilda_display() or 'Sem guilda') for item in inscricoes}, key=lambda item: item[1])
    return render(request, 'core/planilha_larp.html', {'evento': evento, 'balance_rows': balance_rows,
        'metrics': event_metrics(inscricoes), 'guild_filters': guilds, 'event_page': 'participants'})
