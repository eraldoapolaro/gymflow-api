# AGENTS.md — Governança dos Agentes de IA no Desenvolvimento SDD

> **Metodologia:** Spec-Driven Development (SDD) com Assistência de IA  
> **Framework:** Antigravity AI Engine (Google DeepMind)  
> **Projeto:** GymFlow API  

---

## 1. Visão Geral da Abordagem SDD com IA

No modelo tradicional, o desenvolvimento assistido por IA frequentemente sofre com alucinações de escopo e falta de aderência a contratos. No **Spec-Driven Development (SDD)**, o processo é rigorosamente delimitado por especificações e dividido em **Personas Especializadas de Agentes**:

```text
┌────────────────┐      ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│   [SPEC.md]    │ ───► │  [Tech Lead]   │ ───► │[Backend Coder] │ ───► │ [QA Engineer]  │
│  Design-First  │      │ Planeja Fases  │      │ Implementa ORM │      │ Roda Pytest    │
│  OpenAPI 3.1   │      │   em PLAN.md   │      │ e Routers HTTP │      │ 32 Testes 100% │
└────────────────┘      └────────────────┘      └────────────────┘      └────────────────┘
```

---

## 2. Personas e Papéis de Agentes

### 2.1. Persona 1: `[Tech Lead]` (Arquiteto de Software & Planejador)
- **Responsabilidade:** Interpretar o [SPEC.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/SPEC.md), estabelecer as diretrizes inegociáveis de arquitetura (Schema-First, RFC 9457, camelCase no wire, ORM desacoplado) e redigir o roteiro granular de execução [PLAN.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/PLAN.md).
- **Entregáveis:** [PLAN.md](file:///c:/Users/eeral/.gemini/antigravity/scratch/gymflow-api/PLAN.md) com as 7 fases de implementação e matriz de rastreabilidade (Definition of Done).

### 2.2. Persona 2: `[Backend Coder]` (Engenheiro de Implementação)
- **Responsabilidade:** Escrever o código-fonte seguindo estritamente as diretrizes do Tech Lead.
  - Fase 1: Estrutura modular e dependências (`requirements.txt`, `pytest.ini`).
  - Fase 2: Schemas Pydantic v2 com validações rigorosas (`schemas.py`).
  - Fase 3: Segurança com bcrypt e JWT Bearer (`security.py`, `dependencies.py`).
  - Fase 4: Modelagem ORM declarativa em SQLAlchemy 2.0 (`models.py`, `database.py`).
  - Fase 5: Handlers RFC 9457 e Middleware de JSON malformado (`exceptions.py`, `main.py`).
  - Fase 6: Roteadores HTTP modularizados (`routers/auth.py`, `students.py`, `workouts.py`, `executions.py`).

### 2.3. Persona 3: `[QA Engineer]` (Engenheiro de Qualidade & Homologação)
- **Responsabilidade:** Criar e executar a suíte de testes automatizados com pytest, validando cada critério de aceite com fixtures e isolamento de banco de dados.
- **Entregáveis:** Suíte de 32 testes automatizados em `src/api/tests/` com 100% de aprovação comprovada via terminal.

---

## 3. Registro de Decisões Arquiteturais (ADRs)

| ADR | Decisão | Justificativa |
| :--- | :--- | :--- |
| **ADR-01** | Uso de Pydantic v2 com `CamelModel` | Garante tipagem estrita, conversão transparente de `camelCase` (wire) para `snake_case` (domínio) e validação em tempo de execução. |
| **ADR-02** | Adoção do SQLAlchemy 2.0 ORM | Permite persistência relacional com tipagem estrita (`Mapped`, `mapped_column`), integridade referencial via Foreign Keys e deleção em cascata. |
| **ADR-03** | Conformidade com RFC 9457 (Problem Details) | Elimina o formato padrão proprietário do FastAPI (`{"detail": "..."}`), fornecendo estrutura semântica universal de erros HTTP. |
| **ADR-04** | Interceptação de JSON Malformado em Middleware | Captura sintaxes JSON corrompidas antes do pipeline do framework, retornando HTTP 400 estruturado imediatamente. |
| **ADR-05** | Isolamento de Testes via Reset Determinístico | Fixture `autouse=True` com recriação de schema e seeds no SQLite in-memory, garantindo testes 100% idempotentes e sem efeitos colaterais. |
