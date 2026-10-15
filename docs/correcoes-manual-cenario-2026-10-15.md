# Correções da auditoria — 15/10/2026

Este registro acompanha a [auditoria original](auditoria-sistema-manual-cenario-2026-10-15.md). As evidências originais descrevem o comportamento anterior às correções e foram preservadas.

## Problemas corrigidos

| ID | Resultado |
| --- | --- |
| F01 | Cadastro pessoal, inscrição e edição de perfil no Django admin salvam apenas os campos envolvidos, preservando XP alterado por outra operação. |
| F02 | Ativação preserva Conjurar e magias anteriormente compradas após Multiclasse; condições exclusivas de aquisição não são reaplicadas retroativamente. |
| F03 | Multiclasse exige feitiço antigo para Mago, divindade para classes sagradas e afinidade para Druida; a comissão registra sua forma. A ficha apresenta as capacidades da segunda classe ativa. Compras antigas incompletas podem ser complementadas uma vez pelo admin, com registro do responsável e sem nova cobrança. |
| F04 | Forma inicial definida fica bloqueada nos formulários de edição. Detalhes da comissão só são gravados na transação que confirma a aprovação; reenvio e falta de XP não modificam a definição. |
| F05 | Ouro usa decimal e aceita múltiplos de 0,5 DO, inclusive entrada com vírgula. O editor do admin e a planilha de LARP aceitam prata; os saldos antigos mantêm o mesmo valor. |
| F06 | Conjurar registra tipo e descrição do foco e recusa armas, escudos e cajados, inclusive uma “espada-amuleto”. Objetos personalizados continuam sujeitos à comissão. |
| F07 | Mercenários não podem solicitar patente. A comissão registra os benefícios e as obrigações; a compra preserva a guilda em que a patente foi concedida. |
| F08 | Novas solicitações leem preço e repetição do catálogo publicado na wiki. A lista Quem usa das magias alimenta a criação. Cada compra preserva nome, preço e versão da regra; ocultar/remover uma entrada impede novas solicitações e preserva aquisições antigas. |
| F09 | Clérigos e Paladinos precisam informar uma divindade; declarações explícitas de ateísmo/ausência e filosofia de vida são recusadas. Entidades personalizadas permanecem sob avaliação, pois o caderno não é uma lista fechada. |
| C01 | Páginas públicas mostram benefícios de jogo, marcas e condições de saída de guildas; Mercenários têm apresentação própria. As seis guildas administrativas são cadastradas e os membros aprovados/ativos sincronizados. |
| C02 | Focos aparecem nas classes e na criação; foram completadas as regras de Sangue de Dragão e Laço da Verdade. A wiki ganhou referências de combate, morte, descanso, veneno, XP, moeda e missões. |
| C03 | Nova seção Cenário, editável no painel da wiki, com referências de história, divindades, lugares, planos, Zona Neutra e pactos. |

## Regras de preservação

- Uma alteração de preço vale para novas solicitações. Solicitações já registradas mantêm o valor apresentado ao jogador; aquisições pagas preservam seu histórico.
- Alterações de repetição não removem compras antigas. Magias já aprendidas não podem ser silenciosamente renomeadas pelo editor.
- Criar um talento de referência publicado permite solicitá-lo com descrição e avaliação da comissão. Efeitos personalizados são interpretados pela comissão; não geram poderes automáticos adicionais no código.
- As nove classes jogáveis seguem o Manual 3.3. Novas entradas de classe na wiki são referências, e o editor informa essa distinção. Não foi criado um editor de classes mecânicas arbitrárias.
- Conteúdo personalizado existente é preservado pela migração. Os textos de itens só são substituídos quando ainda correspondem ao conteúdo padrão anterior.
- Registros administrativos antigos de guildas, descrições privadas e estados de visibilidade são preservados. Mercenários não ganham uma área privada coletiva.

## Pontos que continuam com a comissão

Os PDFs divergem sobre asilo à Serpente, posição dos guardiões e punição solar da Floresta do Sol. As referências agora expõem esses pontos e orientam consultar a comissão; nenhuma interpretação foi imposta silenciosamente. As lacunas da cronologia também não foram preenchidas com fatos inventados.

O controle completo de inventário, a automação de recompensas e missões e um histórico específico de pactos/deserções continuam sendo ampliações funcionais, separadas das falhas corrigidas. A aprovação de fichas permanece como avaliação humana da história e do cenário.

## Validação

- 134 testes do Django passaram em SQLite em memória, incluindo regressões das falhas confirmadas.
- 149 testes passaram na cópia preparada no servidor, incluindo os 15 testes adicionais de controle de acesso de produção.
- `makemigrations --check --dry-run` não encontrou diferenças pendentes entre modelos e migrações.
- `tools/character_manual_smoke.py`: criação em cinco etapas, magias exatas, talentos pendentes, prévias, upload/remoção e celular.
- `tools/manual_audit_smoke.py`: Multiclasse solicitada/aprovada/ativa, ficha consolidada, 1,5 DO salvo no admin sem recarga, preço editado na wiki refletido na solicitação e referências do cenário.
- `tools/manual_audit_migration.py`: ouro 0, 7 e 2.147.483.647 preservado, XP preservado, custo histórico mantido e texto personalizado preservado.
- Capturas de desktop e celular inspecionadas visualmente.

As gravações desses testes foram feitas exclusivamente em banco isolado. O registro da publicação e de suas verificações consta em [deployment.md](deployment.md).

Publicado em 15/10/2026. A verificação posterior confirmou saldos e histórico preservados, seis guildas administrativas cadastradas e renderização das páginas. As páginas públicas de Wiki e Cenário e a referência de Cenário local retornaram HTTP 200.
