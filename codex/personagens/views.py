from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from core.constants.guildas import GUILDAS
from .consts import MAGIAS_POR_CLASSE
from .consts import CLASSES_CHOICES, GUILDAS_CHOICES
from .forms import PersonagemCreateForm, PersonagemUpdateForm
from .models import Personagem


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
				'nome': GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guilda_id]].get('nome', label),
				'imagem': GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guilda_id]].get('imagem', ''),
				'lema': GUILDAS[GUILDA_PUBLIC_KEY_BY_ID[guilda_id]].get('lema'),
				'slug': GUILDA_SLUG_BY_ID[guilda_id],
			}
			for guilda_id, label in GUILDAS_CHOICES
		],
		'classes_personagem': [
			{
				'value': classe_id,
				'nome': label,
				'imagem': CLASSE_IMAGEM_BY_ID[classe_id],
			}
			for classe_id, label in CLASSES_CHOICES
		],
		'magias_por_classe': {str(classe_id): magias for classe_id, magias in MAGIAS_POR_CLASSE.items()},
		'magias_selecionadas': form['magias_pretendidas'].value() or [],
	}
	return render(request, 'personagens/criar_personagem.html', context)


@login_required
def detalhe_personagem(request, slug):
	personagem = get_object_or_404(Personagem, slug=slug, usuario=request.user)
	return render(request, 'personagens/detalhe_personagem.html', {'personagem': personagem})


@login_required
def editar_personagem(request, slug):
	personagem = get_object_or_404(Personagem, slug=slug, usuario=request.user)
	form = PersonagemUpdateForm(request.POST or None, instance=personagem)

	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Personagem atualizado com sucesso!')
		return redirect('detalhe_personagem', slug=personagem.slug)

	context = {
		'form': form,
		'selected_image': _selected_image(form),
		'personagem': personagem,
	}
	return render(request, 'personagens/editar_personagem.html', context)
