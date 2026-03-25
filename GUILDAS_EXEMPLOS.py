"""
Script de teste do sistema de guildas.

Para usar, abra um shell Django:
    python manage.py shell_plus

Depois copie e cole o código abaixo para testar.
"""

# ============================================
# 1. VISUALIZAR GUILDAS
# ============================================

# Listar todas as guildas
from guildas.models import Guilda

guildas = Guilda.objects.all()
for guilda in guildas:
    print(f"{guilda} - Membros: {guilda.total_membros}, Personagens: {guilda.total_personagens}")


# ============================================
# 2. CRIAR NOTÍCIA
# ============================================

from guildas.models import GuildaNoticia

guilda_fogo = Guilda.objects.get(guilda_id=2)  # Círculo do Fogo

noticia = GuildaNoticia.objects.create(
    guilda=guilda_fogo,
    titulo="Primeira Reunião de Guerra",
    conteudo="Todos os guerreiros devem se reunir na forja do grande corvo...",
    publicado=True
)

print(f"Notícia criada: {noticia}")


# ============================================
# 3. VERIFICAR MEMBROS
# ============================================

from guildas.models import GuildaMembro

membros = GuildaMembro.objects.filter(guilda=guilda_fogo)
for membro in membros:
    print(f"{membro.usuario.username} - Desde: {membro.data_entrada}")


# ============================================
# 4. ATUALIZAR DESCRIÇÃO INTERNA
# ============================================

guilda_fogo.descricao_interna = """
## Informações Secretas do Círculo do Fogo

- Reunião: Toda terça-feira
- Local: Torre de Alerta
- Tesouro Atual: 5000 ouro
- Missões Ativas: 3
"""
guilda_fogo.save()

print("Descrição atualizada!")


# ============================================
# 5. CRIAR PERSONAGEM E VERIFICAR SIGNAL
# ============================================

from personagens.models import Personagem
from personagens.consts import GUILDAS, CLASSES

# Encontra um usuário de teste
from django.contrib.auth.models import User
user = User.objects.first()

# Cria personagem
personagem = Personagem.objects.create(
    usuario=user,
    nome="Guerreiro Teste",
    guilda=GUILDAS.CIRCULO_FOGO,
    classe=CLASSES.GUERREIRO,
)

print(f"Personagem criado: {personagem}")

# Verifica se o usuário foi registrado como membro
membro_criado = GuildaMembro.objects.filter(
    guilda=guilda_fogo,
    usuario=user
).exists()

print(f"Usuário registrado como membro: {membro_criado}")

# Verifica contadores atualizados
guilda_fogo.refresh_from_db()
print(f"Total de membros: {guilda_fogo.total_membros}")
print(f"Total de personagens: {guilda_fogo.total_personagens}")


# ============================================
# 6. USANDO TEMPLATE TAGS
# ============================================

# Em um template:
"""
{% load guildas_tags %}

{{ guilda_id|get_guilda_nome }}        {# "Círculo do Fogo" #}
{{ guilda_id|get_guilda_emoji }}       {# "🔥" #}
{{ guilda_id|get_guilda_divindade }}   {# "Grande Corvo Ancestral ou Wukong" #}
"""


# ============================================
# 7. ACESSAR INFORMAÇÕES PÚBLICAS
# ============================================

from core.constants.guildas import GUILDAS

info_fogo = GUILDAS[2]
print(f"Nome: {info_fogo['nome']}")
print(f"Divindade: {info_fogo['divindade']}")
print(f"Lema: {info_fogo['lema']}")
print(f"Vantagem: {info_fogo['vantagem']}")
print(f"Marca: {info_fogo['marca_nome']} -> {info_fogo['marca_efeito']}")
