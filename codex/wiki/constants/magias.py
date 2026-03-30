REGRAS_GERAIS_MAGIA = {
    "titulo": "Regras Gerais de Magia",
    "itens": [
        "Quem faz magia é chamado de conjurador.",
        "As magias escolhidas pela classe não podem ser mudadas depois.",
        "Para usar magia, é preciso dizer a invocação em voz alta e usar um foco de magia.",
        "O foco deve ser segurado e manipulado com uma das mãos.",
        "Se uma mão estiver ocupada com escudo ou arma, ela não pode usar foco ao mesmo tempo.",
        "Focos não podem ser armas.",
        "A invocação pode ser alterada, desde que não fique menor, não mude o sentido e mantenha as palavras principais em caixa alta.",
    ],
}

MAGIAS_WIKI = {
    "ANTIDOTO_MAGICO": {
        "nome": "Antídoto Mágico",
        "slug": "antidoto-magico",
        "quem_usa": ["Bardo", "Clérigo", "Druida"],
        "invocacao": "Força da Cachoeira, me ajude a NEUTRALIZAR ESSE VENENO!",
        "descricao": (
            "O conjurador abençoa uma semente dos deuses e faz um alvo comê-la imediatamente. "
            "Além dos efeitos normais da semente, o alvo fica curado de efeitos de veneno."
        ),
        "tipo": "Cura",
    },

    "BARREIRA_MAGICA": {
        "nome": "Barreira Mágica",
        "slug": "barreira-magica",
        "quem_usa": ["Clérigo", "Mago"],
        "invocacao": "BARREIRA!",
        "descricao": (
            "O conjurador segura o foco com as duas mãos e fica imune a todo tipo de dano por 4 segundos. "
            "Se soltar uma mão do foco ou se mover, o efeito se desfaz."
        ),
        "tipo": "Defesa",
        "extra": (
            "Após usar Barreira, é preciso esperar ao menos 10 segundos para usar novamente. "
            "Não pode ser usada se o conjurador estiver portando um escudo em qualquer mão."
        ),
    },

    "BOLA_DE_FOGO": {
        "nome": "Bola de Fogo",
        "slug": "bola-de-fogo",
        "quem_usa": ["Mago"],
        "invocacao": "BOLA DE FOGO!",
        "descricao": (
            "Um balão d’água é arremessado. Todas as regiões atingidas recebem dano, ignorando armadura. "
            "Se atingir simultaneamente peito e braço ou perna, o alvo sofre 3 de dano."
        ),
        "tipo": "Ofensiva",
        "extra": (
            "Se a água atingir um escudo, o dono deve soltá-lo, considerando que o escudo está pegando fogo "
            "por alguns minutos."
        ),
    },

    "COMUNHAO_COM_A_NATUREZA": {
        "nome": "Comunhão com a Natureza",
        "slug": "comunhao-com-a-natureza",
        "quem_usa": ["Druida"],
        "invocacao": (
            "Faça uma pequena oração em voz alta, clamando o poder da Terra e prometendo não fazer mal à natureza."
        ),
        "descricao": (
            "Criaturas sobrenaturais ligadas à natureza percebem a energia sagrada do conjurador e tendem a se "
            "tornar mais amigáveis ou menos hostis, desde que ele não represente risco."
        ),
        "tipo": "Interação",
        "extra": "É um efeito interpretativo e não envolve o restante do grupo.",
    },

    "CONTRAMAGICA": {
        "nome": "Contramágica",
        "slug": "contramagica",
        "quem_usa": ["Bardo", "Mago"],
        "invocacao": "CONTRA MÁGICA!",
        "descricao": (
            "Se o conjurador conseguir pegar uma bolinha de magia no ar antes dela atingir o alvo, "
            "a magia não faz efeito e a bolinha pode ser devolvida imediatamente com outra magia."
        ),
        "tipo": "Defesa",
    },

    "EXORCISMO": {
        "nome": "Exorcismo",
        "slug": "exorcismo",
        "quem_usa": ["Clérigo", "Mago", "Paladino"],
        "invocacao": "EXORCISMO! UM… DOIS… TRÊS… QUATRO… CINCO!",
        "descricao": (
            "O conjurador toca um alvo possuído por espíritos por 5 segundos, contando em voz alta. "
            "Se completar a contagem, o alvo é libertado. Em zumbis, o efeito transforma o alvo em corpo morto."
        ),
        "tipo": "Espiritual",
    },

    "LENTIDAO": {
        "nome": "Lentidão",
        "slug": "lentidao",
        "quem_usa": ["Bardo", "Clérigo", "Mago"],
        "invocacao": "LENTIDÃO!",
        "descricao": (
            "O alvo atingido por toque ou bolinha de magia não pode correr por 1 minuto. "
            "Deve caminhar devagar e não pode andar e lutar ao mesmo tempo."
        ),
        "tipo": "Controle",
    },

    "RAIO_ELETRICO": {
        "nome": "Raio Elétrico",
        "slug": "raio-eletrico",
        "quem_usa": ["Mago"],
        "invocacao": "RAIO ELÉTRICO!",
        "descricao": (
            "O conjurador toca ou arremessa a bolinha no alvo. "
            "A magia causa o mesmo dano de uma arma e ignora armadura."
        ),
        "tipo": "Ofensiva",
    },

    "SILENCIAR": {
        "nome": "Silenciar",
        "slug": "silenciar",
        "quem_usa": ["Bardo", "Mago"],
        "invocacao": "SILENCIAR!",
        "descricao": (
            "O alvo atingido por toque ou bolinha de magia não pode falar ou conjurar magias por 30 segundos "
            "ou até receber qualquer cura."
        ),
        "tipo": "Controle",
    },

    "TOQUE_DA_CURA": {
        "nome": "Toque da Cura",
        "slug": "toque-da-cura",
        "quem_usa": ["Clérigo", "Paladino", "Druida"],
        "invocacao": "Força ancestral da cachoeira, RECUPERAI este aliado!",
        "descricao": (
            "O conjurador toca o alvo por 5 segundos e, ao fim da invocação, recupera 1 PV e o desmembramento "
            "de um braço ou perna. Se o alvo estiver incapacitado, ele se levanta desmembrado do peito."
        ),
        "tipo": "Cura",
        "extra": (
            "Não recupera mais do que braços, pernas ou o PV perdido por um acerto no peito."
        ),
    },

    "VERSOS_DE_PROTECAO": {
        "nome": "Versos de Proteção",
        "slug": "versos-de-protecao",
        "quem_usa": ["Bardo", "Clérigo"],
        "invocacao": "VERSOS DE PROTEÇÃO!",
        "descricao": (
            "O personagem que já estava cantando, declamando ou orando antes do efeito fica imune a efeitos "
            "mentais ou espirituais."
        ),
        "tipo": "Defesa",
        "extra": (
            "Só funciona se o personagem já estiver cantando ou orando antes de ser afetado."
        ),
    },

    "VIGOR_DO_TOURO": {
        "nome": "Vigor do Touro",
        "slug": "vigor-do-touro",
        "quem_usa": ["Bardo", "Mago"],
        "invocacao": "Diga o nome do alvo e 'VIGOR DO TOURO'. Depois não pare de cantar ou entoar palavras mágicas.",
        "descricao": (
            "O alvo ignora o primeiro desmembramento sofrido naquele combate enquanto o conjurador não parar "
            "de cantar ou falar alto palavras mágicas."
        ),
        "tipo": "Buff",
    },
}