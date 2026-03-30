"""Conteudo estatico de regras para a Wiki.

Estrutura pensada para evoluir com itens, magias e outras secoes sem depender de banco.
"""

REGRAS = [
    {
        'slug': 'personagem-e-ficha',
        'titulo': 'Personagem e Ficha',
        'categoria': 'Base',
        'resumo': 'Define como o personagem deve ser criado, aprovado e mantido no sistema.',
        'ordem': 1,
        'secoes': [
            {
                'titulo': 'Diretrizes Gerais',
                'itens': [
                    'Cada conta pode ter multiplos personagens.',
                    'Toda ficha precisa de nome, historia, classe e guilda (quando aplicavel).',
                    'Personagens devem seguir o lore e o tom do cenario.',
                ],
            },
            {
                'titulo': 'Aprovacao',
                'itens': [
                    'Personagens novos entram como pendentes de avaliacao.',
                    'A equipe de administracao pode aprovar, pedir ajustes ou recusar.',
                    'Apenas personagens aprovados contam para estatisticas oficiais.',
                ],
            },
        ],
    },
    {
        'slug': 'conduta-e-convivencia',
        'titulo': 'Conduta e Convivencia',
        'categoria': 'Comportamento',
        'resumo': 'Padrao minimo de respeito e seguranca para interacoes dentro e fora de jogo.',
        'ordem': 2,
        'secoes': [
            {
                'titulo': 'Respeito',
                'itens': [
                    'Ataques pessoais, assedio e discriminacao nao sao tolerados.',
                    'Conflitos IC (in character) nao justificam desrespeito OOC (out of character).',
                    'A moderacao pode intervir sempre que necessario para manter seguranca do grupo.',
                ],
            },
            {
                'titulo': 'Postura da Comunidade',
                'itens': [
                    'Priorize colaboracao e jogo responsavel.',
                    'Reporte condutas problematicas para admin ou mestres.',
                    'Decisoes administrativas sobre convivio e seguranca sao finais.',
                ],
            },
        ],
    },
    {
        'slug': 'interacoes-ic-e-ooc',
        'titulo': 'Interacoes IC e OOC',
        'categoria': 'Interpretacao',
        'resumo': 'Separa acao de personagem e pessoa jogadora para evitar confusoes e conflitos.',
        'ordem': 3,
        'secoes': [
            {
                'titulo': 'IC (In Character)',
                'itens': [
                    'Acoes IC devem respeitar as limitacoes do cenario e da propria ficha.',
                    'Consequencias narrativas podem ocorrer durante eventos e tramas.',
                    'Informacoes IC nao devem ser usadas como vantagem OOC.',
                ],
            },
            {
                'titulo': 'OOC (Out of Character)',
                'itens': [
                    'Use canais OOC para combinados, duvidas e alinhamentos de cena.',
                    'Evite spoilers de trama em ambientes IC.',
                    'Sempre alinhe limites e consentimento antes de cenas sensiveis.',
                ],
            },
        ],
    },
    {
        'slug': 'eventos-e-presenca',
        'titulo': 'Eventos e Presenca',
        'categoria': 'Eventos',
        'resumo': 'Regras basicas para participacao em LARPs, pontualidade e comunicacao de ausencia.',
        'ordem': 4,
        'secoes': [
            {
                'titulo': 'Participacao',
                'itens': [
                    'Inscricoes devem ser feitas com personagem valido e dentro do prazo.',
                    'Chegue com antecedencia para check-in e alinhamentos iniciais.',
                    'Em caso de ausencia, avise a organizacao com antecedencia.',
                ],
            },
            {
                'titulo': 'No Dia do Evento',
                'itens': [
                    'Respeite orientacoes de seguranca da equipe organizadora.',
                    'Materiais de cena e espaco fisico devem ser preservados.',
                    'Condutas de risco podem resultar em retirada imediata da atividade.',
                ],
            },
        ],
    },
]
