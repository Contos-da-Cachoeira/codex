# Editor da wiki

Acesse **Área Admin → Wiki** (`/area-admin/`). A lista, os filtros, a criação, a edição e a confirmação de exclusão ficam na própria aba, mantendo as demais abas do admin acessíveis. O antigo endereço `/wiki/gerenciar/` continua abrindo esse painel; o navegador limpa o endereço ao entrar.

O catálogo compacto à esquerda é dividido por seção, com miniaturas e indicação de publicação. Clique em uma entrada para ver sua imagem e todas as informações à direita. Os títulos das seções recolhem ou expandem seus conteúdos. Em telas pequenas, os detalhes aparecem abaixo da lista.

A troca de seleção atualiza apenas os detalhes no navegador, sem nova requisição de conteúdo ou recarga da página. A posição da lista é preservada. A aba e a seleção ficam no estado do painel, sem parâmetros ou fragmentos na barra de endereço. Criar, editar, filtrar, salvar, publicar e excluir usam respostas parciais do servidor, mantendo o documento e as outras abas abertos. As prévias são enviadas somente na página protegida do admin; as alterações continuam passando pela validação do servidor.

- Use o botão **Criar** e escolha a seção dentro do painel de criação: regras, classes, talentos, magias ou itens. Novas entradas começam ocultas.
- Edite textos, campos específicos de cada seção e imagens (até 10 MB).
- Use **Publicar** ou **Ocultar** para controlar a exibição. Uma entrada oculta também retorna 404 pelo link direto, inclusive para administradores; a edição continua disponível no painel.
- **Excluir** mostra a confirmação dentro da aba antes da remoção definitiva.
- As regras gerais de magia são uma entrada própria, editável na lista.
- Nas regras, escreva cada seção como um bloco: título na primeira linha e tópicos nas seguintes. Separe os blocos com uma linha vazia.

A autorização segue o painel existente: superusuário, staff ou perfil com papel Admin. Todas as alterações exigem POST com proteção CSRF.

Os conteúdos são armazenados em `WikiEntry`. As migrações `0001` e `0002` criam a tabela e importam os 67 conteúdos originais com seus links e imagens estáticas. Os arquivos de constantes continuam disponíveis para outros módulos, mas as páginas da wiki consultam o banco. Editar a wiki não altera automaticamente as regras de cálculo das fichas.

Em outra instalação, execute `python manage.py migrate` antes de iniciar a versão atualizada. Os uploads usam o armazenamento de mídia já configurado pelo projeto.

Validação isolada, sem acessar o banco ou armazenamento de produção:

```powershell
codex/.venv/Scripts/python.exe codex/manage.py test wiki dashboard --settings=wiki.test_settings --noinput
```

Para verificar a troca instantânea em um navegador isolado (requer Playwright e Chrome):

```powershell
codex/.venv/Scripts/python.exe tools/wiki_selection_smoke.py
```

Essa verificação cobre cliques rápidos, seleção entre seções, preservação da lista e envio das ações para o item correto, confirmando uma única carga do documento e um endereço limpo.
