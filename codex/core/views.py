from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

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
    now = timezone.now()
    for evento in eventos:
        evento.inscricao_encerrada = bool(evento.inscricao_ate and now > evento.inscricao_ate)

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
    inscricao_encerrada = bool(evento.inscricao_ate and timezone.now() > evento.inscricao_ate)

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
        'inscricao_encerrada': inscricao_encerrada,
        'total_inscricoes': total_inscricoes,
        'total_pagos': total_pagos,
        'total_pendentes': total_inscricoes - total_pagos,
        'inscricao_usuario': inscricao_usuario,
    }
    return render(request, 'core/detalhe_larp.html', context)


@login_required
def personagens_larp(request, slug):
    evento = get_object_or_404(LarpEvento, slug=slug)

    if not _is_admin(request.user):
        messages.error(request, 'Apenas administradores podem editar a tabela de personagens do LARP.')
        return redirect('detalhe_larp', slug=evento.slug)

    inscricoes = list(
        evento.inscricoes.select_related('usuario', 'personagem').order_by('nome_completo_jogador', 'id')
    )
    tabela_encerrada = bool(inscricoes) and all(inscricao.confirmacao_final for inscricao in inscricoes)

    if request.method == 'POST':
        if tabela_encerrada:
            messages.info(request, 'Esta tabela ja foi encerrada e nao permite mais alteracoes.')
            return redirect('personagens_larp', slug=evento.slug)

        action = request.POST.get('action', 'save_draft')
        atualizados = 0
        encerrados = 0

        for inscricao in inscricoes:
            if inscricao.confirmacao_final:
                continue

            changed_fields = []

            if inscricao.dinheiro_inicio_larp is None:
                inscricao.dinheiro_inicio_larp = inscricao.personagem.ouro
                changed_fields.append('dinheiro_inicio_larp')

            dinheiro_pego_raw = request.POST.get(
                f'dinheiro_pego_larp_{inscricao.id}',
                str(inscricao.dinheiro_pego_larp),
            ).strip()

            dinheiro_final_raw = request.POST.get(
                f'dinheiro_final_larp_{inscricao.id}',
                '' if inscricao.dinheiro_final_larp is None else str(inscricao.dinheiro_final_larp),
            ).strip()
            xp_ganho_raw = request.POST.get(f'xp_ganho_{inscricao.id}', str(inscricao.xp_ganho)).strip()

            try:
                dinheiro_final_novo = int(dinheiro_final_raw)
            except (TypeError, ValueError):
                dinheiro_final_novo = inscricao.dinheiro_final_larp

            try:
                dinheiro_pego_novo = int(dinheiro_pego_raw)
            except (TypeError, ValueError):
                dinheiro_pego_novo = inscricao.dinheiro_pego_larp

            try:
                xp_ganho_novo = int(xp_ganho_raw)
            except (TypeError, ValueError):
                xp_ganho_novo = inscricao.xp_ganho

            if inscricao.dinheiro_final_larp != dinheiro_final_novo:
                inscricao.dinheiro_final_larp = dinheiro_final_novo
                changed_fields.append('dinheiro_final_larp')

            if inscricao.dinheiro_pego_larp != dinheiro_pego_novo:
                inscricao.dinheiro_pego_larp = dinheiro_pego_novo
                changed_fields.append('dinheiro_pego_larp')

            if inscricao.xp_ganho != xp_ganho_novo:
                inscricao.xp_ganho = xp_ganho_novo
                changed_fields.append('xp_ganho')

            morreu_novo = request.POST.get(f'morreu_no_larp_{inscricao.id}') == 'on'
            if inscricao.morreu_no_larp != morreu_novo:
                inscricao.morreu_no_larp = morreu_novo
                changed_fields.append('morreu_no_larp')

            faltou_novo = request.POST.get(f'faltou_no_larp_{inscricao.id}') == 'on'
            if inscricao.faltou_no_larp != faltou_novo:
                inscricao.faltou_no_larp = faltou_novo
                changed_fields.append('faltou_no_larp')

            if action == 'close_table' and not inscricao.confirmacao_final:
                personagem = inscricao.personagem
                if inscricao.dinheiro_inicio_larp is None:
                    inscricao.dinheiro_inicio_larp = personagem.ouro
                    if 'dinheiro_inicio_larp' not in changed_fields:
                        changed_fields.append('dinheiro_inicio_larp')

                dinheiro_final_efetivo = inscricao.dinheiro_final_larp
                if dinheiro_final_efetivo is None:
                    dinheiro_final_efetivo = inscricao.dinheiro_pego_larp

                personagem.ouro = max(
                    0,
                    inscricao.dinheiro_inicio_larp - inscricao.dinheiro_pego_larp + dinheiro_final_efetivo,
                )
                personagem.xp_atual = max(0, personagem.xp_atual + inscricao.xp_ganho)
                personagem.save(update_fields=['ouro', 'xp_atual'])

                inscricao.confirmacao_final = True
                changed_fields.append('confirmacao_final')
                encerrados += 1

            if changed_fields:
                inscricao.save(update_fields=changed_fields)
                atualizados += 1

        if action == 'close_table':
            if encerrados:
                messages.success(request, f'Tabela encerrada. {encerrados} personagem(ns) tiveram ouro e XP aplicados.')
            else:
                messages.info(request, 'Tabela ja estava encerrada ou sem dados novos para aplicar.')
        elif atualizados:
            messages.success(request, 'Esboco da tabela salvo com sucesso.')
        else:
            messages.info(request, 'Nenhuma alteracao foi detectada na tabela.')

        return redirect('personagens_larp', slug=evento.slug)

    context = {
        'evento': evento,
        'inscricoes': inscricoes,
        'is_admin': True,
        'tabela_encerrada': tabela_encerrada,
    }
    return render(request, 'core/personagens_larp.html', context)


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

    if evento.inscricao_ate and timezone.now() > evento.inscricao_ate and not is_admin:
        messages.error(request, 'O prazo de inscricao deste LARP foi encerrado.')
        return redirect('detalhe_larp', slug=evento.slug)

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
