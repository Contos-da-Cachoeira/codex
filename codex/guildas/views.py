from django.shortcuts import get_object_or_404, render
from django.template import TemplateDoesNotExist
from django.template.loader import select_template

from core.constants.guildas import GUILDAS
from core.context_processors import _is_admin
from personagens.models import Personagem
from personagens.consts import STATUS_APROVACAO, STATUS_PERSONAGEM
from .models import Guilda, GuildaMembro, GuildaNoticia


GUILDA_PUBLIC_KEY_BY_ID = {
    1: "ARTISTAS_DA_REVOLUCAO",
    2: "CIRCULO_DO_FOGO",
    3: "FLORESTA_DO_SOL",
    4: "IRMANDADE_DAS_TAVERNAS",
    5: "RASGA_MORTALHAS",
    6: "SOCIEDADE_ZAORI",
    7: "MERCENARIOS_INDEPENDENTES",
}

GUILDA_ESTILO_BY_ID = {
    1: {"icone": "🎭", "badge": "badge-secondary", "card": "bg-base-100"},
    2: {"icone": "🔥", "badge": "badge-error", "card": "bg-base-100"},
    3: {"icone": "🌿", "badge": "badge-success", "card": "bg-base-100"},
    4: {"icone": "🍻", "badge": "badge-warning", "card": "bg-base-100"},
    5: {"icone": "☠", "badge": "badge-neutral", "card": "bg-base-100"},
    6: {"icone": "🔮", "badge": "badge-info", "card": "bg-base-100"},
    7: {"icone": "⚔", "badge": "badge-accent", "card": "bg-base-100"},
}


def _get_info_publica(guilda_id):
    return GUILDAS.get(GUILDA_PUBLIC_KEY_BY_ID.get(guilda_id, ""), {})


def _get_template_detalhe(slug):
    template_options = [
        f"guildas/detalhes/{slug}.html",
        "guildas/detalhe_guilda.html",
    ]
    try:
        return select_template(template_options).template.name
    except TemplateDoesNotExist:
        return "guildas/detalhe_guilda.html"


def listar_guildas(request):
    """
    Lista todas as guildas ativas.
    Mostra informações públicas para todos.
    """
    guildas_db = Guilda.objects.filter(ativa=True)
    
    # Verificar se usuário é admin
    eh_admin = _is_admin(request.user)
    
    # Preparar dados com informações públicas + privadas
    guildas_info = []
    for guilda in guildas_db:
        info = {
            'db': guilda,
            'publica': _get_info_publica(guilda.guilda_id),
            'eh_membro': False,
            'pode_ver_privado': eh_admin,
            'estilo': GUILDA_ESTILO_BY_ID.get(guilda.guilda_id, GUILDA_ESTILO_BY_ID[1]),
        }
        
        # Se usuário está logado, verificar se é membro
        if request.user.is_authenticated:
            eh_membro = GuildaMembro.objects.filter(
                guilda=guilda,
                usuario=request.user
            ).exists()
            info['eh_membro'] = eh_membro
            info['pode_ver_privado'] = eh_membro or eh_admin
        
        guildas_info.append(info)
    
    context = {
        'guildas_info': guildas_info,
    }
    return render(request, 'guildas/listar_guildas.html', context)


def detalhe_guilda(request, slug):
    """
    Página de detalhes de uma guilda.
    
    Para todos:
    - Informações públicas (GUILDAS constants)
    - Quantidade de membros
    - Quantidade de personagens
    
    Apenas para membros e admins:
    - Descrição interna
    - Notícias da guilda
    - Contadores
    """
    guilda = get_object_or_404(Guilda, slug=slug, ativa=True)
    
    # Informações públicas
    info_publica = _get_info_publica(guilda.guilda_id)
    
    # Verificar se é membro ou admin
    eh_membro = False
    eh_admin = _is_admin(request.user)
    
    if request.user.is_authenticated:
        eh_membro = GuildaMembro.objects.filter(
            guilda=guilda,
            usuario=request.user
        ).exists()
    
    # Admin ou membro pode ver informações privadas
    pode_ver_privado = eh_membro or eh_admin
    
    # Informações que podem ser vistas por membros e admins
    noticias = []
    if pode_ver_privado:
        noticias = GuildaNoticia.objects.filter(
            guilda=guilda,
            publicado=True
        )
    
    # Obtém lista de personagens na guilda para contagem
    personagens_guilda = Personagem.objects.filter(
        guilda=guilda.guilda_id,
        status_aprovacao=STATUS_APROVACAO.APROVADO,
        status=STATUS_PERSONAGEM.ATIVO,
    )
    
    context = {
        'guilda': guilda,
        'info_publica': info_publica,
        'eh_membro': eh_membro,
        'eh_admin': eh_admin,
        'pode_ver_privado': pode_ver_privado,
        'noticias': noticias,
        'estilo': GUILDA_ESTILO_BY_ID.get(guilda.guilda_id, GUILDA_ESTILO_BY_ID[1]),
        'total_membros': guilda.total_membros,
        'total_personagens': guilda.total_personagens,
        'personagens_guilda': personagens_guilda,
    }

    template_name = _get_template_detalhe(guilda.slug)
    return render(request, template_name, context)
