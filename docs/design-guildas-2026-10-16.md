# Identidades visuais das guildas

As páginas públicas de guildas foram redesenhadas a partir das descrições e dos brasões do Manual LARP 3.3 e do Cenário dos Contos da Cachoeira. Os originais permanecem em `docs/` e podem ser lidos em `/wiki/documentos/`.

As cores foram observadas nas imagens dos PDFs. Os tons hexadecimais, a tipografia, as molduras e os ornamentos são uma interpretação visual para o site, não especificações oficiais de regras, arquitetura ou novos locais do cenário.

| Caminho | Paleta e composição | Referências no Manual | Referências no Cenário |
| --- | --- | --- | --- |
| Artistas da Revolução | Dourado, coral e ciano; cartaz assimétrico, faixas de cor e tipografia expressiva | 6-7 | Sem perfil próprio |
| Círculo do Fogo | Escarlate, carvão e âmbar; estandarte angular e título monumental | 7 | 6-7 |
| Floresta do Sol | Verde profundo e dourado solar; máscara, halo e molduras orgânicas | 7-8 | 8-9 |
| Irmandade das Tavernas | Verde e ouro envelhecido; brasão à esquerda, arco e linhas de madeira discretas | 8-9 | 7-8 |
| Os Rasga-Mortalhas | Violeta, osso e negro; coruja, círculos e linhas de labirinto | 9 | 10-11 |
| Sociedade Zaori | Lilás, índigo e prata; olho, geometria orbital e pontos de luz | 9-10 | 9-10 |
| Mercenários Independentes | Aço e carvão; escudo sem brasão e composição de contrato | 10 | Sem perfil próprio |

Os números indicam as páginas físicas dos PDFs. Cada detalhe tem introdução, traços, narrativa original, referências e chamada final próprias. Os brasões existentes mantêm suas cores. Os textos de vantagem, marcas, desvantagem e saída continuam vindo de `core/constants/guildas.py`, sem alteração das regras.

A divergência sobre a punição solar da Floresta continua explícita. Marca de traição e saída autorizada de Zaori permanecem separadas. Mercenários são apresentados como pessoas sem guilda, sem sede, liderança ou área privada coletiva. Artistas e Mercenários indicam somente o Manual como fonte do seu perfil.

## Computador e celular

O índice reúne seis guildas em uma grade de três colunas no desktop largo, duas em larguras intermediárias e uma no celular. Mercenários possuem um bloco próprio. A navegação por brasões leva diretamente aos cartões, e cada cartão abre o detalhe correspondente.

Nos detalhes, o desktop usa uma abertura ampla de duas colunas, brasões grandes e ornamentação própria; história e identidade ficam lado a lado, assim como vantagem e compromisso. As Tavernas invertem a composição da abertura. No celular, o conteúdo segue uma coluna com títulos e imagens dimensionados para leitura. Todos os links têm foco visível e os efeitos de movimento respeitam a preferência de movimento reduzido.

## Acesso e validação

Não houve alteração de modelos, consultas ou permissões. Descrição interna, notícias, contadores e personagens aprovados continuam exclusivos de membros da própria guilda e administradores. As páginas preservam as prévias públicas com seus brasões e passam a herdar o favicon branco global.

Validação local: 160 testes Django em SQLite isolado. `tools/guild_design_smoke.py` confere o índice e os sete detalhes em Chrome, nas larguras de 1920, 1440 e 390 pixels, incluindo imagens, regras públicas, navegação, ausência de cortes/transbordamento e os perfis de visitante, usuário externo, membro e administrador. As contas, notícias e personagens usados no teste são fictícios e existem apenas no banco temporário.

Os estilos usam versões de cache `guild-identities-1` e `guildas-20261016`. O carrossel compartilhado da página inicial e da criação de personagens não foi alterado.
