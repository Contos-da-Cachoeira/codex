# Arquitetura por Modulos

Este projeto foi reorganizado para crescer por dominio funcional.

## Modulos atuais

- accounts: autenticacao, registro, logout e gestao da propria conta.
- dashboard: home e areas autenticadas (admin e usuario).
- core: componentes compartilhados (ex.: modelo Profile e template base).

## Estrutura

- codex/accounts/
  - forms.py
  - views.py
  - urls.py
  - templates/accounts/
- codex/dashboard/
  - views.py
  - urls.py
  - templates/dashboard/
- codex/core/
  - models.py
  - admin.py
  - templates/core/base.html

## Roteamento

As rotas do projeto agora estao separadas no arquivo principal:

- dashboard.urls para home e dashboards
- accounts.urls para login, registro, logout e minha conta

## Como criar um novo modulo

1. Criar pasta do modulo em codex/<nome_modulo>/.
2. Adicionar arquivos minimos:
   - __init__.py
   - apps.py
   - views.py
   - urls.py
3. Criar templates em codex/<nome_modulo>/templates/<nome_modulo>/.
4. Registrar o app em INSTALLED_APPS no settings.
5. Incluir as urls do modulo no codex/urls.py.
6. Manter nomes de URL unicos para evitar conflito.

## Convencoes recomendadas

- Cada modulo deve ter responsabilidade unica.
- Logica de autenticacao no accounts.
- Telas e fluxo principal no dashboard.
- Entidades compartilhadas no core (ou em um futuro modulo common).
- Evitar dependencia circular entre modulos.

## Proximo passo sugerido

Extrair o modelo Profile do core para um modulo identities com migracao planejada, mantendo compatibilidade de dados.
