# Plano de remodelagem e revisão do Codex da Cachoeira

Este documento será nosso roteiro de trabalho. A ideia é revisar o sistema por etapas, corrigindo erros, reorganizando permissões e remodelando o layout sem tentar mudar tudo ao mesmo tempo.

## Como vamos trabalhar

Para cada etapa, seguiremos este ciclo:

1. Confirmar o objetivo visual e funcional da etapa.
2. Conferir o comportamento atual no código.
3. Listar os problemas encontrados.
4. Implementar uma alteração pequena e coerente.
5. Testar como visitante, usuário comum, admin e superadmin.
6. Confirmar com você antes de avançar.

Uma etapa só será considerada concluída quando a tela estiver funcionando, responsiva e protegida pelas permissões corretas.

---

## 1. Mapa atual do sistema

### `core`

É a base compartilhada do site.

- Possui o modelo `Profile`, ligado ao usuário do Django.
- Guarda o papel atual do usuário: `COMMON` ou `ADMIN`.
- Possui as configurações globais do layout: cabeçalho, rodapé e cores.
- Possui as configurações editáveis da Home.
- Possui seções extras que podem ser exibidas na Home.
- Possui eventos LARP e inscrições.
- Contém o template base usado pelas outras páginas.

### `dashboard`

Controla a Home e os painéis de usuário.

- Exibe a Home pública.
- Personaliza a Home conforme o usuário está logado e seu papel.
- Exibe o painel do usuário comum.
- Exibe o painel administrativo.
- Permite ao admin editar partes da Home, cores, usuários, personagens e eventos.

### `accounts`

Controla a autenticação e os dados da conta.

- Login.
- Registro de novos usuários.
- Logout.
- Página de dados pessoais.
- Criação automática de um `Profile` para cada usuário registrado.

### `personagens`

Controla os personagens dos jogadores.

- Lista os personagens do usuário logado.
- Cria personagem.
- Exibe detalhes do próprio personagem.
- Edita o próprio personagem.
- Armazena nome, história, aparência, objetivos, personalidade, guilda, classe, magias, talentos, status, aprovação, XP e ouro.

### `guildas`

Exibe guildas, membros e notícias associadas.

- Possui páginas públicas de guildas.
- Usa imagens e templates específicos para cada guilda.
- Recalcula alguns dados de guildas quando personagens são alterados.

### `wiki`

Exibe o conteúdo de regras do jogo.

- Regras.
- Classes.
- Itens.
- Talentos.
- Magias.
- Páginas de listagem e detalhe.

Atualmente, o conteúdo está em arquivos de constantes Python. Isso significa que a Wiki é pública e seu conteúdo só é alterado por código, não por uma tela do sistema.

### `docs`

Guarda documentação do projeto, manuais e checklists antigos. A documentação existente será preservada, mas este arquivo passa a ser o roteiro principal da remodelagem visual e funcional.

---

## 2. Matriz inicial de permissões

Esta é a proposta de partida. Precisamos confirmar os pontos marcados como dúvida antes de fechar a implementação definitiva.

| Área ou ação | Visitante | Usuário comum | Admin | Superadmin |
|---|---:|---:|---:|---:|
| Ver Home pública | Sim | Sim | Sim | Sim |
| Ver Wiki pública | Sim* | Sim* | Sim | Sim |
| Ver guildas públicas | Sim | Sim | Sim | Sim |
| Ver LARPs públicos | Sim | Sim | Sim | Sim |
| Fazer login e registro | Sim | Sim | Sim | Sim |
| Ver a própria conta | Não | Sim | Sim | Sim |
| Criar personagens | Não | Sim | Sim, se permitido | Sim |
| Editar os próprios personagens | Não | Sim | Sim, se permitido | Sim |
| Ver personagens de outros usuários | Não | Não* | Sim | Sim |
| Inscrever personagem em LARP | Não | Sim | Não, conforme regra atual | Sim, conforme regra definida |
| Acessar painel do usuário | Não | Sim | Sim | Sim |
| Acessar painel administrativo | Não | Não | Sim | Sim |
| Gerenciar usuários comuns | Não | Não | Sim | Sim |
| Promover ou rebaixar admins | Não | Não | Não* | Sim |
| Editar layout e conteúdo da Home | Não | Não | Sim | Sim |
| Criar e gerenciar eventos LARP | Não | Não | Sim | Sim |
| Editar status, aprovação, XP e ouro de personagens | Não | Não | Sim | Sim |
| Alterar conteúdo da Wiki | Não | Não | Não* | Sim* |
| Acessar o Django Admin | Não | Não | Conforme configuração | Sim |

`*` Ponto que precisa de confirmação.

### Situação técnica atual das permissões

- Usuário comum é identificado por `Profile.role = COMMON`.
- Admin é identificado por `Profile.role = ADMIN`.
- Superadmin é identificado por `User.is_superuser`.
- Algumas áreas usam `Profile.role` e `is_superuser`.
- A área de guildas usa `is_staff` em alguns pontos, o que pode gerar diferença entre o papel exibido e o acesso real.
- Ainda não existe uma camada única de permissões para todas as áreas.

### Correção prevista

Criar uma regra central de acesso, com funções ou decorators reutilizáveis, por exemplo:

- `is_common_user`
- `is_admin`
- `is_superadmin`
- `can_manage_characters`
- `can_manage_home`
- `can_manage_wiki`

O template pode esconder botões, mas a segurança precisa existir também na view. Assim, uma pessoa não consegue acessar uma ação apenas digitando a URL manualmente.

---

## 3. Fase 0 — Preparação e diagnóstico

### O que esta fase faz

Cria uma base segura para comparar o sistema antes e depois da remodelagem.

### Tarefas

- Fazer um inventário de todas as URLs.
- Listar cada template usado por cada URL.
- Conferir quais páginas funcionam sem login.
- Conferir quais páginas funcionam para cada papel.
- Rodar as verificações do Django.
- Confirmar banco, migrações, arquivos estáticos e mídia.
- Criar testes mínimos para autenticação e permissões.
- Corrigir problemas de codificação de textos, como acentos exibidos de forma quebrada.
- Registrar problemas visuais encontrados em desktop e celular.

### Resultado esperado

Ter uma lista real de erros antes de alterar o layout e um ponto de comparação para confirmar que a remodelagem não quebrou funcionalidades existentes.

### Dúvidas desta fase

- O banco de desenvolvimento continuará sendo PostgreSQL?
- Existe um banco de dados com informações reais que não pode ser alterado?
- Você quer manter o conteúdo atual ou podemos substituir textos provisórios da Home?

---

## 4. Fase 1 — Home e identidade visual

Esta será a primeira remodelagem efetiva, conforme combinado.

### O que a Home faz hoje

- Mostra banner, título, subtítulo e imagem configuráveis.
- Mostra status da sessão e papel do usuário.
- Mostra atalhos para LARPs, guildas, personagens e admin.
- Mostra menus diferentes para visitante, usuário comum e admin.
- Mostra uma seção de texto configurável.
- Mostra seções extras configuráveis.
- Usa o template base com cabeçalho, rodapé, tema e mensagens.

### O que será revisado

- Hierarquia visual da Home.
- Cabeçalho e navegação desktop/mobile.
- Banner e chamada principal.
- Cards e atalhos.
- Conteúdo exibido para visitante.
- Conteúdo exibido para usuário comum.
- Conteúdo exibido para admin.
- Responsividade em telas pequenas.
- Contraste, foco de teclado, textos alternativos e acessibilidade.
- Estados vazios, mensagens de erro e mensagens de sucesso.
- Tema visual e consistência entre páginas.
- Dependência atual de Tailwind/DaisyUI carregados por CDN.

### Proposta de estrutura visual

1. Cabeçalho com marca, navegação principal e área da conta.
2. Hero com mensagem clara sobre o Codex e ação principal.
3. Atalhos de acordo com o papel do usuário.
4. Bloco de próximos eventos ou conteúdo em destaque.
5. Bloco de apresentação do universo.
6. Rodapé com links úteis e informações institucionais.

### Critérios de aceite

- A Home funciona para visitante, usuário comum, admin e superadmin.
- Nenhum botão aparece para uma ação que o usuário não pode executar.
- Todos os links levam para uma página existente ou para uma tela planejada.
- O layout funciona em celular, tablet e desktop.
- O cabeçalho mobile não fica preso ou sobreposto ao conteúdo.
- O conteúdo editável pelo admin continua editável.
- Não há texto cortado, contraste insuficiente ou imagem sem descrição.

### Dúvidas da Home

- Qual é a mensagem principal que a Home deve passar?
- A Home será mais informativa sobre o universo ou mais operacional para jogadores?
- Quais itens precisam aparecer no menu principal?
- Visitantes devem ver LARPs e Wiki completos ou apenas uma apresentação?
- Admin e superadmin terão a mesma Home ou painéis diferentes?
- Você já possui logo, paleta de cores, fontes ou referências visuais?

---

## 5. Fase 2 — Permissões e visibilidade

Esta fase define com segurança o que cada perfil pode ver e fazer. Ela deve ser confirmada antes de remodelar os fluxos internos.

### O que será implementado

- Fechar a matriz de permissões.
- Separar claramente visitante, usuário comum, admin e superadmin.
- Centralizar as verificações de papel.
- Corrigir diferenças entre `Profile.role`, `is_staff` e `is_superuser`.
- Proteger URLs e ações POST.
- Definir se admins podem gerenciar outros admins.
- Definir quais dados de personagens são públicos.
- Definir quais dados pessoais são privados.
- Definir a política de acesso ao Django Admin.
- Criar testes para acesso permitido e acesso negado.

### Dados que precisam de cuidado

CPF, telefone e informações de fobia ou gatilho devem permanecer privados por padrão. Eles não devem aparecer em páginas públicas, detalhes de personagens, listagens ou Wiki.

### Critérios de aceite

- Cada URL tem um papel mínimo definido.
- Acesso negado redireciona ou mostra erro de forma consistente.
- O bloqueio funciona mesmo quando a URL é digitada diretamente.
- Admin não consegue fazer ações reservadas ao superadmin, caso essa separação seja aprovada.
- Superadmin mantém o controle total.
- Existem testes automatizados para os principais casos.

### Dúvidas de permissões

- Admin deve poder promover outro usuário a admin?
- Admin deve poder editar outro admin?
- Superadmin será somente o usuário criado pelo Django ou haverá um papel próprio no banco?
- Usuário comum poderá ver personagens de outros usuários?
- Personagens aprovados serão públicos?
- A Wiki será pública para visitantes?
- Admin poderá editar a Wiki ou isso ficará apenas para superadmin?
- Admin poderá criar personagens para outras pessoas?

---

## 6. Fase 3 — Login e registro

### O que o login faz

- Recebe usuário e senha.
- Valida as credenciais.
- Cria a sessão autenticada.
- Redireciona atualmente para a Home.

### O que o registro faz

- Recebe usuário, email e senha.
- Valida a senha pelo sistema do Django.
- Cria o usuário.
- Cria o `Profile` como usuário comum.
- Faz login automaticamente após o cadastro.

### O que será revisado

- Layout e identidade visual.
- Mensagens de erro claras.
- Exibição correta de erros por campo.
- Link de voltar e link entre login e registro.
- Redirecionamento para a página que originou a tentativa de acesso.
- Validação de email e nome de usuário.
- Proteção contra usuário já autenticado acessar login/registro sem necessidade.
- Recuperação e troca de senha, se forem necessárias.
- Confirmação de email, se for necessária.
- Acessibilidade dos campos e mensagens.
- Segurança de sessão, CSRF e logout por POST.

### Critérios de aceite

- Um visitante consegue criar uma conta válida.
- Dados inválidos permanecem no formulário com mensagens compreensíveis.
- Login inválido não revela informação sensível.
- Após tentar acessar personagens sem login, a pessoa volta para o destino original depois de entrar.
- O novo usuário sempre nasce como usuário comum.
- Nenhum usuário consegue escolher seu próprio papel durante o registro.

### Dúvidas de login e registro

- O cadastro precisa de confirmação por email?
- O login será por nome de usuário, email ou ambos?
- Será necessário recuperar senha por email?
- Quais campos devem ser obrigatórios no primeiro cadastro?
- Os dados pessoais serão preenchidos no registro ou somente ao fazer uma inscrição em LARP?

---

## 7. Fase 4 — Criação e gerenciamento de personagens

### O que o fluxo faz hoje

- O usuário logado vê apenas seus próprios personagens.
- Pode criar personagem com nome, descrição, guilda, classe, magias, talentos e aceite.
- A classe influencia as magias disponíveis.
- Há limite de cinco talentos iniciais.
- Algumas classes recebem magias automaticamente.
- O usuário pode abrir detalhes e editar campos do próprio personagem.
- O admin pode atualizar status, aprovação, classe, guilda, XP e ouro pelo painel administrativo.

### Pontos que precisam ser revisados

- O formulário de criação usa `descricao_personagem` e grava em `historia`, enquanto o modelo possui campos separados de história, aparência, objetivos e personalidade.
- Precisamos decidir se a criação será curta, em etapas ou completa.
- Precisamos definir o fluxo de aprovação.
- Precisamos separar claramente dados do jogador e dados do personagem.
- Precisamos definir quais campos o jogador pode editar depois da aprovação.
- Precisamos validar se uma personagem aprovada pode ser excluída.
- Precisamos revisar o uso de magia e talento para evitar valores inválidos enviados manualmente.
- Precisamos definir limites para XP e ouro.
- Precisamos definir se personagens inativos podem participar de LARP.
- Precisamos definir a visibilidade pública de personagens aprovados.

### Proposta de fluxo

1. Usuário cria um rascunho.
2. Preenche os dados básicos.
3. Seleciona classe e guilda.
4. Seleciona magias e talentos válidos.
5. Aceita as regras.
6. Envia para aprovação.
7. Admin revisa.
8. Personagem é aprovado, devolvido para correção ou recusado.
9. O sistema registra a situação e mostra o próximo passo ao jogador.

### Critérios de aceite

- Um usuário nunca consegue editar personagem de outra conta.
- O formulário mostra somente opções compatíveis com a classe escolhida.
- O backend repete as validações, sem depender apenas do JavaScript.
- O status de aprovação fica visível de forma clara.
- Admin consegue revisar sem expor dados privados desnecessários.
- O personagem pode ser usado em uma inscrição somente quando estiver em situação permitida.
- O layout funciona bem em formulários longos.

### Dúvidas de personagens

- A aprovação será obrigatória para todos os personagens?
- O jogador poderá ter quantos personagens?
- Um personagem aprovado poderá ser editado livremente?
- Quem escolhe ou altera a guilda: jogador, admin ou ambos?
- XP e ouro serão editáveis apenas por admin?
- O personagem terá uma página pública?
- Precisaremos de upload de avatar ou imagem?
- A exclusão será permitida ou o personagem apenas ficará inativo?

---

## 8. Fase 5 — Wiki

### O que a Wiki faz hoje

- Exibe regras, classes, itens, talentos e magias.
- Possui listagens e páginas de detalhe.
- Usa dados definidos em arquivos Python.
- Está disponível sem login.

### O que será revisado

- Organização da navegação.
- Busca e filtros.
- Categorias e navegação entre assuntos relacionados.
- Legibilidade de textos longos.
- Breadcrumbs e botão de retorno.
- Responsividade.
- Links quebrados e slugs inválidos.
- Estados vazios e página 404.
- Conteúdo duplicado ou divergente entre Wiki e formulário de personagem.
- Permissões de leitura e edição.

### Decisão arquitetural a tomar

Existem duas possibilidades:

1. **Manter a Wiki em constantes Python:** mais simples e rápida, mas qualquer alteração exige editar código e fazer deploy.
2. **Migrar a Wiki para modelos do banco:** permite editar pelo admin, criar busca, rascunho, publicação e histórico, mas exige modelagem, migração e uma tela administrativa.

### Critérios de aceite

- Todos os links da Wiki funcionam.
- O usuário encontra regras por categoria e busca.
- A Wiki mantém consistência com classes, magias e talentos usados na criação de personagens.
- Conteúdo não publicado não aparece para visitantes.
- A edição, se existir, respeita a permissão definida.
- Conteúdo extenso é confortável de ler no celular.

### Dúvidas da Wiki

- A Wiki continuará pública para visitantes?
- Admin poderá editar o conteúdo?
- Precisamos de rascunho e publicação?
- Precisamos registrar histórico de alterações?
- A Wiki terá conteúdo de cenário/lore além das regras?
- Queremos busca geral no site ou somente dentro da Wiki?

---

## 9. Fase 6 — Revisão transversal depois das cinco primeiras etapas

Depois de concluir Home, permissões, autenticação, personagens e Wiki, faremos uma rodada geral.

### Checklist

- [ ] Todas as rotas principais foram acessadas como visitante.
- [ ] Todas as rotas principais foram acessadas como usuário comum.
- [ ] Todas as rotas administrativas foram acessadas como admin.
- [ ] Todas as rotas reservadas foram acessadas como superadmin.
- [ ] Links do cabeçalho e rodapé foram testados.
- [ ] Formulários foram testados com dados válidos e inválidos.
- [ ] Acesso direto por URL foi testado.
- [ ] Testes CSRF foram conferidos.
- [ ] Layout foi verificado em celular, tablet e desktop.
- [ ] Contraste, foco e textos alternativos foram revisados.
- [ ] Mensagens de sucesso, erro e estado vazio foram revisadas.
- [ ] Não há exposição de CPF, telefone ou fobia/gatilho.
- [ ] Migrações estão aplicadas.
- [ ] Não há erro no `check` do Django.
- [ ] Testes automatizados principais passam.

---

## 10. Ordem de execução prática

Esta é a ordem recomendada para as próximas conversas e alterações:

1. Você responde as dúvidas essenciais da Home e dos papéis.
2. Revisamos e remodelamos o template base e a Home.
3. Testamos a Home nos quatro contextos: visitante, usuário comum, admin e superadmin.
4. Centralizamos e testamos as permissões.
5. Remodelamos login, registro e conta.
6. Testamos autenticação, redirecionamentos e mensagens.
7. Remodelamos o fluxo de personagens.
8. Testamos criação, edição, aprovação e isolamento por usuário.
9. Definimos a arquitetura final da Wiki.
10. Remodelamos a Wiki e validamos seus links e conteúdo.
11. Fazemos a revisão geral e atualizamos a documentação.

Não avançaremos para a próxima etapa enquanto a anterior não tiver um comportamento aprovado e testado.

---

## 11. Perguntas iniciais para começarmos

Responda na ordem que preferir:

1. Qual estilo visual você quer para o site: medieval, sombrio, documental, moderno, minimalista ou outro?
2. A Home deve vender a ideia do universo ou ser um painel rápido para jogadores?
3. Wiki e guildas serão públicas para qualquer visitante?
4. Qual é a diferença exata entre admin e superadmin no seu projeto?
5. Admin pode promover usuários a admin ou somente superadmin pode fazer isso?
6. Personagens aprovados poderão ser vistos por outros jogadores?
7. Todo personagem precisa ser aprovado antes de participar de um LARP?
8. Você quer editar a Wiki pelo painel ou prefere manter o conteúdo em arquivos por enquanto?
9. Tem logo, imagens, cores ou algum site de referência para o novo layout?
10. Quer começar pela Home pública ou pelo painel da Home quando o usuário está logado?

---

## Estado deste plano

- [x] Estrutura atual do projeto levantada.
- [x] Fluxos atuais identificados.
- [x] Primeira matriz de permissões criada.
- [x] Ordem de remodelagem definida.
- [ ] Dúvidas iniciais respondidas.
- [ ] Home remodelada e testada.
- [ ] Permissões centralizadas e testadas.
- [ ] Login e registro remodelados e testados.
- [ ] Personagens remodelados e testados.
- [ ] Wiki remodelada e testada.
- [ ] Revisão transversal concluída.
