from types import SimpleNamespace

from django.http import Http404
from django.shortcuts import render
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

# Slugs estaveis para os links publicos. Eles nao dependem dos registros
# administrativos existirem no banco de dados.
GUILDA_SLUG_BY_ID = {
    1: "artistas-da-revolucao",
    2: "circulo-do-fogo",
    3: "floresta-do-sol",
    4: "irmandade-das-tavernas",
    5: "os-rasga-mortalhas",
    6: "sociedade-zaori",
    7: "mercenarios-independentes",
}
GUILDA_ID_BY_SLUG = {slug: guilda_id for guilda_id, slug in GUILDA_SLUG_BY_ID.items()}

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
    guildas_db = {
        guilda.guilda_id: guilda
        for guilda in Guilda.objects.all()
    }
    
    # Verificar se usuário é admin
    eh_admin = _is_admin(request.user)
    
    # Preparar dados com informações públicas + privadas
    guildas_info = []
    for guilda_id in GUILDA_PUBLIC_KEY_BY_ID:
        guilda = guildas_db.get(guilda_id)

        # O conteudo publico existe em core.constants.guildas e nao deve
        # desaparecer da pagina enquanto os dados administrativos ainda nao
        # foram cadastrados.
        if guilda is not None and not guilda.ativa:
            continue

        info = {
            'db': guilda,
            'slug': GUILDA_SLUG_BY_ID[guilda_id],
            'publica': _get_info_publica(guilda_id),
            'eh_membro': False,
            'pode_ver_privado': bool(guilda) and eh_admin,
            'estilo': GUILDA_ESTILO_BY_ID.get(guilda_id, GUILDA_ESTILO_BY_ID[1]),
        }
        
        # Se usuário está logado, verificar se é membro
        if guilda is not None and request.user.is_authenticated:
            eh_membro = GuildaMembro.objects.filter(
                guilda=guilda,
                usuario=request.user
            ).exists()
            info['eh_membro'] = eh_membro
            info['pode_ver_privado'] = eh_membro or eh_admin
        
        guildas_info.append(info)
    
    context = {
        'guildas_info': guildas_info,
        'guildas_showcase': [
            {
                'nome': item['publica'].get('nome', ''),
                'imagem': item['publica'].get('imagem', ''),
                'slug': item['slug'],
            }
            for item in guildas_info
        ],
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
    guilda_id = GUILDA_ID_BY_SLUG.get(slug)
    if guilda_id is None:
        raise Http404

    guilda_registro = Guilda.objects.filter(
        guilda_id=guilda_id,
        ativa=True,
    ).first()

    # As paginas publicas podem ser acessadas mesmo antes do cadastro dos
    # registros administrativos. Quando o registro existir, todas as areas
    # privadas e estatisticas continuam funcionando normalmente.
    guilda = guilda_registro or SimpleNamespace(
        guilda_id=guilda_id,
        slug=slug,
        descricao_interna="",
        total_membros=0,
        total_personagens=0,
    )
    
    # Informações públicas
    info_publica = _get_info_publica(guilda.guilda_id)
    
    # Verificar se é membro ou admin
    eh_membro = False
    eh_admin = _is_admin(request.user)
    
    if guilda_registro is not None and request.user.is_authenticated:
        eh_membro = GuildaMembro.objects.filter(
            guilda=guilda,
            usuario=request.user
        ).exists()
    
    # Admin ou membro pode ver informações privadas
    pode_ver_privado = guilda_registro is not None and (eh_membro or eh_admin)
    
    # Informações que podem ser vistas por membros e admins
    noticias = []
    if pode_ver_privado:
        noticias = GuildaNoticia.objects.filter(
            guilda=guilda_registro,
            publicado=True
        )
    
    # Obtém lista de personagens na guilda para contagem
    personagens_guilda = Personagem.objects.select_related('image_asset', 'usuario__profile__image_asset').filter(
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
