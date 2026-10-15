# Auditoria do sistema — Manual LARP 3.3 e Contos da Cachoeira

> **Atualização após a auditoria:** os problemas confirmados F01–F09 e as lacunas de conteúdo C01–C03 foram tratados. Consulte o [registro das correções e validações](correcoes-manual-cenario-2026-10-15.md). O texto e as evidências abaixo preservam o diagnóstico anterior às correções. Divergências entre os PDFs e ampliações funcionais continuam identificadas separadamente.

Data: 15/10/2026. Esta é uma nova análise do código e do conteúdo atuais, depois dos ajustes de criação de personagens e talentos.

**Resultado:** a criação básica está mais próxima do manual, mas ainda existem falhas na evolução dos personagens, no registro de moeda e na integridade do XP. As informações de guildas e parte da wiki também precisam de revisão. Os dois PDFs contêm pontos que exigem decisão da comissão antes de virar regra do sistema.

Esta análise não alterou regras, fichas ou saldos reais e não publicou mudanças. As reproduções que exigiram gravação usaram exclusivamente SQLite em memória e usuários fictícios.

## Fontes, escopo e método

- [Manual LARP — 3.3](<Manual LARP - 3.3.pdf>): 25 páginas.
- [Cenário — Contos da Cachoeira](<Cenário_ Contos da Cachoeira.pdf>): 23 páginas.
- Código de personagens, talentos, contas, XP, eventos, guildas e wiki; modelos, formulários, validações e páginas relacionadas.
- Leitura integral do texto dos PDFs e conferência visual de páginas importantes sobre classes, talentos e guildas.
- 109 testes existentes passaram em configuração isolada; a checagem do Django não apontou problemas.
- 15 casos de auditoria foram registrados, incluindo falhas reproduzidas, limitações de registro e verificações positivas. O teste de XP simula uma intercalação de operações concorrentes; não é um teste de carga.
- Consulta somente de leitura ao banco conectado: conteúdo público da wiki, existência de guildas e uma contagem agregada de diferenças entre saldo de XP e histórico. Nenhuma ficha pessoal ou saldo individual consta neste relatório.

**As páginas citadas são as posições no arquivo PDF, contando a primeira página como 1.** A versão de referência é o conjunto de arquivos fornecido nesta solicitação; não foi presumida a existência de regras posteriores da comissão.

Evidência estruturada: [resultados e verificações](auditoria-sistema-manual-cenario-2026-10-15-evidencias.json).

## Prioridades

| ID | Prioridade | Constatação | Referência principal |
| --- | --- | --- | --- |
| F01 | Alta | Salvar dados pessoais pode sobrescrever XP alterado por uma compra concorrente | Manual p. 18; integridade do saldo |
| F02 | Alta | Multiclasse pode impedir a ativação de talentos anteriormente adquiridos | Manual pp. 18–20 |
| F03 | Alta | Multiclasse não registra de forma completa as escolhas da habilidade da segunda classe | Manual pp. 12–15 e 19–20 |
| F04 | Alta | Forma Selvagem já definida pode ser alterada; uma aprovação repetida grava detalhes antes de ser recusada | Manual pp. 13 e 19 |
| F05 | Média | O saldo de ouro não aceita 1 DP / 0,5 DO | Manual p. 20 |
| F06 | Média | Conjurar aceita uma arma como foco | Manual pp. 15 e 19 |
| F07 | Média | Mercenário pode receber Benefícios de patente sem pertencer a uma guilda | Manual pp. 10 e 18 |
| F08 | Média | Editor da wiki e regras de compra usam catálogos independentes | Consistência das regras publicadas |
| F09 | Baixa | Divindade de Clérigo/Paladino é validada apenas como texto preenchido | Manual pp. 12 e 15; Cenário pp. 11–14 |
| C01 | Média | Páginas de guildas omitem benefícios de jogo e misturam contextos de marcas | Manual pp. 6–10; Cenário pp. 6–11 |
| C02 | Média | Resumos de focos e itens omitem regras relevantes | Manual pp. 13–15 e 21 |

“Alta” indica risco de saldo incorreto, bloqueio de evolução válida ou alteração de uma definição que deveria permanecer registrada. “Média” indica inconsistência funcional ou informação capaz de induzir uma decisão errada. A prioridade não significa que houve dano em contas reais.

## Falhas e limitações reproduzidas

### F01 — Gravação de cadastro pode restaurar XP já gasto

O XP está corretamente centralizado no jogador, e a aprovação de uma compra bloqueia o saldo durante o débito. Entretanto, o formulário de dados pessoais salva o objeto `Profile` inteiro, incluindo o XP que ele tinha quando foi carregado.

Reprodução da intercalação:

1. Carregar o perfil com 2.000 XP para salvar os dados pessoais.
2. Aprovar uma compra de Armadura adicional por 25 XP: saldo passa a 1.975.
3. Salvar aquele objeto de perfil, ainda com 2.000 XP em memória.
4. O saldo volta a 2.000, mas o débito de −25 continua no histórico.

Isso depende de requisições concorrentes/intercaladas. Não significa que apenas deixar a tela de cadastro aberta e salvar depois sempre cause o problema: o objeto é carregado pelo servidor durante a requisição.

Código: `codex/accounts/forms.py:71–90`, especialmente `profile.save()`. A compra usa o fluxo protegido em `codex/personagens/rules.py:159–182`.

Correção recomendada: salvar apenas os campos pessoais nesse formulário e auditar outros caminhos que salvam `Profile` inteiro. Manter alterações de XP exclusivamente no serviço de saldo, com histórico e controle de concorrência.

**Verificação real:** a consulta agregada encontrou zero perfis com saldo diferente da soma dos movimentos na data da auditoria. A falha foi reproduzida em dados fictícios; não foi constatada corrupção atual de saldos reais.

### F02 — Multiclasse invalida combinações de talentos já comprados

Foram reproduzidos dois casos com apenas três compras selecionadas, abaixo do limite de cinco:

- Guerreiro adquire Conjurar, uma magia adicional e Multiclasse Mago. Ao ativar os três, recebe “O personagem já é conjurador.”
- Bardo adquire Bola de Fogo e Raio Elétrico como magias de outra classe e depois Multiclasse Mago. Ao ativar os três, recebe “Escolha uma magia válida para este talento.”

O validador de ativação reaplica condições de aquisição considerando a segunda classe. Assim, Conjurar passa a ser considerado redundante e uma magia comprada legitimamente como estrangeira passa a ser recusada por agora pertencer à segunda classe.

O manual mantém os talentos no personagem e descreve Multiclasse como evolução após talentos relacionados, não como motivo para invalidar compras anteriores (pp. 18–20).

Código: `codex/personagens/rules.py:105`, `:119–125` e `:186–195`.

Correção recomendada: separar condições para adquirir uma compra das condições para mantê-la ativa e preservar a origem das magias adquiridas. A falha atual bloqueia a seleção; a operação atômica preserva a seleção anterior quando a validação falha.

### F03 — Multiclasse não consolida escolhas da segunda habilidade

Multiclasse concede a habilidade especial, os dons e os focos da segunda classe, exceto cajado. Não concede automaticamente suas outras proficiências nem toda a lista de magias (Manual p. 20).

No caso Guerreiro → Mago, a compra foi aprovada sem registrar uma escolha estruturada de feitiço antigo. Tentar colocar Necromancia no campo de magia da compra de Multiclasse foi recusado com “Este talento não concede uma magia.” A ficha principal continua sem feitiço antigo e sem uma apresentação consolidada das capacidades da segunda classe.

Há o mesmo tipo de lacuna de registro para uma Forma Selvagem inicial da segunda classe Druida e para informações religiosas necessárias às classes sagradas. Um texto livre em “detalhes” permite anotar decisões, mas não garante que as escolhas necessárias estejam presentes nem as integra à ficha.

Código: `codex/personagens/rules.py:75–76` e `:133–139`; campos de `CompraTalento` em `codex/personagens/models.py:81–96`.

Correção recomendada: exigir as escolhas específicas da segunda habilidade durante a análise da comissão e mostrar as capacidades efetivas da ficha conforme os talentos ativos. Preservar as restrições expressas do manual: não distribuir armas, armaduras ou todas as magias iniciais da segunda classe.

### F04 — Forma Selvagem não permanece fixada após a definição

O Manual p. 13 determina três características e um defeito definidos pela comissão e informa que a forma não pode ser mudada depois. Novas formas são obtidas por talento próprio (p. 19).

Foram confirmados dois caminhos administrativos:

- O formulário de edição permite ao administrador mudar a forma inicial de um Druida já aprovado. A aprovação permanece como “Aprovado”, sem nova análise ou versão da forma anterior.
- Reenviar a aprovação de uma compra de Forma Selvagem já aprovada altera os detalhes. Só depois a operação informa que a solicitação já foi analisada. O novo texto fica gravado apesar da recusa da aprovação repetida.

Código: `codex/personagens/forms.py:337` e `:360–368`; `codex/personagens/views.py:173–176` grava os detalhes antes de chamar a aprovação protegida.

Correção recomendada: fixar a definição aprovada, oferecer correções administrativas explícitas com histórico e gravar a definição da comissão dentro da mesma transação que verifica o estado e aprova a compra. Não interpretar automaticamente todo texto de poderes: o manual permite características sugeridas pelo mestre.

Esses caminhos exigem acesso administrativo; não foi reproduzida alteração da forma por um jogador comum.

### F05 — A moeda não representa prata ou valores fracionados em ouro

O Manual p. 20 estabelece 1 DO = 2 DP. Amuleto de proteção espiritual e Veneno custam 1,5 DO; Poção da Salamandra custa 3,5 DO.

O campo persistido de ouro e o formulário de saldo aceitam apenas inteiros. A tentativa de informar `0.5` foi recusada com “Informe um número inteiro.” Portanto, não é possível registrar corretamente um saldo de 1 DP nessa unidade.

Código: `codex/personagens/models.py:43`; `codex/core/forms.py:31`.

Correção recomendada: armazenar a menor unidade, DP, como inteiro e converter na interface, ou usar um decimal com precisão definida em todo o fluxo. A migração precisa preservar os saldos existentes. Os preços dos 16 itens conferidos estão corretos; o defeito é na representação do saldo.

### F06 — Arma aceita como foco de Conjurar

Um Guerreiro solicitou Conjurar com Exorcismo e foco “Espada”. O formulário aceitou e a compra pôde ser aprovada e ativada.

O Manual p. 15 proíbe armas como focos, e p. 19 limita Conjurar a um único foco, que não pode ser cajado. O sistema verifica a presença de texto e a palavra “cajado”, mas não a natureza do objeto.

Código: `codex/personagens/rules.py:126–127`.

Correção recomendada: registrar o tipo de foco e sua descrição, recusar categorias expressamente proibidas e manter avaliação da comissão para objetos personalizados. Uma lista fechada de nomes não cobriria todos os focos permitidos.

### F07 — Mercenário recebe Benefícios de patente

Com duas participações passadas confirmadas, um personagem marcado como Mercenário pôde ter Benefícios de patente aprovado. A validação considera as participações, mas não o vínculo com uma guilda.

O Manual p. 10 define mercenários como pessoas sem guilda, que não formam um grupo único nem comandam grupos. Benefícios de patente depende de destaque na própria guilda e autorização do mestre (p. 18).

Código: `codex/personagens/rules.py:113–116`; categoria de Mercenários em `codex/personagens/consts.py:22–35`.

Correção recomendada: exigir uma guilda real para a regra comum de patente, registrar a guilda e os benefícios específicos concedidos e tratar exceções expressamente pela comissão. A opção técnica de ID 7 pode ser preservada, mas a apresentação deveria esclarecer “sem guilda — mercenário”.

### F08 — O editor da wiki não alimenta as regras de criação e compra

Em banco fictício, alterar Armadura adicional para 999 XP pelo formulário do editor fez a wiki publicar 999 XP, enquanto uma nova solicitação continuou registrada por 25 XP.

A wiki lê `WikiEntry` do banco; a criação e a compra importam constantes Python. O mesmo desacoplamento existe para as listas de magias por classe e a possibilidade de repetir talentos. Criar uma classe ou talento na wiki também não o torna automaticamente uma opção mecânica na ficha.

Código: `codex/wiki/forms.py:9–10`, `:35–38`; `codex/wiki/views.py:9–10`; `codex/personagens/forms.py:396` e `:428`; `codex/personagens/rules.py:11–20`; `codex/personagens/consts.py:73–95`.

Correção recomendada: definir uma fonte comum e versionada para as regras mecânicas. Separar no editor texto explicativo de alteração mecânica, com efeito claro sobre novas compras e preservação do custo histórico das antigas.

**Estado atual:** os campos de conteúdo público consultados coincidem com as constantes. Esta é uma falha de integração reproduzida; não foi encontrada uma divergência de preços já publicada no banco atual.

### F09 — Divindade preenchida não significa divindade válida

Um Clérigo com o texto “Nenhuma; sou ateu” passou pela validação de base com exigência de comissão. A regra verifica apenas se há conteúdo no campo.

O Manual p. 12 veda Clérigos ateus e exige uma divindade do cenário; a identidade sagrada também é parte de Paladino (p. 15). O Cenário pp. 11–14 oferece exemplos de divindades, sem apresentar a lista como exaustiva.

Código: `codex/personagens/rules.py:52–53`.

Recomendação: oferecer as divindades conhecidas e uma opção personalizada sujeita à avaliação, deixando explícita a confirmação religiosa na aprovação. Não transformar os exemplos do caderno em um catálogo fechado obrigatório. A compatibilidade narrativa continua sendo decisão humana, não algo confiável de deduzir apenas pela palavra digitada.

## Conteúdo de guildas e cenário

### C01 — Benefícios reais devem substituir os resumos genéricos

As páginas públicas usam `codex/core/constants/guildas.py`. Vários campos descrevem uma característica narrativa, mas não explicam o benefício de jogo.

| Grupo | Conteúdo atual | Regra que precisa aparecer | Fonte |
| --- | --- | --- | --- |
| Artistas da Revolução | Nome “Compartilhar Conhecimento” | Pergaminho de magia compartilhada; condições de posse, substituição e caso sem conjurador | Manual pp. 6–7 |
| Círculo do Fogo | Capacidade de combate e preparo militar | Lâmina Escarlate; um ataque flamejante, recarga e condição de armas curtas para Mago | Manual p. 7 |
| Floresta do Sol | Conexão com natureza e resistência espiritual | Proteção do Sol equivalente a amuleto espiritual, com condições de céu aberto, dia e sombra | Manual p. 8 |
| Irmandade das Tavernas | Contatos, espionagem e submundo | Barganha dos Espertos; troca de itens não usados, crédito e ausência de troco | Manual p. 8 |
| Rasga-Mortalhas | Morte, loucura e conhecimento proibido | Contatos Espirituais; uma pergunta de sim/não por sessão | Manual p. 9 |
| Sociedade Zaori | Conhecimento mágico e profecias | Visões Proféticas; pergaminho reservado aos membros, mantido na Zona Neutra | Manual pp. 9–10 |
| Mercenários | Liberdade, sem vínculo | Não constituem uma guilda coletiva; também existe a desvantagem Desconfiança | Manual p. 10 |

Outras correções de contexto:

- **Zaori:** o site apresenta perda de memórias como marca geral. O Manual p. 10 define Cegueira egoísta como marca de pecado/traição; o Cenário p. 10 descreve apagar memórias como condição de uma saída autorizada. São situações diferentes e ambas podem ser representadas, sem substituir uma pela outra.
- **Tavernas:** o texto atual fala genericamente em perder “as mãos”. O Manual pp. 8–9 começa pela perda de uso de uma mão; as regras gerais de marcas permitem acumulação (p. 6).
- **Rasga-Mortalhas:** Lunna aparece entre as divindades no Manual p. 9 e está ausente do resumo do site, que segue a lista mais curta do Cenário p. 10. A descrição da loucura também deve distinguir condição pessoal e agravamento por traição.
- **Floresta:** “Doença do Sol” no site segue a descrição do Cenário p. 9. A diferença para Febre Solar no Manual p. 8 precisa de definição da comissão, conforme a seção seguinte.

### C02 — Focos e itens estão resumidos além do necessário

- O resumo de Druida na criação omite cristais e amuletos ligados à natureza, permitidos no Manual p. 13.
- O resumo de Mago omite grimórios, permitidos no Manual p. 14, e inclui esferas no texto de focos. Saber usar esferas não substitui a explicação dos focos de conjuração.
- A página de detalhe de classe não apresenta uma seção própria de focos. Referências: `codex/personagens/rules.py:29–35` e `codex/wiki/templates/wiki/classe_detalhe.html`.
- Sangue de Dragão na wiki não informa o teto de 10 PV, o encerramento ao fim do combate, os 10 segundos da morte nem que apenas Água Primordial ressuscita esse morto (Manual p. 21). Isso muda decisões de jogo, não apenas a extensão do texto. Referência: `codex/wiki/constants/itens.py:142–150`.
- Laço da Verdade não informa que omissões continuam permitidas e que o efeito é mental (Manual p. 21). Referência: `codex/wiki/constants/itens.py:156–162`.

Recomendação: manter resumos nos cartões, mas disponibilizar as condições completas nos detalhes. Revisar as regras de combate, morte, veneno e descanso que hoje não estão integralmente representadas pelas quatro entradas gerais de regras.

### C03 — Falta uma área de referência do mundo

Não foi encontrada publicação equivalente ao caderno para cronologia, divindades, lugares, planos e organizações históricas. A wiki tem categorias de regras, classes, talentos, magias e itens, mas não uma estrutura própria para o cenário (`codex/wiki/models.py:5–6`).

As lacunas de referência se concentram na história do Cenário pp. 1–5, divindades e lugares pp. 11–18 e organizações do passado pp. 18–23. Conteúdo livre poderia ser cadastrado nas categorias atuais, mas essa base não foi encontrada no conteúdo publicado consultado.

É uma lacuna editorial, não uma exigência para transformar toda a narrativa em validação automática da criação.

## Pontos dos PDFs que precisam de decisão da comissão

### Zona Neutra: proteção da Serpente e posição dos guardiões

O Cenário p. 5 afirma que até um membro da Serpente está protegido na Zona Neutra. O pacto, no mesmo caderno p. 6, nega asilo e proteção à Serpente e a seus fiéis. O Manual p. 5 também contém essa exclusão.

Existe ainda uma diferença sobre o guardião: o Cenário p. 5 admite preferências e ajuda maior a um lado, enquanto o Manual p. 5 proíbe tomar partido. A comissão deve esclarecer o alcance dessa proibição e qual texto é vigente.

Não é correto criar uma validação automática alegando que os documentos são inteiramente consistentes nesse ponto.

### Floresta do Sol: Febre Solar e Doença do Sol

- Manual p. 8: redução de 1 no PV máximo sob o sol, até perdão.
- Cenário p. 9: doença progressiva e incurável que pode levar à morte sob o sol.

O Manual p. 6 admite punições mais severas inventadas pelo mestre para pecados graves. Portanto, pode haver diferença entre uma marca comum e uma consequência narrativa de deserção, mas isso não está suficientemente definido para o site escolher sozinho uma mecânica única.

### Lacunas editoriais do caderno

O texto da 4ª Era repete a descrição da 3ª Era no Cenário p. 2. O título da 9ª sessão aparece sem desenvolvimento na p. 5. Essas lacunas são dos documentos e não devem ser preenchidas com fatos inventados pelo sistema.

### Coisas que não são divergências

- Mãe Natureza e Mãe Elemental são nomes da mesma entidade, conforme o Cenário p. 13.
- Artistas da Revolução são explicitamente apresentados como a guilda mais nova no Manual p. 6. Sua ausência no caderno não justifica removê-los.
- As organizações nas pp. 18–23 do Cenário estão sob o título “Organizações do Passado”. Não devem virar automaticamente escolhas atuais de guilda para jogadores.
- As variações Luna/Lunna aparecem nos próprios documentos. Padronização editorial não deve ser confundida com proibição mecânica de uma divindade.

## Cobertura que ainda depende de registro manual

| Área | Estado atual | Consequência prática |
| --- | --- | --- |
| Entrada e saída de guilda | A troca pelo jogador volta a ficha para pendente; não há histórico próprio de autorização, deserção, marcas e perdão | A aprovação existe, mas não há trilha específica do pacto e de suas consequências; Manual p. 6 e Cenário pp. 6–11 |
| Registros administrativos de guilda | A consulta encontrou zero registros `Guilda`; os sete cartões públicos continuam aparecendo por conteúdo de reserva | Áreas privadas, notícias e sincronização de membros dependem desses cadastros e não estão disponíveis apenas com os cartões públicos |
| Recompensas de sessão | Presença e saldo podem ser ajustados; não há memória estruturada de cada critério de XP e ouro | A comissão precisa calcular e registrar a recompensa; Manual pp. 18 e 20 |
| Recursos financeiros e renda inicial | O talento e as descrições existem; não há cálculo consolidado automático por ficha/sessão | Conferir manualmente +3 DO por compra ativa e particularidades de Bardo/Ladino/NPC; Manual pp. 11, 13, 19–20 |
| Itens e equipamento | A ficha informa a regra da classe, mas não possui inventário completo ou seleção persistida dos itens iniciais | Não é possível conferir automaticamente carga, cajado/escudo, limites de flechas/esferas e consumo de itens |
| Missões | Não foi encontrado módulo estruturado equivalente às regras de missões | Estrelas, exclusividade, prova de conclusão e recompensa continuam na condução presencial; Manual pp. 17–18 |

Na troca de guilda reproduzida, o jogador passou de Zaori para Círculo e a ficha ficou **pendente**, como esperado. Não foi demonstrada troca aprovada unilateralmente por um jogador. O problema é a falta de registro das consequências e autorizações, não a ausência total de revisão.

Referências de guildas: `codex/guildas/views.py:64–118` e `:140–175`; `codex/guildas/signals.py:10–18`. Os controles de acesso às áreas privadas existem; a ausência de cadastros não demonstra vazamento de segredos.

Essas lacunas não provam que a comissão esteja premiando ou conduzindo as sessões incorretamente. Indicam regras que o sistema ainda não acompanha de ponta a ponta.

## O que foi conferido e está correto

- As nove classes do Manual pp. 10–15 estão disponíveis.
- Bardo e Clérigo exigem exatamente três magias iniciais; Mago exige quatro. Selecionar toda a lista foi recusado nos casos de auditoria.
- Druida possui as três magias iniciais e Paladino as duas previstas; as listas das cinco classes conjuradoras coincidem com a referência conferida.
- Mago exige a escolha inicial de um dos três feitiços antigos; Druida exige afinidade e definição da comissão na aprovação.
- Os custos dos 25 talentos coincidem com o Manual pp. 18–20; os preços dos 16 itens conferidos coincidem com p. 20.
- Talentos são solicitações sujeitas à comissão; a compra é individual por personagem e o XP é debitado do jogador na aprovação.
- O limite de cinco compras ativas está aplicado. Cinco compras repetidas de Armadura adicional foram aceitas e seis recusadas.
- A contagem de cada compra repetida como uma vaga e o saldo compartilhado entre personagens seguem as decisões expressas do responsável pelo site nesta conversa. Não são apresentados como uma redação inequívoca do PDF sobre contagem de repetições.
- As magias iniciais não podem ser livremente trocadas por jogadores depois da criação. Há caminho administrativo de revisão de fichas antigas.
- A exigência de comprar Armas curtas antes de Armas médias não é substituída pelo benefício condicional do Mago do Círculo do Fogo, conforme Manual p. 7.
- Identificação por nome, imagem da classe ou foto é uma preferência de apresentação do site; não acrescenta poderes por espécie ou aparência. O Manual p. 5 trata espécies como escolha narrativa/visual.

No banco consultado havia 67 entradas públicas: 9 classes, 25 talentos, 12 magias, 16 itens, 4 regras e 1 conjunto de regras gerais de magia. Os campos de conteúdo conferidos não divergiam das constantes do código.

## Sequência recomendada de correção

1. Impedir a sobrescrita de XP por outros formulários e preservar a correspondência com o histórico.
2. Separar aquisição de ativação de talentos; corrigir os casos de Multiclasse e registrar suas escolhas.
3. Fixar Formas Selvagens aprovadas e tornar atômica a gravação dos detalhes da comissão.
4. Adequar a moeda a DP e revisar foco de Conjurar e patente de Mercenário.
5. Definir a relação entre editor da wiki e catálogo mecânico antes de novas alterações de regras no admin.
6. Revisar benefícios, marcas, focos e detalhes dos itens; cadastrar as guildas administrativas e organizar o conteúdo de cenário.
7. Incorporar decisões da comissão sobre os conflitos dos PDFs e, se desejado, ampliar inventário, recompensas e missões.

## Limites da conclusão

Esta auditoria verifica a aderência às fontes fornecidas e aos comportamentos de código reproduzidos. Não é certificação de segurança, teste de carga ou observação de uma sessão presencial. Os 109 testes existentes passaram, mas não cobrem todos os casos acima. As falhas de gravação foram reproduzidas em SQLite; não foi executado teste concorrente de carga contra o PostgreSQL real. Nenhum resultado depende de modificar dados de jogadores ou de publicar uma nova versão.
