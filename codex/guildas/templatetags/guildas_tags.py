from django import template
from core.constants.guildas import GUILDAS

register = template.Library()


@register.filter
def get_guilda_nome(guilda_id):
    """Retorna o nome público da guilda dado o ID"""
    if guilda_id in GUILDAS:
        return GUILDAS[guilda_id].get('nome', '')
    return f'Guilda {guilda_id}'


@register.filter
def get_guilda_divindade(guilda_id):
    """Retorna a divindade da guilda"""
    if guilda_id in GUILDAS:
        return GUILDAS[guilda_id].get('divindade', 'Desconhecida')
    return 'Desconhecida'


@register.filter
def get_guilda_lema(guilda_id):
    """Retorna o lema da guilda"""
    if guilda_id in GUILDAS:
        return GUILDAS[guilda_id].get('lema', '')
    return ''


@register.filter
def get_guilda_emoji(guilda_id):
    """Retorna um emoji para a guilda baseado no ID"""
    emojis = {
        1: '🎨',  # Artistas da Revolução
        2: '🔥',  # Círculo do Fogo
        3: '🌿',  # Floresta do Sol
        4: '🍺',  # Irmandade das Tavernas
        5: '☠️',  # Os Rasga-Mortalhas
        6: '🔮',  # Sociedade Zaori
        7: '⚔️',  # Mercenários Independentes
    }
    return emojis.get(guilda_id, '🛡️')


@register.simple_tag
def get_guildas_dict():
    """Retorna o dicionário completo de guildas para usar em templates"""
    return GUILDAS
