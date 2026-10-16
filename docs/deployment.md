# Publicação do site

## Brasões na home e na criação de personagens — 16/10/2026

A home e a etapa de guilda em `/personagens/novo/` usam a mesma composição de sete brasões com círculos ovais do índice de guildas. Na home, os símbolos abrem as páginas correspondentes; na criação, são escolhas com nome, foco de teclado e destaque na cor de cada guilda. Os brasões ficam visíveis em uma grade, sem carrossel de guildas. No desktop, a home distribui texto e composição em duas colunas; no celular, os elementos se reorganizam sem rolagem horizontal.

A seleção continua exibindo vantagem, marca/desvantagem e condição de saída da guilda escolhida, diretamente no navegador. Os valores enviados pelo formulário e a preservação das escolhas após erros de validação permanecem iguais. O seletor de classes mantém seu comportamento anterior. O componente compartilhado usa `guild-heraldry.css?v=guild-heraldry-1`.

## Identidades visuais das guildas — 16/10/2026

O índice e os sete detalhes de `/guildas/` receberam composições amplas, paletas próprias, brasões coloridos, ornamentos em SVG/CSS, narrativas e referências dos PDFs. O desktop usa grade e colunas para aproveitar a largura; o celular mantém leitura em uma coluna. Mercenários são identificados como caminho sem guilda, e a área privada continua restrita a membros e administradores das seis guildas. Os detalhes herdam o favicon branco global.

Validação local: **160 testes** em SQLite isolado e teste Chrome do índice e dos sete detalhes em 1920/1440/390 pixels. Foram verificados imagens, links, regras públicas, títulos e brasões sem cortes, ausência de rolagem horizontal e o isolamento dos conteúdos internos entre visitante, usuário externo, membro e admin. A [documentação de design](design-guildas-2026-10-16.md) registra as referências e escolhas.

Publicado em **https://larp.kw1.com.br/guildas/** após **175 testes isolados no servidor** e oito verificações de guildas/metadados sobre a última legenda dos Mercenários. Cópia validada: `/root/codex-ops/stage-guild-design-20261016-145613/`. Backup e manifesto: `/root/codex-ops/backups/guild-design-20261016-145613/`. Foram coletados dois estilos e o Gunicorn recebeu recarga graciosa, sem migrações. O índice e os sete detalhes retornaram 200 pelo domínio público, com brasões, metadados e CSS correspondentes aos arquivos locais, sem cortes ou transbordamento em 1920/390 pixels. A conferência em transação somente de leitura confirmou as restrições das áreas de membros, a independência dos Mercenários e a consistência do histórico de XP.

## Símbolos das guildas nos participantes e favicon branco — 16/10/2026

A primeira coluna da planilha de participantes mostra somente o símbolo da guilda do personagem, com nome no texto alternativo e ao passar o mouse. Os símbolos vêm do mesmo catálogo público das guildas, incluindo Mercenários Independentes. Personagens sem guilda recebem um traço; não é feita consulta adicional ao banco. No celular, o símbolo fica ao lado da identificação do jogador no cartão. Seleção, filtros e salvamento mantêm o funcionamento anterior.

O favicon usa o símbolo branco em fundo transparente, com SVG e fallback PNG de 32 × 32 pixels. Os novos nomes `favicon-white.svg` e `favicon-white-32.png`, com `?v=2`, evitam reutilizar o endereço do ícone antigo. O CSS de eventos usa `?v=events-guilds-2`.

Validação local: **79 testes de core/dashboard** em SQLite isolado e teste de navegador da gestão de eventos, incluindo carregamento real dos símbolos, Mercenários Independentes, celular sem sobreposição ou rolagem horizontal, filtros, seleção, gravação, conflitos, falha de rede e estado vazio. Os pixels do PNG foram conferidos como brancos, com transparência.

Publicado em **https://larp.kw1.com.br** após **175 testes isolados no servidor**. Cópia validada: `/root/codex-ops/stage-participant-guilds-20261016-135209/`. Backup e manifesto: `/root/codex-ops/backups/participant-guilds-20261016-135209/`. Foram coletados três estáticos e o Gunicorn recebeu recarga graciosa, sem migrações. A conferência somente de leitura confirmou o símbolo correto na primeira coluna dos seis inscritos do evento existente e a consistência do histórico de XP. O SVG branco, o PNG transparente e o CSS atualizado retornaram 200 pelo domínio público, com os mesmos bytes dos arquivos locais.

## Prévias de compartilhamento e favicon — 16/10/2026

As páginas públicas entregam metadados Open Graph e Twitter Card no HTML inicial. Detalhes da Wiki, guildas, LARPs públicos e leitores de documentos usam as imagens vinculadas ao conteúdo. Listas e páginas sem imagem própria ficam sem capa genérica; a página inicial usa uma capa de 1200 × 630 pixels com nome e símbolo do Codex. Fichas de personagens, contas, inscrições e administração não recebem prévias públicas. O símbolo também é usado no favicon PNG e no ícone para atalhos Apple.

Validação local: **160 testes** em SQLite isolado, incluindo sete testes de metadados, conteúdo sem imagem, restrições de acesso, HTTPS encaminhado, dimensões e integridade dos PNGs. O teste de HTTPS respeita o cabeçalho de proxy configurado em cada ambiente, inclusive o cabeçalho próprio do servidor. A [documentação de compartilhamento](compartilhamento-links.md) descreve a escolha das imagens e sua atualização.

Publicado em **https://larp.kw1.com.br** após **175 testes isolados no servidor**, preservando os 15 testes exclusivos de acesso. Cópia validada: `/root/codex-ops/stage-social-links-20261016-133054/`. Backup e manifesto: `/root/codex-ops/backups/social-links-20261016-133054/`. Foram coletados três estáticos e o Gunicorn recebeu recarga graciosa, sem migrações. A conferência anônima pelo domínio público confirmou metadados e imagens com resposta 200 na página inicial, Bardo e Círculo do Fogo; também confirmou os dois ícones PNG, listas sem capa genérica e páginas restritas sem metadados públicos.

## Biblioteca de documentos da Wiki — 15/10/2026

A Wiki ganhou `/wiki/documentos/`, com os originais de **Manual LARP - 3.3.pdf** e **Cenário_ Contos da Cachoeira.pdf**. Cada documento possui uma tela de leitura, navegação por páginas, zoom, busca no texto, tela cheia e download. A biblioteca é pública, tem acesso pelo menu e pela página inicial da Wiki, e funciona no celular.

Os PDFs permanecem em `docs/`, sem conversão nem alteração do conteúdo. A entrega usa uma lista fixa de dois documentos, suporta GET/HEAD, intervalos de bytes (206/416), ETag e Last-Modified. O download é enviado como anexo com o nome original; o leitor obtém apenas os trechos necessários. Arquivos desconhecidos ou ausentes retornam 404. Não há acesso a caminhos arbitrários do repositório.

O leitor usa uma cópia local de **PDF.js 6.4.299**, com licença e manifesto de integridade, sem dependência de CDN durante a leitura. Os módulos mantêm os bytes do pacote oficial e usam extensão `.js` para compatibilidade com os tipos MIME do servidor existente. Os novos scripts/estilos usam `?v=documents-1`. O utilitário `tools/prepare_wiki_documents.py` confere SHA-512 do pacote e gera as capas a partir da primeira página dos PDFs.

Validação local: **153 testes** em SQLite isolado e teste real de navegador de ambos os PDFs. Foram conferidos download por SHA-256, navegação sem recarga, zoom, busca, tela cheia, celular, última página e fallback de download quando o leitor não carrega. Nenhum usuário ou saldo real foi alterado. Esta atualização não exige migrações.

**Publicado em 16/10/2026**, após o restabelecimento da conexão com o servidor. A cópia `/root/codex-ops/stage-wiki-documents-20261015-224919/` passou em **168 testes isolados no servidor**; os hashes e checks finais foram reconferidos antes da aplicação. Backup e manifesto: `/root/codex-ops/backups/wiki-documents-20261015-224919/`. A aplicação coletou 291 estáticos e recarregou o Gunicorn de forma graciosa, sem migrações. Ambos os PDFs abriram pelo domínio público, com 25 e 23 páginas, respostas 206 para intervalos e downloads como anexo. A última página do Cenário também renderizou no celular, sem erros de navegador. As conferências no banco foram somente de leitura, preservando os testes de acesso e a consistência do histórico de XP.

Para consultar sem depender da conexão de produção, `codex/.venv/Scripts/python.exe tools/wiki_documents_preview.py --port 8012 --duration 3600` abre uma prévia em `http://127.0.0.1:8012/wiki/documentos/`, durante uma hora, com SQLite temporário. A prévia não usa contas nem saldos reais; os PDFs são os originais locais. O desenvolvimento normal mantém suas configurações anteriores.

## Escolhas na criação de personagens — 15/10/2026

Em `/personagens/novo/`, a guilda selecionada apresenta sua vantagem, marca/desvantagem e, quando aplicável, a condição de saída autorizada. Os textos vêm das mesmas informações públicas usadas nas páginas das guildas. A troca acontece no navegador, sem recarregar o documento.

Os campos de divindade de Clérigos/Paladinos e de afinidade do Druida usam rótulos, ajuda, bordas arredondadas e foco no padrão da criação. O Mago escolhe um dos três feitiços antigos por opções de seleção única, com o mesmo estilo das magias. Essa escolha é excluída das opções de uma solicitação adicional de Feitiço Antigo. Campos de outras classes ficam desabilitados; erros de validação preservam a guilda, as magias e o feitiço antigo escolhidos.

Foram corrigidos também o tamanho do seletor interno de classe e o posicionamento da opção selecionada no carrossel ao redimensionar a tela. Validação local: **51 testes de personagens** em SQLite isolado e **dois testes de navegador**, cobrindo Bardo, Clérigo, Paladino, Druida, Mago, as sete guildas, celular, validação e gravação com contas fictícias. Não há migrações. Os scripts da criação e dos talentos usam `?v=creation-options-1`.

Publicado em **https://larp.kw1.com.br** após **161 testes isolados no servidor**. Cópia validada: `/root/codex-ops/stage-creation-options-20261015-220357/`. Backup dos arquivos e manifesto: `/root/codex-ops/backups/creation-options-20261015-220357/`. Foram coletados dois estáticos e o Gunicorn recebeu recarga graciosa. A conferência em transação somente de leitura confirmou a página de criação, os detalhes das sete guildas, as três opções de feitiço antigo e a exigência de login. As proteções anteriores e a consistência do histórico de XP foram preservadas. Os scripts entregues publicamente e pelo servidor local corresponderam aos arquivos validados.

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
