# ✅ Codex LARP — Checklist de Desenvolvimento

## 📌 INSTRUÇÕES PARA IA

- Marcar [x] quando concluído
- Marcar [ ] quando pendente
- Nunca pular fases
- Priorizar ordem definida
- Garantir funcionamento antes de avançar

## 📍 STATUS REAL DO PROJETO (25/03/2026)

- Fase 1 concluída
- Fase 2 concluída
- Autenticação unificada no app `accounts`
- Perfil e tipo de usuário implementados via model `Profile`
- Dashboard com área de admin e usuário implementado
- Banco configurado para PostgreSQL
- App `personagens` integrado ao projeto com constantes centralizadas
- CRUD de personagens concluído (listar, criar, editar e detalhar)

## ▶ EXECUÇÃO IMEDIATA (PRÓXIMOS PASSOS)

- [x] Definir se a próxima etapa usará SQLite (MVP) ou PostgreSQL
- [x] Iniciar Fase 2 criando app `personagens`
- [x] Modelar `Personagem` com relação 1:N para usuário
- [x] Criar CRUD básico de personagens (listar, criar, editar, detalhar)

---

# 🔹 FASE 1 — FUNDAÇÃO

## Projeto
- [x] Criar projeto Django
- [x] Criar ambiente virtual
- [x] Instalar dependências
- [x] Configurar PostgreSQL
- [x] Rodar servidor inicial

## Usuários
- [x] Criar app de usuários (`accounts`)
- [x] Implementar modelo de usuário
- [x] Criar sistema de login
- [x] Criar sistema de cadastro
- [x] Criar logout
- [x] Criar página de perfil
- [x] Implementar tipos de usuário

---

# 🔹 FASE 2 — PERSONAGENS

- [x] Criar app `personagens`
- [x] Criar model Personagem
- [x] Relacionar com usuário (1:N)
- [x] Padronizar constantes de classes, guildas e status
- [x] Criar CRUD de personagens
- [x] Criar página de listagem
- [x] Criar página de detalhe
- [x] Criar formulário de criação
- [x] Criar edição de personagem

---

# 🔹 FASE 3 — CMS / PÁGINAS

- [ ] Criar app `paginas`
- [ ] Criar model Página
- [ ] Criar model Seção
- [ ] Criar edição via admin
- [ ] Criar home dinâmica
- [ ] Criar páginas institucionais

---

# 🔹 FASE 4 — CENÁRIO

- [ ] Criar app `cenario`
- [ ] Criar model História
- [ ] Criar model Local
- [ ] Criar model Facção/Guilda base
- [ ] Criar páginas públicas de cenário

---

# 🔹 FASE 5 — GUILDAS

- [ ] Criar app `guildas`
- [ ] Criar model Guilda
- [ ] Relacionar personagem com guilda
- [ ] Criar página de guilda
- [ ] Criar área pública da guilda
- [ ] Criar área privada da guilda
- [ ] Listar membros da guilda

---

# 🔹 FASE 6 — EVENTOS

- [ ] Criar app `eventos`
- [ ] Criar model Evento
- [ ] Criar CRUD de eventos
- [ ] Criar página de agenda
- [ ] Criar página de detalhe do evento

---

# 🔹 FASE 7 — INSCRIÇÕES

- [ ] Criar app `inscricoes`
- [ ] Criar model Inscrição
- [ ] Relacionar evento ↔ personagem
- [ ] Criar sistema de inscrição
- [ ] Listar participantes

---

# 🔹 FASE 8 — FORMULÁRIOS

- [ ] Criar app `formularios`
- [ ] Criar model Formulário
- [ ] Criar model Pergunta
- [ ] Criar model Resposta
- [ ] Criar tela de preenchimento
- [ ] Criar visualização de respostas

---

# 🔹 FASE 9 — CHAT

- [ ] Criar app `chat`
- [ ] Criar model Canal
- [ ] Criar model Mensagem
- [ ] Relacionar com guilda
- [ ] Permitir envio por personagem
- [ ] Criar interface de chat
- [ ] Criar mural simples (MVP)

---

# 🔹 FASE 10 — AVISOS

- [ ] Criar app `avisos`
- [ ] Criar model Aviso
- [ ] Criar avisos globais
- [ ] Criar avisos por guilda
- [ ] Exibir no dashboard

---

# 🔹 FASE 11 — SISTEMA DE JOGO (FUTURO)

- [ ] Criar app `sistema`
- [ ] Criar model XP
- [ ] Criar model Item
- [ ] Criar inventário
- [ ] Criar sistema de progressão

---

# 🔹 FASE 12 — NOTIFICAÇÕES

- [ ] Criar app `notificacoes`
- [ ] Criar model Notificação
- [ ] Criar sistema de envio
- [ ] Integrar com eventos e chat

---

# 🔹 FASE 13 — LOGS

- [ ] Criar app `logs`
- [ ] Criar model Log
- [ ] Registrar ações do sistema
- [ ] Criar histórico de alterações

---

# 🔹 FINALIZAÇÃO

- [ ] Testar sistema completo
- [ ] Corrigir bugs
- [ ] Popular banco com dados reais
- [ ] Ajustar layout
- [ ] Deploy inicial

---

# 🧠 REGRAS IMPORTANTES

- Nunca implementar tudo de uma vez
- Sempre validar antes de avançar
- Priorizar funcionalidades essenciais
- Manter código organizado por app
- Usar boas práticas Django

---

# 🚀 STATUS GLOBAL

- [x] Fase 1 completa
- [x] Fase 2 completa
- [ ] Fase 3 completa
- [ ] Fase 4 completa
- [ ] Fase 5 completa
- [ ] Fase 6 completa
- [ ] Fase 7 completa
- [ ] Fase 8 completa
- [ ] Fase 9 completa
- [ ] Fase 10 completa
- [ ] Fase 11 completa
- [ ] Fase 12 completa
- [ ] Fase 13 completa