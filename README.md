# GymFlow API — Gestão de Treinos e Acompanhamento Físico

[![CI Test Suite](https://github.com/gymflow/gymflow-api/actions/workflows/ci.yml/badge.svg)](https://github.com)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/ORM-SQLAlchemy%202.0-red.svg)](https://www.sqlalchemy.org/)
[![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1.0-brightgreen.svg)](https://swagger.io/)
[![RFC 9457](https://img.shields.io/badge/Errors-RFC%209457-orange.svg)](https://datatracker.ietf.org/doc/html/rfc9457)
[![Tests 32/32 Passed](https://img.shields.io/badge/Tests-32%2F32%20Passed-success.svg)](https://docs.pytest.org/)

> **Projeto Semestral de Arquitetura de Software & Desenvolvimento de APIs REST**  
> **Metodologia:** Spec-Driven Development (SDD) com Agentes de IA  
> **Homologação:** 100% de Aprovação nos Testes Automatizados (Pytest)  

---

## 📌 Sumário Executivo para Avaliação (Critérios da Disciplina)

| # | Critério de Avaliação | Onde Encontrar no Repositório | Status |
| :-: | :--- | :--- | :---: |
| **1** | **Organização da Equipe** | [Seção 1: Equipe Envolvida](#1-organização-da-equipe) e papéis definidos | ✅ Concluído |
| **2** | **Desenvolvimento com IA usando SDD** | [SPEC.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/SPEC.md), [PLAN.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/PLAN.md), [AGENTS.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/AGENTS.md) e [STYLEGUIDE.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/STYLEGUIDE.md) | ✅ Concluído |
| **3** | **Arquivos de Especificação** | [gymflow_apidog.json](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/gymflow_apidog.json), Swagger (`/docs`) e ReDoc (`/redoc`) | ✅ Concluído |
| **4** | **Autenticação & RBAC** | `src/api/security.py`, `src/api/dependencies.py` e rotas em `src/api/routers/auth.py` | ✅ Concluído |
| **5** | **ORM (Object-Relational Mapping)** | `src/api/models.py` (SQLAlchemy 2.0 Declarativo) e `src/api/database.py` | ✅ Concluído |
| **6** | **Testes Automatizados** | 32 testes em `src/api/tests/` (100% passando com `pytest -v`) | ✅ Concluído |
| **7** | **Conteúdos Extras** | Dockerfile, Docker Compose, GitHub Actions CI, `api.http` e Cloud Mock | ✅ Concluído |
| **8** | **Demonstração Funcional** | [Seção 8: Roteiro de Demonstração ao Vivo](#8-roteiro-de-demonstração-funcional-ao-vivo) | ✅ Concluído |

---

## 1. Organização da Equipe

| **Eraldo Apolaro** - 2840482421024

---

## 2. Desenvolvimento com IA usando SDD (Spec-Driven Development)

O projeto adotou a metodologia **Spec-Driven Development (SDD)**, orientada a especificações antes da codificação:

```text
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│     SPEC.md     │ ───► │     PLAN.md     │ ───► │  Código + ORM   │ ───► │ 32 Testes Pytest│
│ Contrato OpenAPI│      │ 7 Fases do Líder│      │ Implementação   │      │ 100% Aprovados  │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

1. **[SPEC.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/SPEC.md)** 
2. **[PLAN.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/PLAN.md)**
3. **[AGENTS.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/AGENTS.md)**
4. **[STYLEGUIDE.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/STYLEGUIDE.md)**

---

## 3. Arquivos de Especificação & Design-First

- **Contrato OpenAPI 3.1.0 Completo:** [gymflow_apidog.json](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/gymflow_apidog.json)
  - 12 rotas modeladas e 26 schemas desacoplados (zero objetos inline).
  - Regras dinâmicas de Faker.js / Mock.js (`@guid`, `@name`, `@email`, `@datetime`, `@float`).
- **Documentação Swagger Interativa:** `http://127.0.0.1:8000/docs`
- **Documentação ReDoc:** `http://127.0.0.1:8000/redoc`

---

## 4. Autenticação & Segurança (RBAC)

- **Criptografia de Senhas:** Hash seguro com `bcrypt` e salt dinâmico via `passlib`.
- **Tokens JWT Stateless:** Algoritmo `HS256`, claim `sub`, papel de usuário `role` e expiração de 24h.
- **Role-Based Access Control (RBAC):**
  - Injeção de dependências via `FastAPI Depends`: `get_current_user`, `require_personal`, `require_student`.
  - Rotas exclusivas de Personal (`require_personal`): Cadastro de alunos, montagem de treinos, prescrição de exercícios.
  - Rotas exclusivas de Aluno (`require_student`): Registro de execução e feedback RPE.
  - Segregação de carteira: Alunos só acessam seus próprios treinos; Personals só acessam seus alunos.

---

## 5. Camada de Persistência & ORM (SQLAlchemy 2.0)

Mapeamento relacional declarativo moderno em `src/api/models.py`:

```mermaid
erDiagram
    User ||--o{ StudentProfile : "possui"
    User ||--o{ WorkoutPlan : "prescreve / recebe"
    WorkoutPlan ||--|{ WorkoutRoutine : "composto por"
    WorkoutRoutine ||--|{ WorkoutExercise : "contém"
    WorkoutRoutine ||--o{ Execution : "registrado em"
    User ||--o{ Execution : "executa"
```

- **Modelos Mapeados:**
  - `User`: Personal Trainers e Alunos com vínculo relacional.
  - `StudentProfile`: Dados biométricos, metas e observações.
  - `WorkoutPlan`: Fichas periodizadas com status e vigência.
  - `WorkoutRoutine`: Divisões de treino (A, B, C...) com ordenação.
  - `WorkoutExercise`: Exercícios técnicos com grupamentos musculares, séries e carga.
  - `Execution`: Sessões realizadas com duração, pontuação RPE (1-10) e feedback.
- **Recursos Avançados de ORM:**
  - Tipagem moderna via `Mapped[...]` e `mapped_column(...)`.
  - Integridade referencial com Foreign Keys e `cascade="all, delete-orphan"`.
  - Carregamento otimizado de relacionamentos via `selectinload`.

---

## 6. Testes Automatizados (32 Testes 100% Aprovados)

A suíte em `src/api/tests/` garante isolamento e idempotência total por meio de fixtures determinísticas em `conftest.py`:

```bash
pytest -v
```

**Resultado da Execução:**
```text
src/api/tests/test_auth.py (8 testes) ................ PASSED
src/api/tests/test_students.py (8 testes) ............ PASSED
src/api/tests/test_workouts.py (8 testes) ............ PASSED
src/api/tests/test_executions.py (4 testes) .......... PASSED
src/api/tests/test_errors.py (4 testes) .............. PASSED
======================== 32 passed in 2.49s ========================
```

---

## 7. Conteúdos Extras

1. **Containerização Docker:**
   - [Dockerfile](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/Dockerfile) multi-stage otimizado.
   - [docker-compose.yml](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/docker-compose.yml) para inicialização em 1 comando.
2. **Integração Contínua (CI):**
   - Workflow do GitHub Actions em [.github/workflows/ci.yml](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/.github/workflows/ci.yml) rodando os testes a cada push.
3. **Arquivo de Testes HTTP para Demonstração:**
   - [api.http](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/api.http) para rodar requisições diretamente do VS Code com extensão REST Client / Thunder Client.
4. **Resiliência e RFC 9457:**
   - Middleware interceptador de JSON malformado e tratamento semântico universal sem vazamento de `{"detail": "..."}`.

---