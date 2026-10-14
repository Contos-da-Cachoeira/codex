# Publicação do site

Atualização realizada em 14/10/2026 pelo alias SSH `kiwiki` para **https://larp.kw1.com.br**.

- Projeto ativo: `/var/www/sites/Codex`, dentro do Debian executado pelo Termux.
- Revisão publicada: `30904b68fef943fb1a0c1133c10531f454650716`, com os ajustes de acesso e cache descritos abaixo.
- Configuração de produção: `/root/codex-ops/codex_production.py`.
- Backup anterior, arquivos de retorno, manifesto e relatório: `/root/codex-ops/backups/site-update-20261014-214401/`.
- Cópia preparada e testada: `/root/codex-ops/stage-site-update-20261014-214401/`.

Os ajustes que existiam somente no servidor foram incorporados ao código local: usuários comuns recebem 403 no admin, contas inativas são recusadas, os métodos HTTP são limitados e as ações POST são conferidas antes da execução. A lista de ações permitidas inclui os novos fluxos da Wiki e de LARPs. O teste adicional `dashboard/test_admin_access.py` do servidor foi preservado.

Os links de `wiki/js/items.js` e `dashboard/admin-tabs.js` usam `?v=30904b6`, pois o Cloudflare mantinha as versões anteriores em cache por quatro horas. Ao publicar outra alteração nesses scripts, atualize também a identificação de versão nos templates que os carregam.

O índice do Git foi reconstruído a partir de HEAD, com cópias anteriores guardadas no backup, preservando os arquivos de trabalho. Os ajustes anteriores também foram guardados no stash `9df9e8d05bf21019c5921ec308307a3b0a696991`. Os arquivos locais modificados nesta publicação correspondem aos ajustes aplicados no servidor e ainda precisam ser incluídos em um próximo commit.

## Validação e aplicação

A combinação do código novo com os ajustes de produção passou em **97 testes**, usando SQLite em memória e o overlay de produção. Os testes de navegador verificaram os filtros da Wiki e as operações do admin sem recarregar o documento.

`migrate --check` confirmou que todas as migrações já estavam aplicadas. A publicação coletou 10 arquivos estáticos novos ou alterados e enviou SIGHUP ao master Gunicorn existente para recarga graciosa.

Na origem foram conferidos a página 404, início, Wiki, classes, guildas, LARPs, os novos estáticos e os bloqueios administrativos. Pelo domínio público, `/404/` retornou 404 com o template personalizado e `/wiki/` retornou 200 com o layout novo. O JavaScript da Wiki entregue pelo Cloudflare teve o mesmo SHA-256 do arquivo local.
