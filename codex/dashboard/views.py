from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .home_components import parse_components, serialize_components
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
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


GUILDA_SLUG_BY_KEY = {
    'ARTISTAS_DA_REVOLUCAO': 'artistas-da-revolucao',
    'CIRCULO_DO_FOGO': 'circulo-do-fogo',
    'FLORESTA_DO_SOL': 'floresta-do-sol',
    'IRMANDADE_DAS_TAVERNAS': 'irmandade-das-tavernas',
    'RASGA_MORTALHAS': 'os-rasga-mortalhas',
    'SOCIEDADE_ZAORI': 'sociedade-zaori',
    'MERCENARIOS_INDEPENDENTES': 'mercenarios-independentes',
}


def _is_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role == Profile.UserRole.ADMIN


def home(request, components=None, preview=False):
    guildas_home = [
        {
            'nome': info.get('nome', key.replace('_', ' ').title()),
            'imagem': info.get('imagem', ''),
            'slug': GUILDA_SLUG_BY_KEY.get(key, ''),
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
            'guildas_showcase': guildas_home,
            'show_character_prompt': show_character_prompt and not preview,
            'home_components': components if components is not None else HomeDynamicSection.objects.filter(is_visible=True),
        },
    )


@login_required(login_url='login')
@never_cache
@require_POST
def home_preview(request):
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Acesso restrito.'}, status=403)
    try:
        components = parse_components(request.POST.get('components_json'), user=request.user)
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)
    return home(request, components=components, preview=True)


@login_required(login_url='login')
@never_cache
def admin_user_profile(request, user_id):
    if not _is_admin(request.user):
        return redirect('home')
    account = get_object_or_404(User.objects.select_related('profile'), pk=user_id)
    profile = getattr(account, 'profile', None)
    return render(request, 'dashboard/admin_user_profile.html', {
        'account': account,
        'player_profile': profile,
        'account_is_admin': _is_admin(account),
        'characters': account.personagens.all(),
        'registrations': account.inscricoes_larp.select_related('evento', 'personagem'),
    })


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

    if request.method == 'POST' and request.POST.get('action') in ('update_theme_config', 'reset_theme_config'):
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
        reset_theme = request.POST.get('action') == 'reset_theme_config'
        for field_name in color_fields:
            value = (
                SiteLayoutConfig._meta.get_field(field_name).get_default()
                if reset_theme else request.POST.get(field_name, '').strip().upper()
            )
            setattr(layout_config, field_name, value)
        try:
            layout_config.full_clean()
        except ValidationError:
            messages.error(request, 'Informe cores validas no formato #RRGGBB.')
            return redirect(f"{reverse('admin_dashboard')}?open_theme_modal=1")
        layout_config.save(update_fields=color_fields)
        messages.success(request, 'Cores padrao restauradas.' if reset_theme else 'Cores do layout atualizadas para todo o site.')
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
        try:
            components = parse_components(request.POST.get('components_json'), user=request.user)
        except ValidationError as error:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': ' '.join(error.messages)}, status=400)
            messages.error(request, ' '.join(error.messages))
        else:
            with transaction.atomic():
                HomeDynamicSection.objects.all().delete()
                HomeDynamicSection.objects.bulk_create(components)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'saved': True})
            messages.success(request, 'Componentes publicados na home.')
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
        return redirect(f"{reverse('admin_dashboard')}?open_users_modal=1")

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

        try:
            data_evento = parse_datetime(data_evento_raw) if data_evento_raw else None
            data_limite = parse_datetime(request.POST.get('larp_data_limite_inscricao', '').strip())
        except ValueError:
            data_evento = data_limite = None
        if data_limite and timezone.is_naive(data_limite):
            data_limite = timezone.make_aware(data_limite, timezone.get_current_timezone())
        if data_evento and timezone.is_naive(data_evento):
            data_evento = timezone.make_aware(data_evento, timezone.get_current_timezone())

        if not titulo or not local or not historia or not data_evento or not data_limite:
            messages.error(request, 'Preencha titulo, local, historia, data do evento e prazo de inscricao.')
            return redirect(f"{reverse('admin_dashboard')}?open_larps_modal=1")

        if data_limite > data_evento:
            messages.error(request, 'O prazo de inscricao nao pode ser posterior ao evento.')
            return redirect(f"{reverse('admin_dashboard')}?open_larps_modal=1")

        LarpEvento.objects.create(
            titulo=titulo,
            local=local,
            historia=historia,
            data_evento=data_evento,
            data_limite_inscricao=data_limite,
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
        Q(is_superuser=True)
        | Q(is_staff=True)
        | Q(profile__role=Profile.UserRole.ADMIN)
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

    users = User.objects.select_related('profile').all().order_by('username')
    if q_value:
        users = users.filter(Q(username__icontains=q_value) | Q(email__icontains=q_value))

    users_with_role = []
    for user in users:
        if user.is_superuser:
            role_value = Profile.UserRole.ADMIN
            role_label = 'Admin (Superusuario)'
            role_key = 'SUPERUSER'
        elif user.is_staff or (
            hasattr(user, 'profile')
            and user.profile.role == Profile.UserRole.ADMIN
        ):
            role_value = Profile.UserRole.ADMIN
            role_label = 'Admin'
            role_key = Profile.UserRole.ADMIN
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
                'data_limite_inscricao': evento.data_limite_inscricao,
                'visivel_publicamente': evento.visivel_publicamente,
                'inscricao_path': inscricao_path,
                'inscricao_url': inscricao_url,
                'detalhe_url': reverse('detalhe_larp', kwargs={'slug': evento.slug}),
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
        'home_components_data': serialize_components(),
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
