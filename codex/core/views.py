from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from .forms import AccountPersonalDataForm, RegisterForm
from .models import Profile


def _is_admin(user):
	if not user.is_authenticated:
		return False
	if user.is_superuser:
		return True
	if not hasattr(user, 'profile'):
		return False
	return user.profile.role == Profile.UserRole.ADMIN


def home(request):
	role_label = 'Visitante'
	is_admin = False

	if request.user.is_authenticated:
		if request.user.is_superuser:
			role_label = 'Admin'
			is_admin = True
		else:
			profile, _ = Profile.objects.get_or_create(user=request.user)
			role_label = profile.get_role_display()
			is_admin = profile.role == Profile.UserRole.ADMIN

	context = {
		'role_label': role_label,
		'is_admin': is_admin,
	}

	return render(request, 'core/home.html', context)


def login_view(request):
	if request.user.is_authenticated:
		return redirect('home')

	form = AuthenticationForm(request, data=request.POST or None)
	if request.method == 'POST' and form.is_valid():
		login(request, form.get_user())
		messages.success(request, 'Login realizado com sucesso!')
		return redirect('home')

	return render(request, 'core/login.html', {'form': form})


def register_view(request):
	if request.user.is_authenticated:
		return redirect('home')

	form = RegisterForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		selected_role = form.cleaned_data['role']

		profile = Profile.objects.create(user=user, role=selected_role)
		if profile.role == Profile.UserRole.ADMIN:
			user.is_staff = True
			user.save(update_fields=['is_staff'])

		login(request, user)
		messages.success(request, 'Conta criada com sucesso!')
		return redirect('home')

	return render(request, 'core/register.html', {'form': form})


@login_required
@user_passes_test(_is_admin, login_url='home')
def admin_dashboard(request):
	return render(request, 'core/admin_dashboard.html')


@login_required
def user_dashboard(request):
	return render(request, 'core/user_dashboard.html')


@login_required
def account_personal_data(request):
	form = AccountPersonalDataForm(request.POST or None, instance=request.user)

	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Dados pessoais atualizados com sucesso!')
		return redirect('account_personal_data')

	profile, _ = Profile.objects.get_or_create(user=request.user)
	context = {
		'form': form,
		'profile': profile,
	}
	return render(request, 'core/account_personal_data.html', context)
