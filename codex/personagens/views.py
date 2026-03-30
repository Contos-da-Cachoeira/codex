from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .consts import MAGIAS_POR_CLASSE
from .forms import PersonagemCreateForm, PersonagemUpdateForm
from .models import Personagem


@login_required
def meus_personagens(request):
	personagens = Personagem.objects.filter(usuario=request.user).order_by('-data_criacao')
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
		'popup_mode': popup_mode,
		'created_in_popup': request.GET.get('created', ''),
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
		'personagem': personagem,
	}
	return render(request, 'personagens/editar_personagem.html', context)
