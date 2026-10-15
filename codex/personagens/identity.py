import re
import unicodedata

from django.core.exceptions import ValidationError


DIVINITIES = ('Sun Wukong', 'Jhunni', 'Grande Corvo Ancestral', 'Espírito da Memória',
              'Solaris', 'Mãe Elemental', 'Lunna', 'Artista', 'Rainha da Morte')
FOCUS_TYPES = (('amuleto', 'Amuleto ou símbolo'), ('varinha', 'Varinha'),
               ('livro', 'Livro ou grimório'), ('instrumento', 'Instrumento musical'),
               ('voz', 'Canto'), ('outro', 'Outro objeto — avaliação da comissão'))


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold())
                   if not unicodedata.combining(c))


def validate_divinity(value):
    text = normalized(value.strip())
    if not text or re.search(r'\b(ate(?:u|us|ia|ias|ismo|ista|istas)|nenhuma?|filosofia)\b', text) or text in {'nao', 'sem', 'n/a', '-'} or text.startswith('sem divindade'):
        raise ValidationError('Clérigos e Paladinos precisam venerar uma divindade do cenário. Informe seu nome para avaliação da comissão.')


def validate_focus(value, kind=''):
    text = normalized(value.strip())
    weapons = r'\b(cajados?|espadas?|lancas?|adagas?|arcos?|bestas?|machados?|martelos?|facas?|manoplas?|armas?|escudos?)\b'
    if not text or re.search(weapons, text):
        raise ValidationError('Conjurar exige um único foco; ele não pode ser arma, escudo ou cajado.')
    if kind and kind not in dict(FOCUS_TYPES):
        raise ValidationError('Escolha um tipo de foco válido.')
