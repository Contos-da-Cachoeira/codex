# Auditoria da criação de personagens - Manual LARP 3.3

> **Revisão posterior:** consulte a [auditoria completa com o cenário](auditoria-sistema-manual-cenario-2026-10-15.md) e o [registro de correções publicado](correcoes-manual-cenario-2026-10-15.md). Eles incluem as correções adicionais de concorrência de XP, Multiclasse, Forma Selvagem, prata e integração da wiki, validadas em 134 testes locais e 149 no servidor.

Data: 15/10/2026. Código analisado: revisão `ec3935d`.

Fonte: [Manual LARP - 3.3.pdf](<Manual LARP - 3.3.pdf>), com 25 páginas. As páginas citadas abaixo são as posições das páginas no PDF.

## Correções implementadas após a auditoria

As observações nas seções seguintes descrevem o código anterior à correção. A implementação agora valida as quantidades iniciais (Bardo/Clérigo: três; Mago: quatro), registra feitiço antigo, divindade e afinidade, explica as capacidades de cada classe e impede alterações livres da classe e das magias iniciais. A comissão registra a Forma Selvagem e revisa fichas antigas.

Os talentos passam por solicitações estruturadas, com custo, requisitos, magia/foco/segunda classe quando aplicáveis, justificativa e decisão da comissão. A aprovação desconta XP uma única vez e preserva o vínculo da compra com o personagem. O saldo pertence ao jogador, compartilhado entre seus personagens. Ativação e aquisição são separadas; há até cinco compras ativas.

**Definição do responsável pelo site em 15/10/2026:** duas compras de Armadura adicional ocupam **duas vagas** das cinco. Essa resposta substitui a definição anterior de uma vaga por tipo. O manual permite repetições e limita os benefícios simultâneos, mas não explicita essa contagem; a decisão foi confirmada pelo responsável.

A imagem fica na última etapa, com comparação entre nome, imagem da classe e foto própria. A escolha é salva e usada nas fichas, listas e painel administrativo.

A migração soma os saldos antigos por jogador, mantém os campos anteriores como histórico e sinaliza fichas existentes para revisão. Não inventa compras nem cobra retroativamente os talentos anotados. Antes de aplicar no banco compartilhado com produção, deve ser feita cópia de segurança e publicação coordenada do código; o processo de reversão não deve repetir a consolidação de XP.

Validação: 106 testes automatizados localmente em SQLite isolado, incluindo compras repetidas, pré-requisitos, saldo compartilhado, rejeição de pagamentos duplicados, preservação de dados antigos e segurança de acesso. A navegação administrativa e a criação com prévias também foram conferidas no navegador. A combinação com as proteções de produção passou em 121 testes no servidor.

Publicado em 15/10/2026, com backup PostgreSQL 18 e as três migrações aplicadas. Foram conferidos os arquivos ativos, a renderização de criação/talentos e a correspondência dos saldos com o histórico de XP. Detalhes e localização do backup em [deployment.md](deployment.md).

## Resultado original

A criação está parcialmente de acordo com o manual. As nove classes, as listas de magias por classe e os preços dos 25 talentos conferem. A seleção e a validação, porém, permitem fichas que não seguem essas regras.

Os principais problemas são: quantidade de magias sem validação adequada, caixas de magia que obrigam a selecionar todas no navegador, talentos sem compra em XP ou verificação dos requisitos, ausência de escolhas especiais e edição de classe sem revalidar a ficha.

Foram reproduzidos 22 cenários usando SQLite em memória, contas fictícias e um navegador isolado. Os exemplos de fichas salvas nessa análise não são registros de jogadores reais. A auditoria produz este relatório; não implementa mudanças nas regras do jogo.

## Classes e magias iniciais

Estas são as regras da classe base, antes de talentos ou exceções de guilda:

| Classe | Regra do manual | Página | Comportamento atual |
| --- | --- | --- | --- |
| Bárbaro | Sem magias naturais | 10 | Correto para a classe base |
| Bardo | Escolher exatamente 3 entre 6 | 11 | Servidor aceita de 1 a 6; navegador exige as 6 |
| Caçador | Sem magias naturais | 12 | Correto para a classe base |
| Clérigo | Escolher exatamente 3 entre 6 | 12 | Servidor aceita de 1 a 6; mesma lógica de caixas obrigatórias do Bardo |
| Druida | Receber as 3 magias: Antídoto Mágico, Comunhão com a Natureza e Toque da Cura | 13 | As 3 são atribuídas automaticamente; correto |
| Guerreiro | Sem magias naturais | 13 | Correto para a classe base |
| Ladino | Sem magias naturais | 13 | Correto para a classe base |
| Mago | Escolher exatamente 4 entre 8 | 14 | Servidor aceita de 1 a 8; mesma lógica de caixas obrigatórias do Bardo |
| Paladino | Receber Toque da Cura e Exorcismo | 15 | As 2 são atribuídas automaticamente; correto |

As listas de opções de magia foram comparadas com o manual. Não há divergência na associação de magias às cinco classes conjuradoras. O manual usa uma variação de nome, "Versos da Proteção", na descrição do Clérigo; a lista de magias usa "Versos de Proteção". Trata-se da mesma magia.

### 1. A tela exige todas as magias em vez da quantidade da classe

Prioridade: alta.

Em [criar_personagem.html](../codex/personagens/templates/personagens/criar_personagem.html), linha 479, cada caixa de magia recebe `input.required = true`. Em uma caixa de seleção, isso torna aquela caixa individualmente obrigatória. A validação da etapa, na linha 324, percorre esses campos.

Reprodução no navegador: selecionar Bardo, marcar Antídoto Mágico, Contramágica e Lentidão, e clicar em "Continuar para guilda". O navegador exige marcar Silenciar e impede avançar. Marcando também as três opções restantes, a etapa avança com seis magias, contrariando o limite inicial de três.

Correção indicada: contar as escolhas do grupo e informar "3 de 3" ou "4 de 4", com validação do grupo no navegador e no servidor. Não tornar cada caixa obrigatória.

### 2. O servidor aceita quantidades iniciais incorretas

Prioridade: alta.

Em [forms.py](../codex/personagens/forms.py), linhas 76 a 88, as classes de escolha só precisam enviar pelo menos uma magia. Não existe o requisito de três para Bardo/Clérigo ou quatro para Mago.

Foram aceitos Bardo com uma ou seis magias, Clérigo com uma ou seis e Mago com uma ou oito. Os casos corretos, de três/três/quatro, também foram aceitos.

Correção indicada: separar magias iniciais da classe de magias adquiridas por talentos. O limite inicial não deve bloquear uma magia adicional legitimamente comprada depois.

## Talentos e XP

### 3. O limite de cinco não significa cinco talentos gratuitos

Prioridade: alta. Referência: páginas 18 e 19.

O manual estabelece compra por XP, persistência do talento no personagem e limite de cinco talentos dos quais ele pode se beneficiar simultaneamente. Também exige justificativa na história e na evolução do personagem. Não concede cinco talentos gratuitos na criação.

A tela apresenta "Selecione até cinco talentos iniciais" e mostra apenas seus nomes. Em [forms.py](../codex/personagens/forms.py), linha 73, a única regra específica é o máximo de cinco seleções. O método `save`, na linha 93, grava os nomes sem conferir saldo, calcular custo ou registrar compra. [models.py](../codex/personagens/models.py), linha 36, inicia o XP do personagem em zero.

Reprodução: um Guerreiro foi salvo com Feitiço antigo adicional, Forma selvagem adicional, Uso extra de habilidade, Multiclasse e Alquimista. São cinco escolhas de 70 XP, totalizando 350 XP, com `xp_atual = 0`. A ficha ficou **pendente de aprovação**; isso evita tratá-la automaticamente como aprovada, mas não valida o custo nem a legalidade da seleção.

Correção indicada: distinguir planejamento, aquisição e ativação. Se esta etapa for uma lista de desejos para avaliação, isso deve estar explícito na interface e separado dos talentos efetivamente adquiridos.

### 4. Os pré-requisitos não são aplicados

Prioridade: alta. Referência: páginas 18 a 20.

| Talento | Condição relevante do manual | Situação atual |
| --- | --- | --- |
| Arremesso extra | Já saber arremessar | Não é conferida |
| Flechas adicionais | Saber usar armas à distância | Não é conferida |
| Esferas de magia adicionais | Saber usar esferas | Não é conferida |
| Benefícios de patente | Pelo menos duas participações com o mesmo personagem e autorização do mestre | Aceito sem participações anteriores |
| Usar cajado | Conjurar magias de toque e ainda não saber usar cajado; uso incompatível com escudo | Não é conferida |
| Magia de outra classe | Ser conjurador | Não é conferida |
| Armas médias | Saber usar armas curtas | Não é conferida |
| Armas longas | Saber usar armas médias | Mago sem armas médias foi aceito |
| Usar esferas de magia | Ser conjurador e não ser Mago | Um Mago foi aceito com esse talento |
| Feitiço antigo adicional | Pertencer à classe Mago | Um Guerreiro foi aceito |
| Forma selvagem adicional | Pertencer à classe Druida | Um Guerreiro foi aceito |
| Uso extra de habilidade | Ter habilidade de classe de uso único | Não distingue, por exemplo, os Milagres ilimitados do Clérigo |
| Multiclasse | Ao menos dois talentos anteriores relacionados à nova classe, evolução interpretada e conversa prévia com a comissão | Aceito sem registrar esses elementos |

Parte das condições pode ser automatizada; a autorização e a evolução interpretativa precisam de decisão humana registrada. Não basta verificar se o nome do talento existe.

### 5. Os talentos são gravados, mas não completam as escolhas necessárias

Prioridade: alta. Referência: páginas 19 e 20.

- **Conjurar:** o manual concede uma magia e um foco, exceto cajado. Um Guerreiro com esse talento e sem magia é aceito. Ao tentar enviar uma magia, o formulário a rejeita porque as opções continuam dependendo somente da classe base.
- **Magia de outra classe:** um Bardo selecionando esse talento não consegue enviar Bola de Fogo; ela é rejeitada por estar fora da lista da classe base.
- **Magia extra da classe:** não há seleção adicional vinculada à compra. Atualmente a seleção inicial já pode ultrapassar a quantidade permitida sem qualquer talento.
- **Multiclasse:** não existe campo de segunda classe ou registro dos benefícios concedidos. O manual concede habilidade especial, dons e focos, exceto cajado, e permite comprar magias dessa lista. Ele não concede automaticamente as proficiências em armas da segunda classe.
- **Talentos adicionais de feitiço ou forma:** não existe registro de qual feitiço ou forma foi adquirido.

O campo `talentos_iniciais` é uma lista de nomes. Ele não registra custo pago, aquisição, autorização, escolha associada, origem do benefício ou estado ativo/inativo.

### 6. Compras repetidas e talentos ativos precisam ser representados

Prioridade: média. Referência: páginas 18 e 19.

O manual permite compras repetidas de talentos como Armadura adicional, Arremesso extra, Magia extra da classe, Recursos financeiros e Equipamento adicional. A tela possui uma única caixa por nome, sem controle de quantidade, e não separa talentos já adquiridos daqueles atualmente em uso.

A regra de cinco benefícios simultâneos não define completamente como contar múltiplas compras do mesmo talento. Essa interpretação precisa ser confirmada com a comissão antes de ser fixada no sistema.

## Escolhas especiais das classes

### 7. Falta a escolha inicial obrigatória do Mago

Prioridade: alta. Referência: página 14.

Além das quatro magias comuns, o Mago começa conhecendo apenas um feitiço antigo: Controle Mental, Necromancia ou Petrificação. A criação não oferece essa escolha e o modelo não possui um campo específico para guardá-la.

Essa escolha é diferente dos truques de Bárbaro, Bardo e Caçador. Nas páginas 10 a 12, eles escolhem qual efeito utilizar **no momento do uso**, compartilhando o uso único da habilidade. Não seria correto exigir que esses personagens escolhessem permanentemente apenas uma dessas técnicas na criação.

### 8. Outras informações ficam sem registro específico

Prioridade: média.

- **Druida, página 13:** o jogador escolhe afinidade, enquanto a comissão define três características e um defeito da Forma Selvagem. A forma não pode ser trocada livremente depois. Não há registro estruturado dessa definição.
- **Clérigo e Paladino, páginas 12 e 15:** precisam venerar uma divindade do cenário. Não há pergunta ou validação específica; a informação pode aparecer apenas na história, se o jogador a incluir.
- **Focos e opções de item inicial, páginas 10 a 15:** não são explicados nem registrados pela seleção de classe. O contexto da tela, em [views.py](../codex/personagens/views.py), linha 87, envia apenas nome, ID e imagem para os cartões.
- **Mago do Círculo do Fogo, página 7:** o benefício de armas curtas depende da arma escarlate e se perde ao sair da guilda. Para comprar armas médias, o manual ainda exige pagar armas curtas antes. Um benefício de guilda não deve ser confundido com um talento comprado.

Essas lacunas não provam que o jogador esteja interpretando incorretamente o personagem; mostram que a ficha digital não registra nem verifica essas condições.

## Edição pode deixar a ficha incoerente

### 9. Trocar classe conserva as magias e a aprovação antigas

Prioridade: alta. Referência: limites de classe nas páginas 10 a 15 e permanência das escolhas de magia na página 15.

[PersonagemUpdateForm](../codex/personagens/forms.py), linha 266, permite alterar a classe sem executar as regras da criação ou reconciliar magias e talentos. O `save` do modelo só trata a geração do slug.

Reprodução: um Mago aprovado, com quatro magias, foi alterado para Guerreiro. O formulário aceitou, manteve as quatro magias e conservou o status **Aprovado**.

O manual não especifica um fluxo digital completo de mudança da classe principal. A falha demonstrada é a conservação de uma ficha incoerente. Mudanças desse tipo precisam de política da comissão, revalidação das capacidades e avaliação da aprovação.

## O que já está correto

- As nove classes correspondem ao capítulo 6.
- As listas de magias das cinco classes conjuradoras correspondem ao manual.
- Druida recebe três magias fixas e Paladino recebe duas automaticamente.
- Os 25 custos de talentos cadastrados nas constantes correspondem às páginas 18 a 20. O problema é que a compra não os utiliza.
- O servidor rejeita um talento inexistente e mais de cinco seleções.
- A criação exige classe, guilda, nome, descrição e concordância.
- Fichas novas começam pendentes de aprovação.

## Consistência entre Wiki e criação

A Wiki pública e o editor consultam `WikiEntry`, enquanto a criação consulta `TALENTOS_WIKI` e `MAGIAS_POR_CLASSE`, derivados das constantes Python. Alterar uma descrição, um custo ou adicionar conteúdo pelo admin da Wiki não muda automaticamente as opções e validações de personagens.

Essa separação está documentada no projeto e não é, isoladamente, uma violação do manual. Para sincronizar as áreas, é necessária uma fonte estruturada de regras, distinguindo apresentação, requisitos e efeitos. Não é seguro transformar frases livres da Wiki diretamente em regras de aquisição.

## Ordem indicada para corrigir

1. Corrigir a validação das caixas de magia e exigir as quantidades iniciais de cada classe no servidor.
2. Definir a seleção de talentos como planejamento ou compra; na compra, validar XP, requisitos e autorizações.
3. Registrar as escolhas ligadas aos talentos e às classes, principalmente feitiço antigo do Mago, Forma Selvagem, magia aprendida e segunda classe.
4. Revalidar edição de classe, magias e talentos, com política explícita para fichas já aprovadas.
5. Exibir capacidades da classe, custo, requisitos e efeitos antes da confirmação das escolhas.
6. Separar histórico de aquisições, quantidades e benefícios ativos, preservando as fichas existentes para revisão.

O manual fala em XP do jogador para melhorar personagens, mas o sistema guarda o saldo no personagem. A origem e o uso do saldo entre personagens, os critérios de troca de talentos e a contagem de compras repetidas no limite de cinco precisam de definição da comissão.

## Casos reproduzidos

| Cenário | Resultado observado |
| --- | --- |
| Bardo com 1, 3 e 6 magias, em três testes | Todos aceitos pelo servidor |
| Clérigo com 1, 3 e 6 magias, em três testes | Todos aceitos pelo servidor |
| Mago com 1, 4 e 8 magias, em três testes | Todos aceitos pelo servidor |
| Druida sem seleção manual de magias | Recebeu as três fixas |
| Paladino sem seleção manual de magias | Recebeu as duas fixas |
| Guerreiro com cinco talentos de 70 XP | Salvo com XP zero e aprovação pendente |
| Benefícios de patente sem participações anteriores | Aceito |
| Guerreiro com Conjurar, sem magia | Salvo sem magia |
| Guerreiro com Conjurar tentando escolher Barreira Mágica | Magia rejeitada |
| Bardo com Magia de outra classe tentando escolher Bola de Fogo | Magia rejeitada |
| Mago com Armas longas sem Armas médias | Aceito |
| Mago com Usar esferas de magia | Aceito |
| Seis talentos distintos | Rejeitados |
| Talento inexistente | Rejeitado |
| Mago aprovado alterado para Guerreiro | Conservou magias e aprovação |
| Navegador: Bardo com três magias e depois com seis | Bloqueou com três; avançou com seis |

Total: 21 cenários de formulário/modelo e um cenário de navegador. A conferência adicional comparou os 25 custos e as cinco listas de magias com o PDF.
