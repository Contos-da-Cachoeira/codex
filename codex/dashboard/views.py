from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, render

from core.models import HomePageConfig, Profile, SiteLayoutConfig
from personagens.consts import (
    CLASSES_CHOICES,
    GUILDAS_CHOICES,
    STATUS_APROVACAO,
    STATUS_APROVACAO_CHOICES,
    STATUS_PERSONAGEM_CHOICES,
)
from personagens.models import Personagem


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
    home_config = HomePageConfig.load()
    layout_config = SiteLayoutConfig.load()

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
        'home_config': home_config,
        'layout_config': layout_config,
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

    home_config = HomePageConfig.load()
    layout_config = SiteLayoutConfig.load()

    if request.method == 'POST' and request.POST.get('action') == 'update_home_components':
        home_config.banner_visible = request.POST.get('banner_visible') == 'on'
        home_config.banner_badge_text = request.POST.get('banner_badge_text', '').strip()
        home_config.banner_title = request.POST.get('banner_title', '').strip()
        home_config.banner_subtitle = request.POST.get('banner_subtitle', '').strip()

        if request.POST.get('remove_banner_image') == 'on':
            if home_config.banner_image:
                home_config.banner_image.delete(save=False)
            home_config.banner_image = None
        elif request.FILES.get('banner_image'):
            home_config.banner_image = request.FILES['banner_image']

        home_config.menu_section_visible = request.POST.get('menu_section_visible') == 'on'
        home_config.menu_section_title = request.POST.get('menu_section_title', '').strip()

        home_config.text_section_visible = request.POST.get('text_section_visible') == 'on'
        home_config.text_section_title = request.POST.get('text_section_title', '').strip()
        home_config.text_section_content = request.POST.get('text_section_content', '').strip()
        home_config.save()

        layout_config.header_visible = request.POST.get('header_visible') == 'on'
        layout_config.header_title = request.POST.get('header_title', '').strip()
        layout_config.footer_visible = request.POST.get('footer_visible') == 'on'
        layout_config.footer_title = request.POST.get('footer_title', '').strip()
        layout_config.footer_description = request.POST.get('footer_description', '').strip()
        layout_config.footer_copyright = request.POST.get('footer_copyright', '').strip()
        layout_config.save()

        messages.success(request, 'Componentes da Home atualizados com sucesso.')
        return redirect(f"{reverse('admin_dashboard')}?open_home_components_modal=1")

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

        messages.success(request, 'Tipos de usuario atualizados.')
        return redirect('admin_dashboard')

    if request.method == 'POST' and request.POST.get('action') == 'bulk_update_personagens':
        allowed_status = {choice[0] for choice in STATUS_PERSONAGEM_CHOICES}
        allowed_aprovacao = {choice[0] for choice in STATUS_APROVACAO_CHOICES}
        allowed_classes = {choice[0] for choice in CLASSES_CHOICES}
        allowed_guildas = {choice[0] for choice in GUILDAS_CHOICES}
        personagem_ids = request.POST.getlist('personagem_ids')
        updated_count = 0

        for personagem_id in personagem_ids:
            personagem = Personagem.objects.filter(id=personagem_id).first()
            if not personagem:
                continue

            changed_fields = []

            status_raw = request.POST.get(f'status_{personagem_id}', str(personagem.status)).strip()
            try:
                new_status = int(status_raw)
            except (TypeError, ValueError):
                new_status = personagem.status

            if new_status in allowed_status and personagem.status != new_status:
                personagem.status = new_status
                changed_fields.append('status')

            classe_raw = request.POST.get(f'classe_{personagem_id}', '').strip()
            new_classe = None
            if classe_raw:
                try:
                    classe_candidate = int(classe_raw)
                    if classe_candidate in allowed_classes:
                        new_classe = classe_candidate
                except (TypeError, ValueError):
                    new_classe = personagem.classe

            if personagem.classe != new_classe:
                personagem.classe = new_classe
                changed_fields.append('classe')

            guilda_raw = request.POST.get(f'guilda_{personagem_id}', '').strip()
            new_guilda = None
            if guilda_raw:
                try:
                    guilda_candidate = int(guilda_raw)
                    if guilda_candidate in allowed_guildas:
                        new_guilda = guilda_candidate
                except (TypeError, ValueError):
                    new_guilda = personagem.guilda

            if personagem.guilda != new_guilda:
                personagem.guilda = new_guilda
                changed_fields.append('guilda')

            aprovacao_raw = request.POST.get(
                f'status_aprovacao_{personagem_id}',
                str(personagem.status_aprovacao),
            ).strip()
            try:
                new_status_aprovacao = int(aprovacao_raw)
            except (TypeError, ValueError):
                new_status_aprovacao = personagem.status_aprovacao

            if (
                new_status_aprovacao in allowed_aprovacao
                and personagem.status_aprovacao != new_status_aprovacao
            ):
                personagem.status_aprovacao = new_status_aprovacao
                changed_fields.append('status_aprovacao')

            xp_raw = request.POST.get(f'xp_atual_{personagem_id}', str(personagem.xp_atual)).strip()
            ouro_raw = request.POST.get(f'ouro_{personagem_id}', str(personagem.ouro)).strip()

            try:
                new_xp = max(0, int(xp_raw))
            except (TypeError, ValueError):
                new_xp = personagem.xp_atual

            try:
                new_ouro = max(0, int(ouro_raw))
            except (TypeError, ValueError):
                new_ouro = personagem.ouro

            if personagem.xp_atual != new_xp:
                personagem.xp_atual = new_xp
                changed_fields.append('xp_atual')

            if personagem.ouro != new_ouro:
                personagem.ouro = new_ouro
                changed_fields.append('ouro')

            if changed_fields:
                changed_fields.append('data_atualizacao')
                personagem.save(update_fields=changed_fields)
                updated_count += 1

        messages.success(request, 'Personagens atualizados.')
        return redirect(f"{reverse('admin_dashboard')}?open_personagens_modal=1")

    q_value = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role_filter', 'ALL')
    open_users_modal = request.GET.get('open_users_modal') == '1'

    character_q_value = request.GET.get('character_q', '').strip()
    character_status_filter = request.GET.get('character_status_filter', 'ALL')
    character_approval_filter = request.GET.get('character_approval_filter', 'ALL')
    open_personagens_modal = request.GET.get('open_personagens_modal') == '1'
    open_home_components_modal = request.GET.get('open_home_components_modal') == '1'

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

    personagens_queryset = Personagem.objects.select_related('usuario').order_by('nome')
    if character_q_value:
        query_lower = character_q_value.lower()
        matching_guildas = [
            guilda_id for guilda_id, guilda_nome in GUILDAS_CHOICES if query_lower in guilda_nome.lower()
        ]
        matching_classes = [
            classe_id for classe_id, classe_nome in CLASSES_CHOICES if query_lower in classe_nome.lower()
        ]
        personagens_queryset = personagens_queryset.filter(
            Q(nome__icontains=character_q_value)
            | Q(slug__icontains=character_q_value)
            | Q(usuario__username__icontains=character_q_value)
            | Q(usuario__email__icontains=character_q_value)
            | Q(guilda__in=matching_guildas)
            | Q(classe__in=matching_classes)
        )

    if character_status_filter != 'ALL':
        try:
            personagens_queryset = personagens_queryset.filter(status=int(character_status_filter))
        except (TypeError, ValueError):
            pass

    if character_approval_filter != 'ALL':
        try:
            personagens_queryset = personagens_queryset.filter(
                status_aprovacao=int(character_approval_filter)
            )
        except (TypeError, ValueError):
            pass

    personagens_data = [
        {
            'id': personagem.id,
            'nome': personagem.nome,
            'slug': personagem.slug,
            'usuario': personagem.usuario.username,
            'status': personagem.status,
            'status_display': personagem.get_status_display(),
            'classe': personagem.classe,
            'classe_display': personagem.get_classe_display() if personagem.classe else '',
            'guilda': personagem.guilda,
            'guilda_display': personagem.get_guilda_display() if personagem.guilda else '',
            'xp_atual': personagem.xp_atual,
            'ouro': personagem.ouro,
            'status_aprovacao': personagem.status_aprovacao,
            'status_aprovacao_display': personagem.get_status_aprovacao_display(),
        }
        for personagem in personagens_queryset
    ]

    context = {
        'users_with_role': users_with_role,
        'role_choices': Profile.UserRole.choices,
        'q_value': q_value,
        'role_filter': role_filter,
        'open_users_modal': open_users_modal,
        'personagens_data': personagens_data,
        'character_q_value': character_q_value,
        'character_status_filter': character_status_filter,
        'character_approval_filter': character_approval_filter,
        'open_personagens_modal': open_personagens_modal,
        'filter_role_options': [
            ('ALL', 'Todos os tipos'),
            ('ADMIN', 'Admin'),
            ('COMMON', 'Usuario comum'),
            ('SUPERUSER', 'Superusuario'),
        ],
        'character_status_options': [('ALL', 'Todos os status'), *STATUS_PERSONAGEM_CHOICES],
        'character_approval_options': [('ALL', 'Todos'), *STATUS_APROVACAO_CHOICES],
        'character_class_options': CLASSES_CHOICES,
        'character_guild_options': GUILDAS_CHOICES,
        'home_config': home_config,
        'layout_config': layout_config,
        'open_home_components_modal': open_home_components_modal,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def user_dashboard(request):
    return render(request, 'dashboard/user_dashboard.html')
