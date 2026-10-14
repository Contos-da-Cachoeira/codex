# Catálogos da Área Admin

As abas **Usuários**, **Personagens** e **LARPs** seguem o layout da Wiki: catálogo compacto com fotos e seções à esquerda, ficha e ações do registro selecionado à direita.

- Usuários são separados entre superadministradores, administradores e usuários comuns. A ficha mostra os dados do jogador, seus personagens e inscrições. O tipo da conta é alterado individualmente; contas de superadministrador continuam protegidas.
- Personagens são separados por aprovação. A ficha permite consultar as informações e editar status, aprovação, classe, guilda, XP e ouro.
- LARPs são separados entre publicados e ocultos. É possível criar e editar um evento, enviar sua capa, mudar a visibilidade, copiar o link de inscrição e acessar a planilha de inscritos.

A seleção e a abertura dos formulários acontecem no navegador, sem recarregar o documento. Os grupos e a posição da lista permanecem abertos; alternar entre registros preserva uma edição em andamento. **Cancelar** descarta as alterações do formulário. A aba e o registro escolhido são guardados no estado do painel e na sessão do navegador por conta, mantendo a barra de endereço em `/area-admin/`. Links antigos com parâmetros e fragmentos continuam sendo aceitos ao entrar e depois são normalizados.

Salvar e filtrar usam requisições em segundo plano, sem navegar para outra página. A validação administrativa e a proteção CSRF permanecem no servidor. Somente o painel afetado recebe a resposta; as outras abas e os campos de uma edição em andamento permanecem intactos. Falhas de rede mantêm o formulário disponível para tentar novamente. Em telas pequenas, a ficha aparece abaixo do catálogo.

As prévias só são renderizadas na rota protegida `/area-admin/`. O contexto é preparado em `dashboard/record_managers.py`. `admin-shell.js` centraliza o estado e as requisições; `admin-records.js` controla os três catálogos. O cabeçalho `X-Admin-Panel` solicita uma resposta JSON parcial, sem alterar as permissões da rota. O editor da página inicial mantém seu próprio salvamento em segundo plano.

Verificação com banco e navegador isolados, sem usar dados de produção:

```powershell
codex/.venv/Scripts/python.exe codex/manage.py test wiki dashboard --settings=wiki.test_settings --noinput
codex/.venv/Scripts/python.exe tools/admin_records_smoke.py
codex/.venv/Scripts/python.exe tools/wiki_selection_smoke.py
codex/.venv/Scripts/python.exe tools/admin_session_smoke.py
```

Os testes de navegador exigem Playwright e Chrome instalados. As capturas usam somente dados fictícios e são gravadas na pasta de mídia local ignorada pelo Git.
