# 🧩 Codex LARP — Sistema de Gerenciamento e Portal de LARP

## 📌 O que é o sistema

O Codex LARP é um sistema web completo para gerenciamento e centralização de um LARP (Live Action Role Play).

Ele funciona como:
- Portal informativo do mundo
- Sistema de criação e gerenciamento de personagens
- Plataforma de eventos (LARPs)
- Sistema de formulários
- CMS (edição de conteúdo pelo admin)
- Hub social (guildas + chat por personagem)

---

## 🎯 Objetivo do sistema

Centralizar TODAS as informações e interações do LARP em um único lugar.

Resolver problemas como:
- informações espalhadas
- dificuldade de gerenciar personagens
- falta de controle de eventos
- ausência de organização de lore
- comunicação descentralizada

---

## 👥 Tipos de usuário

### Jogador
- cria conta
- cria e gerencia personagens
- participa de eventos
- responde formulários
- interage em guildas

### Admin / Mestre
- gerencia conteúdo do sistema
- cria eventos
- cria formulários
- edita cenário
- gerencia personagens
- modera guildas e chat

### Superadmin
- controle total do sistema
- gerencia admins
- controla permissões

---

## 🧠 Estrutura geral do sistema

O sistema é dividido em módulos independentes:

- usuarios
- personagens
- guildas
- chat
- paginas (CMS)
- cenario
- regras
- eventos
- inscricoes
- formularios
- avisos
- sistema (XP, itens)
- notificacoes
- logs

---

## 🧙‍♂️ Personagens

- Um usuário pode ter múltiplos personagens
- Cada personagem pertence a uma guilda
- Possui:
  - nome
  - história
  - classe
  - status
  - XP
  - ouro

---

## 🛡️ Guildas

Cada guilda possui:

- página própria
- lore exclusiva
- membros
- chat interno
- área pública e privada

### Funcionalidades:
- listar membros
- exibir história
- avisos internos
- comunicação entre personagens

---

## 💬 Chat por Personagem

- mensagens enviadas como personagem
- não como usuário

### Tipos:
- IC (in character)
- OOC (out of character)

### Regras:
- só membros da guilda participam
- admin pode moderar

---

## 🌍 Cenário / Mundo

Conteúdo do universo:

- história
- locais
- facções
- eventos históricos

Gerenciado por admin via painel.

---

## 📜 CMS (Páginas)

Admin pode editar:

- home
- páginas institucionais
- textos do cenário
- seções dinâmicas

Sem necessidade de alterar código.

---

## 📅 Eventos (LARP)

- criação de eventos
- agenda
- inscrições por personagem

---

## 📋 Formulários

- criação de formulários personalizados
- perguntas dinâmicas
- coleta de respostas

---

## 📢 Avisos

- avisos globais
- avisos por guilda
- exibidos no dashboard

---

## 🎒 Sistema de Jogo (futuro)

- XP
- itens
- inventário
- progressão

---

## 🔔 Notificações

- eventos
- mensagens
- respostas
- avisos

---

## 🏗️ Stack Tecnológica

- Backend: Django
- Banco: PostgreSQL
- Frontend: Django Templates + Bootstrap
- Admin: Django Admin

---

## 🚀 Plano estratégico de desenvolvimento

### Fase 1 — Fundação
- autenticação
- usuários
- personagens

### Fase 2 — Conteúdo
- páginas (CMS)
- cenário
- regras

### Fase 3 — Guildas
- guildas
- membros
- páginas de guilda

### Fase 4 — Eventos
- eventos
- inscrições

### Fase 5 — Formulários
- criação de forms
- respostas

### Fase 6 — Social
- chat por guilda

### Fase 7 — Avançado
- sistema de jogo (XP, itens)
- notificações
- logs

---

## 🧠 Resumo

O sistema é um:

> Portal + CMS + Sistema de RPG + Rede social de personagens

---

## ⚠️ Diretrizes para desenvolvimento (IA)

- sempre modularizar
- seguir separação por apps
- evitar lógica duplicada
- usar boas práticas Django
- priorizar MVP antes de features avançadas