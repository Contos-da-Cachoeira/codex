from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError, PermissionDenied
from django.views.decorators.http import require_http_methods
from django.db import transaction

from core.constants.guildas import GUILDAS
from .consts import MAGIAS_POR_CLASSE
from .consts import CLASSES_CHOICES, GUILDAS_CHOICES
from .forms import PersonagemCreateForm, PersonagemUpdateForm, CompraTalentoForm, MulticlassReviewForm
from .models import Personagem, CompraTalento
from .rules import CLASS_DATA, FOCI, ALL_SPELLS, ANCIENT_SPELLS, approve_purchase, activate_purchases, complete_multiclass
from core.models import Profile
from wiki.constants.talentos import TALENTOS_WIKI
from wiki.catalog import talent_catalog, spells_by_class, all_spells, class_catalog
from .identity import DIVINITIES
from django.templatetags.static import static


GUILDA_PUBLIC_KEY_BY_ID = {
	1: 'ARTISTAS_DA_REVOLUCAO',
	2: 'CIRCULO_DO_FOGO',
	3: 'FLORESTA_DO_SOL',
	4: 'IRMANDADE_DAS_TAVERNAS',
	5: 'RASGA_MORTALHAS',
	6: 'SOCIEDADE_ZAORI',
	7: 'MERCENARIOS_INDEPENDENTES',
}

GUILDA_SLUG_BY_ID = {
	1: 'artistas-da-revolucao',
	2: 'circulo-do-fogo',
	3: 'floresta-do-sol',
	4: 'irmandade-das-tavernas',
	5: 'os-rasga-mortalhas',
	6: 'sociedade-zaori',
	7: 'mercenarios-independentes',
}

CLASSE_IMAGEM_BY_ID = {
	1: 'core/img/classes/Barbaro-ink.png',
	2: 'core/img/classes/Bardo-ink.png',
	3: 'core/img/classes/Cacador-ink.png',
	4: 'core/img/classes/Clerigo-ink.png',
	5: 'core/img/classes/Druida-ink.png',
	6: 'core/img/classes/Guerreiro-ink.png',
	7: 'core/img/classes/Ladino-ink.png',
	8: 'core/img/classes/Mago-ink.png',
	9: 'core/img/classes/Paladino-ink.png',
}


def _selected_image(form):
	value = form['image_asset'].value()
	if str(value).isdigit():
		return form.fields['image_asset'].queryset.filter(pk=value).first()
	return None


@login_required
def meus_personagens(request):
	personagens = Personagem.objects.select_related('image_asset').filter(usuario=request.user).order_by('-data_criacao')
	context = {'personagens': personagens}
	return render(request, 'personagens/meus_personagens.html', context)


@login_required
def criar_personagem(request):
	popup_mode = request.GET.get('popup') == '1'
	form = PersonagemCreateForm(request.POST or None, user=request.user)

	if request.method == 'POST' and form.is_valid():
		personagem = form.save()

		messages.success(request, 'Personagem criado com sucesso!')
		if form.pending_talents:
			messages.info(request, 'As solicitações de talentos foram enviadas à comissão. O XP será descontado após aprovação.')
		if popup_mode:
			return redirect(f"{request.path}?popup=1&created={personagem.id}")
		return redirect('meus_personagens')

	context = {
		'form': form,
		'selected_image': _selected_image(form),
		'popup_mode': popup_mode,
		'created_in_popup': request.GET.get('created', ''),
		'guildas_personagem': [
			{
				'value': guilda_id,
				**GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guilda_id]],
				'nome': GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guilda_id]].get('nome', label),
				'slug': GUILDA_SLUG_BY_ID[guilda_id],
			}
			for guilda_id, label in GUILDAS_CHOICES
		],
		'classes_personagem': [
			{
				'value': classe_id,
				'nome': label,
				'image_url': class_catalog()[classe_id].get('image_url') or static(class_catalog()[classe_id].get('imagem', CLASSE_IMAGEM_BY_ID[classe_id])),
			}
			for classe_id, label in CLASSES_CHOICES
		],
        'magias_por_classe': {str(classe_id): magias for classe_id, magias in spells_by_class().items()},
		'magias_selecionadas': form['magias_pretendidas'].value() or [],
        'class_rules': {str(k): {**v, 'foco': v.get('foco') or FOCI.get(k, 'Não conjura naturalmente.')} for k, v in class_catalog().items()},
        'talent_catalog': [{**talent, 'key': key} for key, talent in talent_catalog().items()],
        'talent_spell_choices': all_spells(),
        'divinities': DIVINITIES,
		'ancient_spell_choices': list(ANCIENT_SPELLS),
		'player_xp': getattr(getattr(request.user, 'profile', None), 'xp_disponivel', 0),
	}
	return render(request, 'personagens/criar_personagem.html', context)


@login_required
def detalhe_personagem(request, slug):
	personagem = _character_for_user(request, slug)
	return render(request, 'personagens/detalhe_personagem.html', {'personagem': personagem})


@login_required
def editar_personagem(request, slug):
	personagem = _character_for_user(request, slug)
	form = PersonagemUpdateForm(request.POST or None, instance=personagem, admin=_is_admin(request.user))

	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Personagem atualizado com sucesso!')
		return redirect('detalhe_personagem', slug=personagem.slug)

	context = {
		'form': form,
		'selected_image': _selected_image(form),
		'personagem': personagem,
	}
	return render(request, 'personagens/editar_personagem_manual.html', context)


def _is_admin(user):
	return user.is_active and (user.is_staff or user.is_superuser or getattr(getattr(user, 'profile', None), 'role', '') == 'ADMIN')


def _character_for_user(request, slug):
	queryset = Personagem.objects.select_related('usuario__profile', 'image_asset')
	if not _is_admin(request.user):
		queryset = queryset.filter(usuario=request.user)
	return get_object_or_404(queryset, slug=slug)


@login_required
@require_http_methods(['GET', 'POST'])
def talentos_personagem(request, slug):
	character = _character_for_user(request, slug)
	Profile.objects.get_or_create(user=character.usuario)
	admin = _is_admin(request.user)
	action = request.POST.get('action')
	form = CompraTalentoForm(request.POST if action == 'request' else None, character=character)
	if request.method == 'POST':
		try:
			if action == 'request':
				if form.is_valid():
					form.save()
					messages.success(request, 'Solicitação registrada. O XP será descontado uma única vez após aprovação da comissão. Depois, escolha quais compras ativar.')
					return redirect('talentos_personagem', slug=slug)
			elif action == 'activate':
				activate_purchases(character.pk, request.POST.getlist('active'))
				messages.success(request, 'Talentos ativos atualizados.')
				return redirect('talentos_personagem', slug=slug)
			elif action == 'complete_choices':
				if not admin:
					raise PermissionDenied
				purchase = get_object_or_404(CompraTalento, pk=request.POST.get('purchase'), personagem=character)
				review = MulticlassReviewForm(request.POST, purchase=purchase)
				if review.is_valid():
					complete_multiclass(purchase.pk, request.user, review.cleaned_data)
					messages.success(request, 'Escolhas antigas completadas pela comissão. Nenhum XP adicional foi cobrado.')
					return redirect('talentos_personagem', slug=slug)
			elif action in {'approve', 'reject'}:
				if not admin:
					raise PermissionDenied
				purchase = get_object_or_404(CompraTalento, pk=request.POST.get('purchase'), personagem=character)
				if action == 'approve':
					approve_purchase(purchase.pk, request.user, commission_details=request.POST.get('commission_details'))
				else:
					with transaction.atomic():
						purchase = CompraTalento.objects.select_for_update().get(pk=purchase.pk)
						if purchase.status != 'pending':
							raise ValidationError('Esta solicitação já foi analisada.')
						purchase.status = 'rejected'
						purchase.aprovado_por = request.user
						purchase.save(update_fields=['status', 'aprovado_por'])
				messages.success(request, 'Solicitação analisada.')
				return redirect('talentos_personagem', slug=slug)
		except (ValidationError, ValueError) as error:
			messages.error(request, '; '.join(error.messages) if isinstance(error, ValidationError) else 'Seleção inválida.')
	return render(request, 'personagens/talentos.html', {
		'personagem': character, 'form': form, 'is_admin': admin,
        'purchases': character.compras_talentos.all().order_by('pk'), 'catalog': talent_catalog(),
		'choice_reviews': [{'purchase': purchase, 'form': MulticlassReviewForm(request.POST if action == 'complete_choices' and str(purchase.pk) == request.POST.get('purchase') else None, purchase=purchase)}
			for purchase in character.compras_talentos.all() if purchase.precisa_completar_escolhas] if admin else [],
	})
