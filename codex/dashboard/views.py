from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, render

from core.models import Profile


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

    return render(request, 'dashboard/home.html', context)


@login_required
@user_passes_test(_is_admin, login_url='home')
def admin_dashboard(request):
    def _redirect_admin_with_filters(q_value, role_value):
        params = {'open_users_modal': '1'}
        if q_value:
            params['q'] = q_value
        if role_value and role_value != 'ALL':
            params['role_filter'] = role_value
        return redirect(f"{reverse('admin_dashboard')}?{urlencode(params)}")

    if request.method == 'POST' and request.POST.get('action') == 'bulk_update_roles':
        allowed_roles = {choice[0] for choice in Profile.UserRole.choices}
        user_ids = request.POST.getlist('user_ids')
        updated_count = 0

        for user_id in user_ids:
            target_user = User.objects.filter(id=user_id).first()
            if not target_user or target_user.is_superuser:
                continue

            new_role = request.POST.get(f'role_{user_id}')
            if new_role not in allowed_roles:
                continue

            profile, _ = Profile.objects.get_or_create(user=target_user)
            if profile.role != new_role:
                profile.role = new_role
                profile.save(update_fields=['role'])

            new_staff_value = new_role == Profile.UserRole.ADMIN
            if target_user.is_staff != new_staff_value:
                target_user.is_staff = new_staff_value
                target_user.save(update_fields=['is_staff'])

            updated_count += 1

        messages.success(request, f'Tipos de usuario atualizados ({updated_count} usuarios).')
        return redirect('admin_dashboard')

    q_value = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role_filter', 'ALL')
    open_users_modal = request.GET.get('open_users_modal') == '1'

    users = User.objects.all().order_by('username')
    if q_value:
        users = users.filter(Q(username__icontains=q_value) | Q(email__icontains=q_value))

    users_with_role = []
    for user in users:
        if hasattr(user, 'profile'):
            role_value = user.profile.role
            role_label = user.profile.get_role_display()
            role_key = role_value
        elif user.is_superuser:
            role_value = Profile.UserRole.ADMIN
            role_label = 'Admin (Superusuario)'
            role_key = 'SUPERUSER'
        else:
            role_value = Profile.UserRole.COMMON
            role_label = 'Usuario comum'
            role_key = Profile.UserRole.COMMON

        if role_filter == 'COMMON' and role_key != Profile.UserRole.COMMON:
            continue
        if role_filter == 'SUPERUSER' and role_key != 'SUPERUSER':
            continue
        if role_filter == 'ADMIN' and role_key not in {Profile.UserRole.ADMIN, 'SUPERUSER'}:
            continue

        users_with_role.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'role_value': role_value,
            'role_label': role_label,
        })

    context = {
        'users_with_role': users_with_role,
        'role_choices': Profile.UserRole.choices,
        'q_value': q_value,
        'role_filter': role_filter,
        'open_users_modal': open_users_modal,
        'filter_role_options': [
            ('ALL', 'Todos os tipos'),
            ('ADMIN', 'Admin'),
            ('COMMON', 'Usuario comum'),
            ('SUPERUSER', 'Superusuario'),
        ],
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def user_dashboard(request):
    return render(request, 'dashboard/user_dashboard.html')
