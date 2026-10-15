# Publicação do site

## Gerenciamento de eventos — 15/10/2026

As telas administrativas de cada LARP passam a ter uma visão geral com indicadores de inscrições, pagamentos e presenças, edição do evento e prévia da capa. A página de participantes reúne pagamento, presença, XP do jogador e ouro do personagem; inclui busca, filtros e detalhes do inscrito. No celular, os participantes aparecem em cartões e os detalhes abrem em uma janela.

Seleção, filtros e salvamento dos formulários acontecem sem recarregar o documento. Somente os campos alterados são enviados para gravação. A atualização dos participantes é atômica, verifica os valores anteriores e permite recuperar conflitos sem apagar as edições dos outros inscritos. Reenviar uma resposta perdida não duplica ajustes no histórico de XP.

Validação local: **146 testes** em SQLite isolado e testes de navegador de eventos e do admin. Foram conferidos os estados vazio/sem resultados, pagamentos, presença, saldos, conflito concorrente, falha de rede, prévia e upload da capa, horário local e layout no celular. Nenhuma conta real foi usada nos testes. Esta atualização não exige migrações; os novos estáticos usam `?v=events-1`.

Publicado em **https://larp.kw1.com.br** após **161 testes no servidor** em SQLite isolado, incluindo os 15 testes exclusivos de acesso administrativo. Cópia validada: `/root/codex-ops/stage-events-20261015-205455/`. Backup dos arquivos e manifesto: `/root/codex-ops/backups/events-20261015-205455/`. A aplicação coletou dois arquivos estáticos e recarregou o Gunicorn de forma graciosa, sem executar migrações.

A verificação posterior, em transação somente de leitura, confirmou a renderização da visão geral e dos participantes de um evento existente e a consistência dos saldos com o histórico de XP. Os arquivos entregues pelo Cloudflare corresponderam aos SHA-256 locais; a lista pública de LARPs retornou 200. Os ajustes anteriores e os testes exclusivos de produção foram preservados.

## Correções da auditoria Manual/Cenário — 15/10/2026

Correções aplicadas em **https://larp.kw1.com.br**, cobrindo XP concorrente, ativação e escolhas de Multiclasse, definições de Forma Selvagem, prata, focos, patentes e integração do catálogo publicado com novas solicitações. A wiki ganhou a seção Cenário e referências adicionais das regras; os benefícios de guilda foram revisados.

- Cópia validada: `/root/codex-ops/stage-audit-20261015-180759/`.
- Backup dos arquivos, manifesto e banco PostgreSQL 18: `/root/codex-ops/backups/audit-20261015-180759/`. O banco foi exportado em formato customizado, com acesso restrito, antes da aplicação.
- Migrações aplicadas: `personagens.0008`, `guildas.0002`, `wiki.0003` e `wiki.0004`. A conversão do ouro preservou o valor de todos os saldos; não houve consolidação adicional de XP.
- Validação: **134 testes locais** e **149 testes no servidor**, ambos em SQLite isolado; os 15 testes adicionais de acesso de produção foram preservados. Dois testes de navegador passaram, incluindo Multiclasse e salvamento de 1,5 DO no admin sem recarregar o documento. A migração também foi reproduzida sobre dados antigos fictícios, preservando custo pago e texto personalizado.
- Durante a aplicação, o Django foi interrompido sob bloqueio do gerenciador. PostgreSQL e os serviços de rede permaneceram ativos. O Django foi reiniciado e as verificações de renderização foram concluídas.
- Conferência posterior: todos os valores de ouro, saldos de XP e quantidade de movimentos corresponderam aos valores anteriores à migração. Todos os saldos de XP continuam coincidindo com a soma do histórico; as seis guildas administrativas estão cadastradas. Nenhuma conta real foi usada para compras de teste.
- As páginas públicas `/wiki/` e `/wiki/cenario/` retornaram 200 pelo Cloudflare, com o conteúdo novo. `/wiki/cenario/` também retornou 200 em `127.0.0.1:8000`.
- Os estáticos alterados usam `?v=manual-audit-2`. O histórico de compras mantém o preço da solicitação; alterações posteriores na wiki valem para novas solicitações.

O [registro das correções](correcoes-manual-cenario-2026-10-15.md) distingue os defeitos resolvidos das decisões pendentes da comissão e das ampliações funcionais de inventário, recompensas, missões e pactos.

Para recuperação, use o backup de banco e arquivos conjuntamente, considerando qualquer atividade posterior à publicação. Não reverta apenas o código após novos saldos em prata ou novas compras.

## Etapa de talentos na criação — 15/10/2026

A criação passa a ter cinco etapas: nome, classe, guilda, talentos e prévia/foto. O jogador consulta custos e requisitos, adiciona ou remove até cinco solicitações (incluindo compras repetidas) e pode continuar sem talentos. As solicitações são gravadas junto com a ficha, pendentes da comissão. O servidor confere saldo, pré-requisitos, repetições e escolhas de magias; o XP continua sendo descontado somente na aprovação. Esta alteração não exige novas migrações.

## Atualização de personagens — 15/10/2026

Regras de criação e evolução conforme o Manual LARP 3.3 aplicadas ao projeto ativo, incluindo o saldo único de XP por jogador e a definição de que cada compra repetida ativa ocupa uma das cinco vagas. A aparência fica na última etapa, com comparação entre nome, imagem da classe e foto própria.

- Cópia validada: `/root/codex-ops/stage-manual-20261015-143921/`.
- Backup dos arquivos, manifesto e banco PostgreSQL 18: `/root/codex-ops/backups/manual-20261015-143921/`. O banco foi exportado com `pg_dump` 18.6 em formato customizado, com acesso restrito.
- Migrações aplicadas: `core.0021`, `personagens.0006` e `personagens.0007`. Os saldos antigos foram consolidados uma única vez; as colunas anteriores e as anotações de talentos foram preservadas. Fichas existentes foram sinalizadas para revisão.
- Validação: **121 testes** no servidor em SQLite isolado, incluindo as proteções de produção; testes de navegador da criação, prévias, upload/remoção, celular e operações do admin sem recarga. Após a publicação, as telas de criação/talentos renderizaram, os arquivos corresponderam ao manifesto e todos os saldos coincidiram com o histórico de XP.
- Apenas o Django foi interrompido durante o backup e a migração. O bloqueio do gerenciador impediu reiniciar processos antigos durante a consolidação; PostgreSQL e os serviços de rede permaneceram ativos.

O código publicado corresponde à revisão local `ec3935d` mais as alterações desta implementação, ainda sem commit. Os ajustes e o teste de acesso que já existiam no servidor foram preservados. Os scripts de aparência/criação e o seletor de imagens usam a versão de cache `manual33`.

Reverter somente o código ou repetir a migração de consolidação não é um procedimento seguro após novas compras. Para recuperação integral, interrompa o Django e use conjuntamente o backup do banco e dos arquivos, considerando qualquer atividade posterior ao backup.

## Publicação anterior

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
