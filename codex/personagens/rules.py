"""Regras estruturadas do Manual LARP 3.3 (páginas 10–20).

Cada compra ativa ocupa uma das cinco vagas, inclusive compras repetidas.
Esta contagem foi definida pelo responsável pelo site em 15/10/2026.
"""
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone

from core.models import Profile
from wiki.constants.classes import CLASSES_WIKI
from wiki.constants.magias import MAGIAS_WIKI
from wiki.constants.talentos import TALENTOS_WIKI
from wiki.catalog import talent_catalog, spells_by_class, all_spells, class_catalog
from .consts import CLASSES_CHOICES, MAGIAS_POR_CLASSE
from .identity import validate_divinity, validate_focus

CLASS_DATA = dict(zip((n for n, _ in CLASSES_CHOICES), CLASSES_WIKI.values()))
SPELL_COUNTS = {2: 3, 4: 3, 8: 4}
ANCIENT_SPELLS = ('Controle Mental', 'Necromancia', 'Petrificação')
ALL_SPELLS = sorted({m['nome'] for m in MAGIAS_WIKI.values()})
REPEATABLE = {key for key, item in TALENTOS_WIKI.items() if item.get('stackavel')} | {'FEITICO_ANTIGO', 'FORMA_SELVAGEM'}
NATIVE = {
    'ARMAS_CURTAS': {1, 2, 3, 4, 5, 6, 7, 9},
    'ARMAS_MEDIAS': {1, 3, 4, 5, 6, 9},
    'ARMAS_LONGAS': {1, 5, 6, 9},
    'USAR_ARREMESSO': {2, 7}, 'USAR_ARCO': {3, 7},
    'USAR_ESFERAS': {8}, 'USAR_CAJADO': {4, 5, 8},
    'USAR_ESCUDO': {1, 4, 6, 9}, 'USAR_MANOPLA': {5},
}
FOCI = {
    2: 'Instrumento musical (tocado) ou canto. Instrumentos de sopro são proibidos.',
    4: 'Cajado, amuleto da divindade ou livro sagrado.',
    5: 'Cajado, cristais ou amuletos ligados à natureza; mato, flores ou folhas pelo Dom de Druida (sem galhos duros).',
    8: 'Cajado, varinha ou grimório (livro de magia).',
    9: 'Símbolo da divindade; na frente do escudo, ele conta como foco.',
}


def validate_base(character, require_commission=False):
    errors = {}
    spells = character.magias_pretendidas or []
    available = spells_by_class(include_hidden=bool(character.pk)).get(character.classe, [])
    if character.classe not in CLASS_DATA:
        errors['classe'] = 'Escolha uma classe.'
    elif character.classe in SPELL_COUNTS:
        count = SPELL_COUNTS[character.classe]
        if len(spells) != count or len(set(spells)) != count or not set(spells) <= set(available):
            errors['magias_pretendidas'] = f'Escolha exatamente {count} magias iniciais desta classe.'
    elif set(spells) != set(available) or len(spells) != len(available):
        errors['magias_pretendidas'] = 'As magias iniciais precisam corresponder à classe.'
    if character.classe == 8 and character.feitico_antigo not in ANCIENT_SPELLS:
        errors['feitico_antigo'] = 'Escolha um feitiço antigo inicial.'
    if character.classe in {4, 9}:
        try:
            validate_divinity(character.divindade)
        except ValidationError as error:
            errors['divindade'] = error.messages
    if character.classe == 5:
        if not character.afinidade.strip():
            errors['afinidade'] = 'Informe sua afinidade com a natureza.'
        if require_commission and not character.forma_selvagem.strip():
            errors['forma_selvagem'] = 'A comissão precisa registrar três características e um defeito da forma.'
    if require_commission and character.revisao_manual:
        errors['revisao_manual'] = 'Revise a ficha antiga conforme o manual antes de aprová-la.'
    if errors:
        raise ValidationError(errors)


def active_purchases(character):
    if not character.pk:
        return []
    return list(character.compras_talentos.filter(status='approved', ativo=True))


def validate_talent(character, purchase, benefits=None, acquiring=True, commission=False):
    key = purchase.talento
    catalog = talent_catalog() if acquiring else talent_catalog(include_hidden=True)
    rule = catalog.get(key) if acquiring else (purchase.regra_snapshot or catalog.get(key))
    if not rule:
        raise ValidationError('Talento inválido.')
    if purchase.magia and key not in {'MAGIA_EXTRA_CLASSE', 'MAGIA_OUTRA_CLASSE', 'CONJURAR', 'FEITICO_ANTIGO', 'MULTICLASSE'}:
        raise ValidationError('Este talento não concede uma magia.')
    if purchase.segunda_classe and key != 'MULTICLASSE':
        raise ValidationError('A segunda classe é exclusiva de Multiclasse.')
    benefits = active_purchases(character) if benefits is None else benefits
    others = [p for p in benefits if p.pk != purchase.pk or p.pk is None]
    keys = {p.talento for p in others}
    classes = {character.classe} | {p.segunda_classe for p in others if p.talento == 'MULTICLASSE'}
    spell_lists = spells_by_class(include_hidden=not acquiring)
    caster = bool(classes & {2, 4, 5, 8, 9}) or 'CONJURAR' in keys
    knows = lambda k: character.classe in NATIVE.get(k, set()) or k in keys
    from .models import CompraTalento
    acquired = character.compras_talentos.filter(status='approved').exclude(pk=purchase.pk) if character.pk else CompraTalento.objects.none()
    repeatable = rule.get('stackavel')
    if acquiring and not repeatable and acquired.filter(talento=key).exists():
        raise ValidationError('Este talento já foi adquirido e não permite compras repetidas.')
    if acquiring and character.classe in NATIVE.get(key, set()):
        raise ValidationError('Sua classe já possui esta capacidade.')
    needs = {'ARREMESSO_EXTRA': 'USAR_ARREMESSO', 'FLECHAS_ADICIONAIS': 'USAR_ARCO',
             'ESFERAS_ADICIONAIS': 'USAR_ESFERAS', 'ARMAS_MEDIAS': 'ARMAS_CURTAS', 'ARMAS_LONGAS': 'ARMAS_MEDIAS'}
    if key in needs and not knows(needs[key]):
        raise ValidationError('Pré-requisito: ' + TALENTOS_WIKI[needs[key]]['nome'] + '.')
    # O benefício condicional do Círculo do Fogo não substitui a compra de Armas curtas.
    if key in {'MAGIA_OUTRA_CLASSE', 'USAR_ESFERAS', 'USAR_CAJADO'} and not caster:
        raise ValidationError('É necessário ser conjurador.')
    if acquiring and key == 'USAR_ESFERAS' and 8 in classes:
        raise ValidationError('Magos já sabem usar esferas de magia.')
    if key == 'USAR_CAJADO':
        touch = {'Exorcismo', 'Lentidão', 'Raio Elétrico', 'Silenciar', 'Toque da Cura'}
        known = set(character.magias_pretendidas) | {p.magia for p in others if p.magia}
        if not known & touch:
            raise ValidationError('É necessário saber conjurar uma magia de toque.')
    if acquiring and key == 'CONJURAR' and caster:
        raise ValidationError('O personagem já é conjurador.')
    if key == 'FEITICO_ANTIGO' and 8 not in classes:
        raise ValidationError('Feitiço antigo adicional exige a classe Mago.')
    if key == 'FORMA_SELVAGEM' and 5 not in classes:
        raise ValidationError('Forma selvagem adicional exige a classe Druida.')
    if key == 'USO_EXTRA' and not classes & {1, 2, 3, 5, 6, 7, 8, 9}:
        raise ValidationError('Milagres de Clérigo não têm limite de uso. É necessária uma habilidade de uso único.')
    if key == 'BENEFICIOS_DE_PATENTE':
        if character.guilda not in {1, 2, 3, 4, 5, 6}:
            raise ValidationError('Benefícios de patente exige vínculo com uma guilda; mercenários não pertencem a uma guilda coletiva.')
        granted_guild = purchase.escolhas_classe.get('guilda')
        if not acquiring and granted_guild and granted_guild != character.guilda:
            raise ValidationError('A patente pertence à guilda em que foi concedida. Solicite avaliação da comissão após mudar de guilda.')
        count = character.inscricoes_larp.filter(presenca_confirmada=True, evento__data_evento__lte=timezone.now()).count() if character.pk else 0
        if acquiring and count < 2:
            raise ValidationError('É necessário confirmar duas participações anteriores com este personagem.')
        if commission and not purchase.detalhes.strip():
            raise ValidationError('A comissão precisa registrar as vantagens e desvantagens concedidas pela patente.')
    if key in {'MAGIA_EXTRA_CLASSE', 'MAGIA_OUTRA_CLASSE', 'CONJURAR'}:
        own = set().union(*(set(spell_lists.get(c, [])) for c in classes))
        allowed = own if key == 'MAGIA_EXTRA_CLASSE' else set(all_spells()) - own
        if key == 'CONJURAR' or not acquiring:
            allowed = set(all_spells(include_hidden=not acquiring))
        if not acquiring and purchase.regra_snapshot:
            allowed.add(purchase.magia)  # Uma edição editorial não apaga uma aquisição.
        if purchase.magia not in allowed:
            raise ValidationError('Escolha uma magia válida para este talento.')
        if acquiring and (purchase.magia in character.magias_pretendidas or acquired.filter(magia=purchase.magia).exists()):
            raise ValidationError('Esta magia já foi aprendida.')
    if key == 'CONJURAR':
        validate_focus(purchase.foco, purchase.tipo_foco)
    if key == 'FEITICO_ANTIGO':
        multi_ancient = {p.magia for p in others if p.talento == 'MULTICLASSE' and p.segunda_classe == 8}
        if purchase.magia not in ANCIENT_SPELLS or purchase.magia == character.feitico_antigo or purchase.magia in multi_ancient or (acquiring and acquired.filter(talento=key, magia=purchase.magia).exists()):
            raise ValidationError('Escolha outro feitiço antigo ainda não adquirido.')
    if key == 'FORMA_SELVAGEM' and not purchase.detalhes.strip():
        raise ValidationError('Informe a nova forma para definição das três características e do defeito pela comissão.')
    if key == 'MULTICLASSE':
        related = purchase.talentos_relacionados
        if purchase.segunda_classe not in CLASS_DATA or purchase.segunda_classe == character.classe:
            raise ValidationError('Escolha uma segunda classe diferente da principal.')
        if acquiring and (len(set(related)) < 2 or acquired.filter(pk__in=related).count() != len(set(related))):
            raise ValidationError('Indique ao menos duas compras anteriores relacionadas à segunda classe para avaliação da comissão.')
        if not purchase.detalhes.strip():
            raise ValidationError('Descreva a jornada interpretativa nas sessões e a relação dos talentos com a nova classe.')
        if purchase.segunda_classe == 8:
            if purchase.magia not in ANCIENT_SPELLS:
                raise ValidationError('Multiclasse Mago exige a escolha de um feitiço antigo inicial.')
        elif purchase.magia:
            raise ValidationError('Somente Multiclasse Mago concede a escolha de um feitiço antigo.')
        if purchase.segunda_classe in {4, 9}:
            validate_divinity(purchase.escolhas_classe.get('divindade', ''))
        if purchase.segunda_classe == 5:
            if not purchase.escolhas_classe.get('afinidade', '').strip():
                raise ValidationError('Informe a afinidade natural da segunda classe Druida.')
            if (commission or not acquiring) and not purchase.escolhas_classe.get('forma_selvagem', '').strip():
                raise ValidationError('A comissão precisa definir três características e um defeito para a forma da segunda classe Druida.')
    if not purchase.justificativa.strip():
        raise ValidationError('Justifique o talento com a história e a evolução do personagem.')


@transaction.atomic
def set_player_xp(user, amount, actor, reason, expected=None):
    from .models import MovimentoXP
    if not 0 <= amount <= 2147483647:
        raise ValidationError('XP precisa estar entre 0 e 2147483647.')
    Profile.objects.get_or_create(user=user)
    wallet = Profile.objects.select_for_update().get(user=user)
    if expected is not None and wallet.xp_disponivel != expected:
        raise ValidationError('O saldo de XP mudou desde que a tela foi aberta. Atualize os dados antes de ajustar o saldo.')
    delta = amount - wallet.xp_disponivel
    if delta:
        wallet.xp_disponivel = amount
        wallet.save(update_fields=['xp_disponivel'])
        MovimentoXP.objects.create(jogador=user, valor=delta, saldo=amount, responsavel=actor, motivo=reason)


@transaction.atomic
def approve_purchase(purchase_id, actor, commission_details=None):
    from .models import CompraTalento, MovimentoXP, Personagem
    if not actor.is_active or not (actor.is_staff or actor.is_superuser or getattr(getattr(actor, 'profile', None), 'role', '') == 'ADMIN'):
        raise PermissionDenied
    # Uma ordem estável de bloqueios serializa todas as compras do mesmo jogador.
    owner_id = CompraTalento.objects.values_list('personagem__usuario_id', flat=True).get(pk=purchase_id)
    wallet = Profile.objects.select_for_update().get(user_id=owner_id)
    purchase = CompraTalento.objects.select_for_update().select_related('personagem').get(pk=purchase_id)
    character = Personagem.objects.select_for_update().get(pk=purchase.personagem_id)
    if purchase.status != 'pending':
        raise ValidationError('Esta solicitação já foi analisada.')
    if commission_details is not None:
        if purchase.talento in {'FORMA_SELVAGEM', 'BENEFICIOS_DE_PATENTE'}:
            purchase.detalhes = commission_details.strip()
        elif purchase.talento == 'MULTICLASSE' and purchase.segunda_classe == 5:
            purchase.escolhas_classe = {**purchase.escolhas_classe, 'forma_selvagem': commission_details.strip()}
    validate_base(character, require_commission=True)
    validate_talent(character, purchase, commission=True)
    if wallet.xp_disponivel < purchase.custo_xp:
        raise ValidationError('Saldo de XP do jogador insuficiente.')
    wallet.xp_disponivel -= purchase.custo_xp
    wallet.save(update_fields=['xp_disponivel'])
    purchase.status, purchase.aprovado_por = 'approved', actor
    if purchase.talento == 'BENEFICIOS_DE_PATENTE':
        purchase.escolhas_classe = {**purchase.escolhas_classe, 'guilda': character.guilda}
    purchase.regra_snapshot = purchase.regra_snapshot or talent_catalog()[purchase.talento]
    purchase.save(update_fields=['status', 'aprovado_por', 'detalhes', 'escolhas_classe', 'regra_snapshot'])
    MovimentoXP.objects.create(jogador_id=owner_id, valor=-purchase.custo_xp, saldo=wallet.xp_disponivel,
                               compra=purchase, responsavel=actor, motivo='Compra: ' + purchase.nome)


@transaction.atomic
def activate_purchases(character_id, ids):
    from .models import Personagem
    character = Personagem.objects.select_for_update().get(pk=character_id)
    ids = {int(i) for i in ids}
    selected = list(character.compras_talentos.filter(pk__in=ids, status='approved').order_by('pk'))
    if len(ids) > 5 or len(selected) != len(ids):
        raise ValidationError('Escolha até cinco compras adquiridas deste personagem. Cada compra repetida ocupa uma vaga.')
    for purchase in selected:
        validate_talent(character, purchase, benefits=selected, acquiring=False)
    character.compras_talentos.update(ativo=False)
    character.compras_talentos.filter(pk__in=ids).update(ativo=True)


@transaction.atomic
def complete_multiclass(purchase_id, actor, choices):
    """Completa lacunas de compras antigas sem cobrar XP nem substituir escolhas fixadas."""
    from .models import CompraTalento, Personagem
    if not actor.is_active or not (actor.is_staff or actor.is_superuser or getattr(getattr(actor, 'profile', None), 'role', '') == 'ADMIN'):
        raise PermissionDenied
    purchase = CompraTalento.objects.select_for_update().get(pk=purchase_id)
    character = Personagem.objects.select_for_update().get(pk=purchase.personagem_id)
    if not purchase.precisa_completar_escolhas:
        raise ValidationError('Esta compra não possui escolhas pendentes de revisão.')
    if purchase.segunda_classe == 8 and purchase.magia not in ANCIENT_SPELLS:
        purchase.magia = choices.get('magia', '').strip()
    for key in ('divindade', 'afinidade', 'forma_selvagem'):
        if not purchase.escolhas_classe.get(key):
            purchase.escolhas_classe[key] = choices.get(key, '').strip()
    validate_talent(character, purchase, acquiring=False, commission=True)
    purchase.escolhas_classe['revisao_comissao'] = {'responsavel': actor.pk, 'em': timezone.now().isoformat()}
    purchase.save(update_fields=['magia', 'escolhas_classe'])
