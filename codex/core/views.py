from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from personagens.forms import LarpInscricaoEventoForm

from .models import LarpEvento, LarpInscricao, Profile


def _is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
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

    if is_admin:
        inscricoes = evento.inscricoes.select_related('usuario', 'personagem').order_by('nome_completo_jogador', 'id')

        if request.method == 'POST':
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
    elif request.method == 'POST':
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
        'total_pendentes': total_inscricoes - total_pagos,
        'inscricao_usuario': inscricao_usuario,
    }
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
