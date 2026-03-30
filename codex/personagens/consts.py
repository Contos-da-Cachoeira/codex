from wiki.constants.magias import MAGIAS_WIKI


# ==========================================
# 🛡️ GUILDAS
# ==========================================

class GUILDAS:
    """
    IDs fixos das guildas do sistema.

    ⚠️ NÃO ALTERAR os números depois de produção,
    pois isso pode quebrar dados existentes no banco.
    """

    ARTISTAS_REVOLUCAO = 1
    CIRCULO_FOGO = 2
    FLORESTA_SOL = 3
    IRMANDADE_TAVERNAS = 4
    RASGA_MORTALHAS = 5
    SOCIEDADE_ZAORI = 6
    MERCENARIOS = 7


GUILDAS_CHOICES = (
    (GUILDAS.ARTISTAS_REVOLUCAO, "Artistas da Revolução"),
    (GUILDAS.CIRCULO_FOGO, "Círculo do Fogo"),
    (GUILDAS.FLORESTA_SOL, "Floresta do Sol"),
    (GUILDAS.IRMANDADE_TAVERNAS, "Irmandade das Tavernas"),
    (GUILDAS.RASGA_MORTALHAS, "Os Rasga-Mortalhas"),
    (GUILDAS.SOCIEDADE_ZAORI, "Sociedade Zaori"),
    (GUILDAS.MERCENARIOS, "Mercenários Independentes"),
)


# ==========================================
# ⚔️ CLASSES
# ==========================================

class CLASSES:
    """
    IDs fixos das classes do sistema.

    ⚠️ NÃO ALTERAR os números depois de produção.
    """

    BARBARO = 1
    BARDO = 2
    CACADOR = 3
    CLERIGO = 4
    DRUIDA = 5
    GUERREIRO = 6
    LADINO = 7
    MAGO = 8
    PALADINO = 9


CLASSES_CHOICES = (
    (CLASSES.BARBARO, "Bárbaro"),
    (CLASSES.BARDO, "Bardo"),
    (CLASSES.CACADOR, "Caçador"),
    (CLASSES.CLERIGO, "Clérigo"),
    (CLASSES.DRUIDA, "Druida"),
    (CLASSES.GUERREIRO, "Guerreiro"),
    (CLASSES.LADINO, "Ladino"),
    (CLASSES.MAGO, "Mago"),
    (CLASSES.PALADINO, "Paladino"),
)


def _build_magias_por_classe():
    classe_id_por_nome = {nome: classe_id for classe_id, nome in CLASSES_CHOICES}
    mapping = {}

    for magia in MAGIAS_WIKI.values():
        nome_magia = magia.get('nome', '').strip()
        if not nome_magia:
            continue

        for nome_classe in magia.get('quem_usa', []):
            classe_id = classe_id_por_nome.get(nome_classe)
            if classe_id is None:
                continue
            mapping.setdefault(classe_id, []).append(nome_magia)

    for classe_id, magias in mapping.items():
        mapping[classe_id] = sorted(set(magias))

    return mapping


MAGIAS_POR_CLASSE = _build_magias_por_classe()


CLASSES_CONJURADORAS_FIXAS = {
    CLASSES.DRUIDA,
    CLASSES.PALADINO,
}


CLASSES_CONJURADORAS = set(MAGIAS_POR_CLASSE.keys())


# ==========================================
# 🧙 STATUS DO PERSONAGEM
# ==========================================

class STATUS_PERSONAGEM:
    """
    Status geral do personagem.
    """

    ATIVO = 1
    INATIVO = 2
    MORTO = 3
    APOSENTADO = 4


STATUS_PERSONAGEM_CHOICES = (
    (STATUS_PERSONAGEM.ATIVO, "Ativo"),
    (STATUS_PERSONAGEM.INATIVO, "Inativo"),
    (STATUS_PERSONAGEM.MORTO, "Morto"),
    (STATUS_PERSONAGEM.APOSENTADO, "Aposentado"),
)


# ==========================================
# ✅ STATUS DE APROVAÇÃO
# ==========================================

class STATUS_APROVACAO:
    """
    Controle administrativo de personagens.
    """

    PENDENTE = 1
    APROVADO = 2
    REJEITADO = 3


STATUS_APROVACAO_CHOICES = (
    (STATUS_APROVACAO.PENDENTE, "Pendente"),
    (STATUS_APROVACAO.APROVADO, "Aprovado"),
    (STATUS_APROVACAO.REJEITADO, "Rejeitado"),
)


# ==========================================
# 🧠 FUNÇÕES AUXILIARES (OPCIONAL)
# ==========================================

def get_nome_guilda(guilda_id: int) -> str:
    """
    Retorna o nome da guilda a partir do ID.

    Ex:
        get_nome_guilda(5) -> "Os Rasga-Mortalhas"
    """
    return dict(GUILDAS_CHOICES).get(guilda_id, "Desconhecida")


def get_nome_classe(classe_id: int) -> str:
    """
    Retorna o nome da classe a partir do ID.

    Ex:
        get_nome_classe(1) -> "Bárbaro"
    """
    return dict(CLASSES_CHOICES).get(classe_id, "Desconhecida")