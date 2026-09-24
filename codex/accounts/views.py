from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from core.models import Profile

from .forms import AccountPersonalDataForm, RegisterForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, 'Login realizado com sucesso!')
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('home')

    return render(
        request,
        'accounts/login.html',
        {'form': form, 'next': request.GET.get('next', '')},
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        Profile.objects.create(user=user)

        login(request, user)
        messages.success(request, 'Conta criada com sucesso!')
        return redirect('home')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def account_personal_data(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = AccountPersonalDataForm(request.POST or None, request.FILES or None, instance=request.user, profile=profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Dados pessoais atualizados com sucesso!')
        return redirect('account_personal_data')

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/account_personal_data.html', context)
