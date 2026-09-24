from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.constants.guildas import GUILDAS
from core.models import HomeDynamicSection, HomePageConfig, LarpEvento, LarpInscricao, Profile, SiteLayoutConfig
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
    if user.is_superuser or user.is_staff:
        return True
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role == Profile.UserRole.ADMIN


def home(request):
    guildas_home = [
        {
            'nome': info.get('nome', key.replace('_', ' ').title()),
            'imagem': info.get('imagem', ''),
            'lema': info.get('lema') or 'Uma história ainda será escrita.',
        }
        for key, info in GUILDAS.items()
        if info.get('imagem')
    ]
    show_character_prompt = (
        request.user.is_authenticated
        and not _is_admin(request.user)
        and not Personagem.objects.filter(usuario=request.user).exists()
    )
    return render(
        request,
        'dashboard/home.html',
        {
            'guildas_home': guildas_home,
            'show_character_prompt': show_character_prompt,
        },
    )


@login_required(login_url='login')
def admin_dashboard(request):
    if not _is_admin(request.user):
        return redirect('home')

    def _redirect_admin_with_filters(q_value, role_value):
        params = {'open_users_modal': '1'}
        if q_value:
            params['q'] = q_value
        if role_value and role_value != 'ALL':
            params['role_filter'] = role_value
        return redirect(f"{reverse('admin_dashboard')}?{urlencode(params)}")

    home_config = HomePageConfig.load()
    layout_config = SiteLayoutConfig.load()

    if request.method == 'POST' and request.POST.get('action') == 'update_theme_config':
        color_fields = (
            'primary_color',
            'primary_content_color',
            'secondary_color',
            'secondary_content_color',
			'site_background_color',
			'site_surface_color',
			'site_accent_color',
			'site_accent_content_color',
			'site_text_color',
			'site_muted_text_color',
        )
        for field_name in color_fields:
            value = request.POST.get(field_name, '').strip().upper()
            if len(value) == 7 and value.startswith('#'):
                setattr(layout_config, field_name, value)
        layout_config.full_clean()
        layout_config.save(update_fields=color_fields)
        messages.success(request, 'Cores do layout atualizadas para todo o site.')
        return redirect(f"{reverse('admin_dashboard')}?open_theme_modal=1")

    if request.method == 'POST' and request.POST.get('action') == 'update_social_links':
        social_fields = (
            'social_instagram_url',
            'social_whatsapp_url',
            'social_x_url',
            'social_youtube_url',
        )
        for field_name in social_fields:
            setattr(layout_config, field_name, request.POST.get(field_name, '').strip())

        try:
            layout_config.full_clean()
        except ValidationError:
            messages.error(request, 'Confira se todos os links das redes sociais sao URLs validas.')
            return redirect(f"{reverse('admin_dashboard')}?open_social_modal=1")

        layout_config.save(update_fields=social_fields)
        messages.success(request, 'Links das redes sociais atualizados com sucesso.')
        return redirect(f"{reverse('admin_dashboard')}?open_social_modal=1")

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

        section_ids = request.POST.getlist('section_ids')
        for section_id in section_ids:
            section = HomeDynamicSection.objects.filter(id=section_id).first()
            if not section:
                continue

            section.title = request.POST.get(f'section_title_{section_id}', section.title).strip()
            section.content = request.POST.get(f'section_content_{section_id}', section.content).strip()
            section.is_visible = request.POST.get(f'section_visible_{section_id}') == 'on'

            order_raw = request.POST.get(f'section_order_{section_id}', section.display_order)
            try:
                section.display_order = max(1, int(order_raw))
            except (TypeError, ValueError):
                pass

            section.save()

        delete_section_ids = request.POST.getlist('delete_section_ids')
        if delete_section_ids:
            HomeDynamicSection.objects.filter(id__in=delete_section_ids).delete()

        new_title = request.POST.get('new_section_title', '').strip()
        new_content = request.POST.get('new_section_content', '').strip()
        if new_title and new_content:
            new_order_raw = request.POST.get('new_section_order', '1').strip()
            try:
                new_order = max(1, int(new_order_raw))
            except (TypeError, ValueError):
                new_order = 1

            HomeDynamicSection.objects.create(
                title=new_title,
                content=new_content,
                display_order=new_order,
                is_visible=request.POST.get('new_section_visible') == 'on',
            )

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

    if request.method == 'POST' and request.POST.get('action') == 'create_larp_event':
        titulo = request.POST.get('larp_titulo', '').strip()
        local = request.POST.get('larp_local', '').strip()
        historia = request.POST.get('larp_historia', '').strip()
        data_evento_raw = request.POST.get('larp_data_evento', '').strip()
        visivel_publicamente = request.POST.get('larp_visivel_publicamente') == 'on'

        data_evento = parse_datetime(data_evento_raw) if data_evento_raw else None
        if data_evento and timezone.is_naive(data_evento):
            data_evento = timezone.make_aware(data_evento, timezone.get_current_timezone())

        if not titulo or not local or not historia or not data_evento:
            messages.error(request, 'Preencha titulo, local, historia e data para criar o LARP.')
            return redirect(f"{reverse('admin_dashboard')}?open_larps_modal=1")

        LarpEvento.objects.create(
            titulo=titulo,
            local=local,
            historia=historia,
            data_evento=data_evento,
            visivel_publicamente=visivel_publicamente,
            criado_por=request.user,
        )

        messages.success(request, 'LARP criado com sucesso.')
        return redirect(f"{reverse('admin_dashboard')}?open_larps_modal=1")

    if request.method == 'POST' and request.POST.get('action') == 'bulk_update_larp_visibility':
        evento_ids = request.POST.getlist('larp_ids')
        updated_count = 0

        for evento_id in evento_ids:
            evento = LarpEvento.objects.filter(id=evento_id).first()
            if not evento:
                continue

            nova_visibilidade = request.POST.get(f'larp_visivel_{evento_id}') == 'on'
            if evento.visivel_publicamente != nova_visibilidade:
                evento.visivel_publicamente = nova_visibilidade
                evento.save(update_fields=['visivel_publicamente'])
                updated_count += 1

        if updated_count:
            messages.success(request, 'Visibilidade dos LARPs atualizada.')
        else:
            messages.info(request, 'Nenhuma alteracao de visibilidade foi feita.')

        return redirect(f"{reverse('admin_dashboard')}?open_larps_modal=1")

    q_value = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role_filter', 'ALL')
    open_users_modal = request.GET.get('open_users_modal') == '1'

    character_q_value = request.GET.get('character_q', '').strip()
    character_status_filter = request.GET.get('character_status_filter', 'ALL')
    character_approval_filter = request.GET.get('character_approval_filter', 'ALL')
    open_personagens_modal = request.GET.get('open_personagens_modal') == '1'
    open_home_components_modal = request.GET.get('open_home_components_modal') == '1'
    open_larps_modal = request.GET.get('open_larps_modal') == '1'
    open_theme_modal = request.GET.get('open_theme_modal') == '1'
    open_social_modal = request.GET.get('open_social_modal') == '1'

    now = timezone.now()
    total_users = User.objects.count()
    total_admins = User.objects.filter(
        Q(is_superuser=True) | Q(profile__role=Profile.UserRole.ADMIN)
    ).distinct().count()
    total_characters = Personagem.objects.count()
    total_larps = LarpEvento.objects.count()
    total_registrations = LarpInscricao.objects.count()

    dashboard_stats = {
        'users_total': total_users,
        'users_admin': total_admins,
        'users_common': max(0, total_users - total_admins),
        'characters_total': total_characters,
        'characters_pending': Personagem.objects.filter(status_aprovacao=STATUS_APROVACAO.PENDENTE).count(),
        'characters_active': Personagem.objects.filter(status=STATUS_PERSONAGEM_CHOICES[0][0]).count(),
        'characters_without_guild': Personagem.objects.filter(guilda__isnull=True).count(),
        'characters_with_guild': Personagem.objects.filter(guilda__isnull=False).count(),
        'larps_total': total_larps,
        'larps_public': LarpEvento.objects.filter(visivel_publicamente=True).count(),
        'larps_private': LarpEvento.objects.filter(visivel_publicamente=False).count(),
        'larps_upcoming': LarpEvento.objects.filter(data_evento__gte=now).count(),
        'registrations_total': total_registrations,
        'guilds_total': len(GUILDAS_CHOICES),
        'home_sections_visible': HomeDynamicSection.objects.filter(is_visible=True).count(),
    }

    recent_users = User.objects.order_by('-date_joined', '-id')[:5]
    recent_characters = Personagem.objects.select_related('usuario').order_by('-data_criacao', '-id')[:5]
    recent_larps = LarpEvento.objects.order_by('-data_criacao', '-id')[:5]
    pending_characters = Personagem.objects.select_related('usuario').filter(
        status_aprovacao=STATUS_APROVACAO.PENDENTE,
    ).order_by('-data_criacao', '-id')[:5]

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

    larp_events_queryset = LarpEvento.objects.prefetch_related('inscricoes').order_by('-data_evento')
    larp_events_data = []
    for evento in larp_events_queryset:
        inscricao_path = reverse(
            'inscricao_larp',
            kwargs={'slug': evento.slug, 'token': evento.inscricao_token},
        )
        inscricao_url = request.build_absolute_uri(inscricao_path)
        larp_events_data.append(
            {
                'id': evento.id,
                'titulo': evento.titulo,
                'local': evento.local,
                'data_evento': evento.data_evento,
                'visivel_publicamente': evento.visivel_publicamente,
                'inscricao_path': inscricao_path,
                'inscricao_url': inscricao_url,
                'inscricoes_count': evento.inscricoes.count(),
            }
        )

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
        'dynamic_sections': HomeDynamicSection.objects.all(),
        'open_home_components_modal': open_home_components_modal,
        'open_theme_modal': open_theme_modal,
        'open_social_modal': open_social_modal,
        'larp_events_data': larp_events_data,
        'open_larps_modal': open_larps_modal,
        'dashboard_stats': dashboard_stats,
        'recent_users': recent_users,
        'recent_characters': recent_characters,
        'recent_larps': recent_larps,
        'pending_characters': pending_characters,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def user_dashboard(request):
    return render(request, 'dashboard/user_dashboard.html')
