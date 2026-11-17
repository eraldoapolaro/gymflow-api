# SPEC.md — Especificação de Requisitos e Arquitetura do Sistema

> **Projeto:** GymFlow API (Gestão de Treinos e Acompanhamento Físico)  
> **Abordagem:** Spec-Driven Development (SDD) & Design-First  
> **Versão:** 1.0.0  
> **Status:** Aprovado para Implementação e Homologado  

---

## 1. Visão Geral do Produto

### 1.1. Problema de Negócio
No acompanhamento de consultorias fitness e academias, Personal Trainers enfrentam dificuldades para centralizar o histórico de seus alunos, prescrever divisões de treino (A/B/C) com clareza técnica e auditar o esforço real despendido durante as sessões. Por outro lado, os alunos carecem de uma interface estruturada para consultar exercícios, séries, repetições e registrar seu feedback imediato pós-treino.

### 1.2. Solução Proposta
A **GymFlow API** é uma API RESTful de alta performance que conecta Personal Trainers e seus Alunos, garantindo:
- Gestão de carteira de alunos e perfis biométricos.
- Montagem modular de planos de treino, rotinas e exercícios prescritos.
- Check-in de execução com duração, pontuação na **Escala RPE Borg (1 a 10)** e feedback qualitativo.
- Autenticação stateless com JWT Bearer e controle de acesso baseado em papéis (RBAC).
- Respostas de erro estritamente em conformidade com a **RFC 9457 (Problem Details)**.

---

## 2. Requisitos do Sistema

### 2.1. Requisitos Funcionais (RF)
- **RF01 - Autenticação e Registro:** O sistema deve permitir o cadastro de usuários com os papéis `PERSONAL` ou `STUDENT`. Para o papel `PERSONAL`, o registro profissional (CREF) é obrigatório.
- **RF02 - Login Seguro:** O sistema deve autenticar usuários via e-mail e senha, emitindo um token JWT Bearer com validade de 24 horas.
- **RF03 - Gestão da Carteira de Alunos:** O Personal Trainer deve poder cadastrar, listar (com paginação e filtros), consultar detalhes, atualizar perfil e remover alunos de sua carteira.
- **RF04 - Segregação de Dados do Aluno:** Um aluno só pode consultar seu próprio perfil físico e histórico; não deve ter acesso a dados de outros alunos.
- **RF05 - Prescrição de Fichas de Treino:** O Personal Trainer deve criar planos de treino com período de vigência e status (`ACTIVE`, `INACTIVE`, `ARCHIVED`), vinculando rotinas (ex.: Treino A, Treino B) e exercícios com séries, repetições, carga e descanso.
- **RF06 - Consulta de Treino pelo Aluno:** O aluno pode visualizar as fichas de treino que lhe foram atribuídas pelo seu Personal Trainer, com rotinas e exercícios ordenados.
- **RF07 - Registro de Execução (Check-in):** O aluno deve registrar a conclusão de uma rotina de treino informando duração em minutos (1 a 360), pontuação na escala RPE (1 a 10) e feedback textual opcional.
- **RF08 - Auditoria de Histórico:** O Personal Trainer e o próprio Aluno podem consultar o histórico cronológico de execuções com métricas de esforço.

### 2.2. Requisitos Não Funcionais (RNF)
- **RNF01 - Schema-First & Pydantic v2:** 100% dos contratos de entrada e saída devem ser modelados com Pydantic v2, com serialização automática em `camelCase`.
- **RNF02 - Persistência ORM:** A camada de dados deve utilizar o ORM SQLAlchemy 2.0 com mapeamento declarativo moderno (`Mapped`, `mapped_column`, `relationship`, chaves estrangeiras e deleção em cascata).
- **RNF03 - RFC 9457 Strict Error Handling:** Toda resposta de erro HTTP (400, 401, 403, 404, 422, 500) deve seguir o schema `ApiError` com lista `invalidParams` quando aplicável.
- **RNF04 - Middleware de JSON Malformado:** Requisições `POST`, `PUT` ou `PATCH` com header `Content-Type: application/json` e payload sintaticamente corrompido devem ser interceptadas e responder imediatamente `400 Bad Request` no schema RFC 9457.
- **RNF05 - Testes Automatizados:** Cobertura de testes unitários e de integração com pytest, garantindo isolamento total por meio de reset determinístico de banco.

---

## 3. Modelo de Dados e Relacionamentos (ORM)

```text
[User (Personal)] 1 ─── N [User (Student)]
       │                          │
       │ prescreve                │ possui
       ▼                          ▼
[WorkoutPlan] 1 ───────── [StudentProfile]
       │
       └── 1 ─── N [WorkoutRoutine]
                         │
                         ├── 1 ─── N [WorkoutExercise]
                         └── 1 ─── N [Execution] ◄─── (registrado pelo Student)
```

---

## 4. Matriz de Endpoints da API

| Método | Endpoint | Papel Mínimo | Descrição | Status Sucesso |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Público | Cadastro de novo usuário (Personal/Aluno) | 201 Created |
| `POST` | `/api/v1/auth/login` | Público | Login e emissão de token JWT | 200 OK |
| `GET` | `/api/v1/auth/me` | Autenticado | Dados do usuário autenticado | 200 OK |
| `GET` | `/api/v1/students` | Personal | Listar alunos da carteira (com paginação) | 200 OK |
| `POST` | `/api/v1/students` | Personal | Cadastrar novo aluno na carteira | 201 Created |
| `GET` | `/api/v1/students/{id}` | Personal/Aluno | Detalhes cadastrais e perfil físico do aluno | 200 OK |
| `PATCH` | `/api/v1/students/{id}` | Personal | Atualizar dados cadastrais e perfil físico | 200 OK |
| `DELETE` | `/api/v1/students/{id}` | Personal | Remover aluno da carteira | 204 No Content |
| `GET` | `/api/v1/workouts` | Autenticado | Listar planos de treino (filtro automático por papel) | 200 OK |
| `POST` | `/api/v1/workouts` | Personal | Criar plano de treino com rotinas e exercícios | 201 Created |
| `GET` | `/api/v1/workouts/{id}` | Personal/Aluno | Obter plano de treino completo por ID | 200 OK |
| `PATCH` | `/api/v1/workouts/{id}` | Personal | Atualizar metadados do plano de treino | 200 OK |
| `DELETE` | `/api/v1/workouts/{id}` | Personal | Remover plano de treino em cascata | 204 No Content |
| `POST` | `/api/v1/workouts/{id}/routines` | Personal | Adicionar divisão (rotina) a um plano existente | 201 Created |
| `POST` | `/api/v1/routines/{id}/exercises` | Personal | Adicionar exercício técnico à rotina | 201 Created |
| `DELETE` | `/api/v1/exercises/{id}` | Personal | Remover exercício da rotina | 204 No Content |
| `POST` | `/api/v1/routines/{id}/executions` | Aluno | Registrar check-in de treino com RPE e feedback | 201 Created |
| `GET` | `/api/v1/students/{id}/executions` | Personal/Aluno | Histórico cronológico de execuções do aluno | 200 OK |
