# PLAN.md — Plano Técnico de Implementação (GymFlow API — Personal & Aluno)

> **Documento de Governança Técnica — Spec-Driven Development (SDD)**  
> **Papel Atual:** `[Tech Lead]` (Arquiteto & Planejador) & `[QA Engineer]`  
> **Status:** Concluído com Sucesso e Aprovado nos Testes (100% Passed)  
> **Fontes da Verdade:** SPEC.md, STYLEGUIDE.md e AGENTS.md

---

## 1. Visão Geral e Princípios Arquiteturais (Tech Lead Directives)

Como **Tech Lead**, a concepção e implementação da **GymFlow API** deve resolver o ecossistema de gestão de treinos e acompanhamento físico entre **Personal Trainers** e seus **Alunos**, aplicando com rigor metodológico a abordagem **Schema-First**, orientada a contratos e alinhada à especificação OpenAPI 3.1 / Apidog.

### 1.1. Pilares Inegociáveis de Arquitetura
1. **Schema-First Rigoroso:** Toda a modelagem de domínio e contratos de dados nasce dos modelos Pydantic v2 em `schemas.py`, espelhando fielmente os schemas da especificação antes da implementação de qualquer lógica de persistência ou rotas HTTP.
2. **Conformidade Estrita com RFC 9457 (Problem Details):** É terminantemente proibido retornar respostas de erro no formato padrão do FastAPI (`{"detail": "..."}`). Todo erro (400, 401, 403, 404, 409, 422, 500) DEVE aderir ao schema `ApiError` com lista `invalidParams` quando aplicável.
3. **Nomenclatura CamelCase no Wire, SnakeCase no Domínio:** Os payloads JSON de entrada e saída devem preservar rigorosamente a notação `camelCase` (`personalId`, `studentId`, `workoutPlanId`, `routineId`, `muscleGroup`, `restSeconds`, `weightKg`, `rpeScore`, `durationMinutes`, `createdAt`, `updatedAt`, `accessToken`, `tokenType`, `invalidParams`). No código interno Python, deve-se adotar `snake_case` com conversão transparente via Pydantic `to_camel`.
4. **Isolamento de Persistência e Thread-Safety:** Camada de dados centralizada em `database.py`, thread-safe via `threading.RLock`, permitindo mutações seguras em memória e desacoplada dos roteadores HTTP (facilitando futura transição para PostgreSQL / SQLAlchemy 2.0).
5. **Segurança e RBAC (Role-Based Access Control):** Autenticação stateless via JWT Bearer (HS256) com hash de senhas criptografado via `passlib[bcrypt]`. Proteção de rotas com injeção de dependências (`get_current_user`, `require_personal`, `require_student`).
6. **Autonomia e Idempotência de Testes:** Fixtures de teste com isolamento total via `reset_database()` antes de cada asserção, cobrindo fluxos de sucesso, segregação de permissões (RBAC) e cenários de exceção.

### 1.2. Mapeamento de Conciliação e Regras de Negócio
- **Fluxo do Personal Trainer:**
  - Login seguro -> Listagem/cadastro de alunos -> Montagem de planos de treino compostos por rotinas (Treino A, B, C...) e exercícios com prescrição técnica (séries, repetições, carga sugerida, descanso) -> Acompanhamento do histórico de execuções e pontuação RPE dos alunos.
- **Fluxo do Aluno:**
  - Login seguro -> Consulta aos planos de treino atribuídos pelo seu personal -> Visualização detalhada das rotinas e exercícios prescritos -> Registro de execução (check-in) com duração, pontuação RPE (1-10) e feedback textual.
- **Envelope Padronizado de Paginação:**
  - Implementação padronizada de `PaginationMeta` (`page`, `limit`, `totalItems`, `totalPages`, `hasNext`) em listagens de alunos e planos de treino.
- **UUID de Simulação 404 (`00000000-0000-0000-0000-000000000000`):**
  - Qualquer consulta, atualização ou remoção sobre este identificador em qualquer recurso retorna determinísticamente `404 Not Found` no schema RFC 9457 com `type: "https://api.gymflow.dev/errors/not-found"` e `title: "Recurso Inexistente"`.
- **Middleware de Interceptação de JSON Malformado:**
  - Requisições `POST`, `PUT` ou `PATCH` com header `Content-Type: application/json` e sintaxe JSON corrompida são interceptadas antes dos handlers de rota, respondendo imediatamente `400 Bad Request` no schema RFC 9457.

---

## 2. Estrutura Canônica de Arquivos e Módulos

O projeto segue a seguinte organização arquitetural modular:

```text
gymflow-api/
├── PLAN.md                  # Este roteiro de governança técnica e checklist
├── pytest.ini               # Configuração do executor pytest (pythonpath = src)
└── src/
    └── api/
        ├── __init__.py
        ├── main.py          # App FastAPI, CORS, middleware de JSON malformado e include dos routers
        ├── schemas.py       # Contratos Pydantic v2 estritos espelhando os Schemas da especificação
        ├── database.py      # Camada de persistência thread-safe, seed determinístico e CRUD em memória
        ├── security.py      # Hashing de senhas (bcrypt) e geração/validação de tokens JWT (HS256)
        ├── dependencies.py  # Injeção de dependências RBAC (get_current_user, require_personal, require_student)
        ├── exceptions.py    # Exceções de domínio e handlers globais no padrão RFC 9457 (Problem Details)
        ├── requirements.txt # Dependências fixadas do projeto
        ├── routers/
        │   ├── __init__.py
        │   ├── auth.py      # Endpoints /api/v1/auth (register, login, me)
        │   ├── students.py  # Endpoints /api/v1/students (gestão da carteira de alunos)
        │   ├── workouts.py  # Endpoints /api/v1/workouts, /routines e /exercises (fichas e montagem de treino)
        │   └── executions.py# Endpoints /api/v1/routines/.../executions e histórico
        └── tests/
            ├── __init__.py
            ├── conftest.py      # Fixtures de TestClient, tokens JWT (Personal/Aluno) e reset de banco
            ├── test_auth.py     # Testes de registro, login e proteção de rotas
            ├── test_students.py # Testes de gestão e segregação de alunos
            ├── test_workouts.py # Testes de criação, divisões (A/B/C) e exercícios de treino
            ├── test_executions.py # Testes de realização do treino pelo aluno e feedback
            └── test_errors.py   # Testes de conformidade com RFC 9457 (400, 401, 403, 404, 422)
```

---

## 3. Checklist Sequencial e Granular de Implementação

### FASE 1: Inicialização do Ambiente, Estrutura e Dependências
- [x] **1.1. Estruturação da Árvore de Diretórios:**
  - Criar os diretórios `src/api/`, `src/api/routers/` e `src/api/tests/`.
  - Criar arquivos vazios `__init__.py` em todos os pacotes para garantir a correta importação de módulos.
- [x] **1.2. Definição do Arquivo de Dependências (`requirements.txt`):**
  - Fixar dependências estritas:
    - `fastapi>=0.110.0,<1.0.0`
    - `uvicorn[standard]>=0.28.0,<1.0.0`
    - `pydantic>=2.6.0,<3.0.0`
    - `pydantic[email]>=2.6.0,<3.0.0`
    - `python-jose[cryptography]>=3.3.0,<4.0.0`
    - `passlib[bcrypt]>=1.7.4,<2.0.0`
    - `pytest>=8.0.0,<9.0.0`
    - `httpx>=0.27.0,<1.0.0`
- [x] **1.3. Configuração do Executor de Testes (`pytest.ini`):**
  - Criar `pytest.ini` na raiz com:
    - `pythonpath = src`
    - `testpaths = src/api/tests`
    - `addopts = -v -s --strict-markers`
  - Garantir compatibilidade plena com o runtime Python 3.12+.

---

### FASE 2: Geração de Tipos Pydantic v2 a partir dos Schemas (`schemas.py`)
- [x] **2.1. Definição dos Enums de Domínio:**
  - `UserRole(str, Enum)`: `"PERSONAL"`, `"STUDENT"`.
  - `FitnessGoal(str, Enum)`: `"HYPERTROPHY"`, `"WEIGHT_LOSS"`, `"CONDITIONING"`, `"REHABILITATION"`, `"GENERAL_FITNESS"`.
  - `MuscleGroup(str, Enum)`: `"CHEST"`, `"BACK"`, `"LEGS"`, `"SHOULDERS"`, `"BICEPS"`, `"TRICEPS"`, `"CORE"`, `"CARDIO"`, `"FULL_BODY"`.
  - `WorkoutStatus(str, Enum)`: `"ACTIVE"`, `"INACTIVE"`, `"ARCHIVED"`.
- [x] **2.2. Base Model com Aliases CamelCase (`CamelModel`):**
  - Criar `CamelModel(BaseModel)` configurado com `ConfigDict`:
    - `populate_by_name = True`
    - `alias_generator = to_camel`
    - `from_attributes = True`
- [x] **2.3. Modelos de Erro RFC 9457 (Problem Details):**
  - `InvalidParam(CamelModel)`: `name: str`, `reason: str`.
  - `ApiError(CamelModel)`: `type: str`, `title: str`, `status: int`, `detail: str`, `instance: str`, `invalidParams: Optional[List[InvalidParam]] = None`.
- [x] **2.4. Modelos de Paginação e Metadados:**
  - `PaginationMeta(CamelModel)`: `page: int` (ge=1), `limit: int` (ge=1, le=100), `totalItems: int` (ge=0), `totalPages: int` (ge=0), `hasNext: bool`.
- [x] **2.5. Modelos de Usuário e Autenticação:**
  - `RegisterUserDTO(CamelModel)`:
    - `name: str` (min_length=3, max_length=100)
    - `email: EmailStr`
    - `password: str` (min_length=6)
    - `role: UserRole`
    - `phone: Optional[str] = None`
    - `cref: Optional[str] = None`
    - Validador `@model_validator(mode="after")` para garantir que se `role == UserRole.PERSONAL`, `cref` seja obrigatório e não vazio.
  - `LoginRequestDTO(CamelModel)`:
    - `email: EmailStr`
    - `password: str`
  - `UserResponse(CamelModel)`:
    - `id: UUID`, `name: str`, `email: str`, `role: UserRole`, `phone: Optional[str]`, `cref: Optional[str]`, `createdAt: datetime`, `updatedAt: datetime`.
  - `AuthTokenResponse(CamelModel)`:
    - `accessToken: str`, `tokenType: str = "bearer"`, `user: UserResponse`.
- [x] **2.6. Modelos de Aluno e Perfil Físico:**
  - `StudentProfileDTO(CamelModel)`:
    - `birthDate: Optional[date] = None`, `weightKg: Optional[float] = None` (gt=0), `heightCm: Optional[float] = None` (gt=0), `goal: FitnessGoal`, `notes: Optional[str] = None` (max_length=500).
  - `CreateStudentDTO(CamelModel)`:
    - `name: str` (min_length=3, max_length=100), `email: EmailStr`, `password: str` (min_length=6), `phone: Optional[str] = None`, `profile: Optional[StudentProfileDTO] = None`.
  - `UpdateStudentDTO(CamelModel)`:
    - `name: Optional[str] = None` (min_length=3, max_length=100), `phone: Optional[str] = None`, `profile: Optional[StudentProfileDTO] = None`.
  - `StudentResponse(CamelModel)`:
    - `id: UUID`, `personalId: UUID`, `name: str`, `email: str`, `role: UserRole = UserRole.STUDENT`, `phone: Optional[str]`, `profile: Optional[StudentProfileDTO]`, `createdAt: datetime`, `updatedAt: datetime`.
  - `PaginatedStudentsResponse(CamelModel)`:
    - `data: List[StudentResponse]`, `meta: PaginationMeta`.
- [x] **2.7. Modelos de Exercícios, Rotinas e Planos de Treino:**
  - `WorkoutExerciseDTO(CamelModel)`:
    - `name: str` (min_length=2, max_length=100), `muscleGroup: MuscleGroup`, `sets: int` (ge=1, le=20), `reps: str` (max_length=30), `restSeconds: int` (ge=0, le=600), `weightKg: Optional[float] = None` (ge=0), `notes: Optional[str] = None` (max_length=300), `order: int` (ge=1).
  - `WorkoutExerciseResponse(CamelModel)`:
    - `id: UUID`, `routineId: UUID`, `name: str`, `muscleGroup: MuscleGroup`, `sets: int`, `reps: str`, `restSeconds: int`, `weightKg: Optional[float]`, `notes: Optional[str]`, `order: int`, `createdAt: datetime`.
  - `WorkoutRoutineDTO(CamelModel)`:
    - `name: str` (min_length=2, max_length=80), `dayOfWeek: Optional[str] = None`, `order: int` (ge=1), `exercises: Optional[List[WorkoutExerciseDTO]] = []`.
  - `WorkoutRoutineResponse(CamelModel)`:
    - `id: UUID`, `workoutPlanId: UUID`, `name: str`, `dayOfWeek: Optional[str]`, `order: int`, `exercises: List[WorkoutExerciseResponse]`, `createdAt: datetime`.
  - `CreateWorkoutPlanDTO(CamelModel)`:
    - `studentId: UUID`, `title: str` (min_length=3, max_length=100), `description: Optional[str] = None` (max_length=500), `startDate: date`, `endDate: Optional[date] = None`, `status: WorkoutStatus = WorkoutStatus.ACTIVE`, `routines: Optional[List[WorkoutRoutineDTO]] = []`.
  - `UpdateWorkoutPlanDTO(CamelModel)`:
    - `title: Optional[str] = None` (min_length=3, max_length=100), `description: Optional[str] = None` (max_length=500), `startDate: Optional[date] = None`, `endDate: Optional[date] = None`, `status: Optional[WorkoutStatus] = None`.
  - `WorkoutPlanResponse(CamelModel)`:
    - `id: UUID`, `personalId: UUID`, `studentId: UUID`, `title: str`, `description: Optional[str]`, `status: WorkoutStatus`, `startDate: date`, `endDate: Optional[date]`, `routines: List[WorkoutRoutineResponse]`, `createdAt: datetime`, `updatedAt: datetime`.
  - `PaginatedWorkoutsResponse(CamelModel)`:
    - `data: List[WorkoutPlanResponse]`, `meta: PaginationMeta`.
- [x] **2.8. Modelos de Execução de Treino:**
  - `CreateExecutionDTO(CamelModel)`:
    - `durationMinutes: int` (ge=1, le=360), `rpeScore: int` (ge=1, le=10), `feedback: Optional[str] = None` (max_length=500), `completedAt: Optional[datetime] = None`.
  - `ExecutionResponse(CamelModel)`:
    - `id: UUID`, `studentId: UUID`, `routineId: UUID`, `durationMinutes: int`, `rpeScore: int`, `feedback: Optional[str]`, `completedAt: datetime`, `createdAt: datetime`.

---

### FASE 3: Camada de Segurança, JWT e RBAC (`security.py` & `dependencies.py`)
- [x] **3.1. Hashing e Validação Criptográfica de Senhas (`security.py`):**
  - Instanciar `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`.
  - Implementar `hash_password(password: str) -> str`.
  - Implementar `verify_password(plain_password: str, hashed_password: str) -> bool`.
- [x] **3.2. Manipulação de Tokens JWT (`security.py`):**
  - Definir constantes: `SECRET_KEY = "gymflow-secret-super-key-2026"`, `ALGORITHM = "HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24h).
  - Implementar `create_access_token(data: dict) -> str` injetando claims `sub`, `role` e `exp`.
  - Implementar `decode_access_token(token: str) -> Optional[dict]` tratando exceções de assinatura e expiração.
- [x] **3.3. Injeção de Dependências de Autenticação e RBAC (`dependencies.py`):**
  - Configurar `oauth2_scheme = HTTPBearer(auto_error=False)`.
  - Implementar `get_current_user`:
    - Validar presença do header Authorization Bearer.
    - Decodificar token JWT. Se ausente, corrompido ou expirado, lançar `UnauthorizedException` (HTTP 401 RFC 9457).
    - Buscar usuário correspondente no banco. Se inexistente, lançar `UnauthorizedException`.
    - Retornar o registro do usuário autenticado.
  - Implementar `require_personal(current_user = Depends(get_current_user))`:
    - Validar se `current_user["role"] == "PERSONAL"`. Se falso, disparar `ForbiddenException` (HTTP 403 RFC 9457).
  - Implementar `require_student(current_user = Depends(get_current_user))`:
    - Validar se `current_user["role"] == "STUDENT"`. Se falso, disparar `ForbiddenException` (HTTP 403 RFC 9457).

---

### FASE 4: Persistência em Memória Thread-Safe (`database.py`)
- [x] **4.1. Estrutura de Concorrência e Tabelas em Memória:**
  - Instanciar `_lock = threading.RLock()` para atomicidade de leituras e escritas.
  - Estruturas de armazenamento em dicionários:
    - `_users: Dict[str, dict]` (indexado por UUID em formato str)
    - `_students_profile: Dict[str, dict]` (indexado por UUID do aluno)
    - `_workout_plans: Dict[str, dict]` (indexado por UUID do plano)
    - `_routines: Dict[str, dict]` (indexado por UUID da rotina)
    - `_exercises: Dict[str, dict]` (indexado por UUID do exercício)
    - `_executions: Dict[str, dict]` (indexado por UUID da execução)
- [x] **4.2. Carga do Seed Inicial Determinístico:**
  - **Personal Trainer Seed:**
    - `id`: `"11111111-1111-1111-1111-111111111111"`
    - `name`: `"Carlos Personal"`
    - `email`: `"carlos@gymflow.dev"`
    - `password`: hash bcrypt de `"Personal123#"`
    - `role`: `"PERSONAL"`
    - `cref`: `"012345-G/SP"`
    - `phone`: `"+5511999990001"`
    - `createdAt`: `"2026-02-10T08:00:00Z"`
    - `updatedAt`: `"2026-02-10T08:00:00Z"`
  - **Aluno Seed:**
    - `id`: `"22222222-2222-2222-2222-222222222222"`
    - `personalId`: `"11111111-1111-1111-1111-111111111111"`
    - `name`: `"Rodrigo Aluno"`
    - `email`: `"rodrigo@gymflow.dev"`
    - `password`: hash bcrypt de `"Aluno123#"`
    - `role`: `"STUDENT"`
    - `phone`: `"+5511999990002"`
    - Perfil: `goal: "HYPERTROPHY"`, `weightKg: 78.5`, `heightCm: 178.0`, `notes: "Foco em ganho de massa"`
    - `createdAt`: `"2026-02-10T09:00:00Z"`
    - `updatedAt`: `"2026-02-10T09:00:00Z"`
  - **Plano de Treino Seed:**
    - `id`: `"55555555-5555-5555-5555-555555555555"`
    - `personalId`: `"11111111-1111-1111-1111-111111111111"`
    - `studentId`: `"22222222-2222-2222-2222-222222222222"`
    - `title`: `"Ciclo Hipertrofia 1 - Upper/Lower"`
    - `description`: `"Periodização inicial com foco em membros superiores e inferiores."`
    - `status`: `"ACTIVE"`
    - `startDate`: `"2026-02-10"`
    - `endDate`: `None`
    - `createdAt`: `"2026-02-10T10:00:00Z"`
    - `updatedAt`: `"2026-02-10T10:00:00Z"`
  - **Rotina Seed:**
    - `id`: `"33333333-3333-3333-3333-333333333333"`
    - `workoutPlanId`: `"55555555-5555-5555-5555-555555555555"`
    - `name`: `"Treino A — Peito, Tríceps e Deltoides"`
    - `dayOfWeek`: `"Segunda-feira"`
    - `order`: 1
    - `createdAt`: `"2026-02-10T10:05:00Z"`
  - **Exercício Seed:**
    - `id`: `"44444444-4444-4444-4444-444444444444"`
    - `routineId`: `"33333333-3333-3333-3333-333333333333"`
    - `name`: `"Supino Reto com Barra"`
    - `muscleGroup`: `"CHEST"`
    - `sets`: 4
    - `reps`: `"8-12"`
    - `restSeconds`: 90
    - `weightKg`: 60.0
    - `notes`: `"Manter escápulas aduzidas"`
    - `order`: 1
    - `createdAt`: `"2026-02-10T10:10:00Z"`
- [x] **4.3. Implementação dos Métodos CRUD em Memória:**
  - **Métodos de Usuário:**
    - `get_user_by_email(email: str) -> Optional[dict]`
    - `get_user_by_id(user_id: str) -> Optional[dict]`
    - `create_user(dto: RegisterUserDTO, hashed_pwd: str) -> dict`
  - **Métodos de Aluno:**
    - `list_students_by_personal(personal_id: str, page: int, limit: int, search: Optional[str], goal: Optional[str]) -> Tuple[List[dict], int]`
    - `get_student_by_id(student_id: str) -> Optional[dict]`
    - `create_student_by_personal(personal_id: str, dto: CreateStudentDTO, hashed_pwd: str) -> dict`
    - `update_student(student_id: str, dto: UpdateStudentDTO) -> Optional[dict]`
    - `delete_student(student_id: str) -> bool`
  - **Métodos de Planos de Treino, Rotinas e Exercícios:**
    - `list_workouts(user_id: str, role: str, page: int, limit: int, search: Optional[str], student_id: Optional[str], status: Optional[str]) -> Tuple[List[dict], int]`
    - `get_workout_full(workout_id: str) -> Optional[dict]` (agrega rotinas e exercícios ordenados por `order`)
    - `create_workout_plan(personal_id: str, dto: CreateWorkoutPlanDTO) -> dict` (cria plano, rotinas e exercícios em cascata)
    - `update_workout_plan(workout_id: str, dto: UpdateWorkoutPlanDTO) -> Optional[dict]`
    - `delete_workout_plan(workout_id: str) -> bool`
    - `add_routine(workout_id: str, dto: WorkoutRoutineDTO) -> dict`
    - `add_exercise(routine_id: str, dto: WorkoutExerciseDTO) -> dict`
    - `delete_exercise(exercise_id: str) -> bool`
  - **Métodos de Execução de Treino:**
    - `record_execution(student_id: str, routine_id: str, dto: CreateExecutionDTO) -> dict`
    - `list_executions_by_student(student_id: str) -> List[dict]`
  - **Método de Reset do Banco:**
    - `reset_database()`: limpa todas as tabelas em memória e restaura os seeds determinísticos.

---

### FASE 5: Tratamento de Erros RFC 9457 e Middlewares Core (`exceptions.py` & `main.py`)
- [x] **5.1. Definição das Exceções de Domínio Customizadas (`exceptions.py`):**
  - `EntityNotFoundException(entity_name: str, entity_id: str)`
  - `InvalidUUIDException(param_name: str, value: str)`
  - `BadRequestException(detail: str, invalid_params: Optional[List[dict]] = None)`
  - `UnauthorizedException(detail: str = "Credenciais inválidas ou token ausente/expirado.")`
  - `ForbiddenException(detail: str = "Acesso negado para o perfil do usuário.")`
  - `ConflictException(detail: str, invalid_params: Optional[List[dict]] = None)`
- [x] **5.2. Fábrica Canônica de Resposta `ApiError` (`exceptions.py`):**
  - Implementar helper `build_api_error_response(status_code: int, type_uri: str, title: str, detail: str, instance: str, invalid_params: Optional[List[dict]] = None) -> JSONResponse`.
- [x] **5.3. Exception Handlers Globais (`exceptions.py`):**
  - Handler para `RequestValidationError` (HTTP 422):
    - Itera sobre `exc.errors()`, formata cada erro em `{"name": loc_str, "reason": err_msg}` e insere na lista `invalidParams`.
    - Retorna `type: "https://api.gymflow.dev/errors/validation-error"`, `title: "Erro de Validação Semântica"`, status 422.
  - Handler para `EntityNotFoundException` (HTTP 404):
    - Retorna `type: "https://api.gymflow.dev/errors/not-found"`, `title: "Recurso Inexistente"`, status 404.
  - Handler para `UnauthorizedException` (HTTP 401):
    - Retorna `type: "https://api.gymflow.dev/errors/unauthorized"`, `title: "Não Autorizado"`, status 401.
  - Handler para `ForbiddenException` (HTTP 403):
    - Retorna `type: "https://api.gymflow.dev/errors/forbidden"`, `title: "Acesso Proibido"`, status 403.
  - Handler para `BadRequestException` / `InvalidUUIDException` (HTTP 400):
    - Retorna `type: "https://api.gymflow.dev/errors/bad-request"`, `title: "Requisição Inválida"`, status 400.
  - Handler para `StarletteHTTPException`:
    - Intercepta erros internos do framework (ex: 404 de rota não encontrada, 405 Method Not Allowed) e encapsula no formato `ApiError`, evitando o leak de `{"detail": "..."}`.
- [x] **5.4. Middleware de Interceptação de JSON Malformado (`main.py`):**
  - Interceptar requisições `POST`, `PUT`, `PATCH` que contenham header `Content-Type: application/json`.
  - Ler `await request.body()` e tentar executar `json.loads(body)`.
  - Caso ocorra `json.JSONDecodeError`, abortar imediatamente o processamento e responder `400 Bad Request` com:
    - `type: "https://api.gymflow.dev/errors/bad-request"`
    - `title: "Requisição Malformada"`
    - `detail: "O corpo da requisição não é um JSON sintaticamente válido."`
    - `instance: request.url.path`
- [x] **5.5. Configuração da Aplicação FastAPI (`main.py`):**
  - Instanciar `app = FastAPI(title="GymFlow API", version="1.0.0", description="API para Personal Trainers e Alunos")`.
  - Configurar `CORSMiddleware` permitindo origens de desenvolvimento, headers e métodos autorizados.
  - Registrar todos os Exception Handlers customizados.
  - Incluir os roteadores modulares com seus respectivos prefixos e tags.

---

### FASE 6: Implementação dos Roteadores da API (`routers/`)
- [x] **6.1. Roteador de Autenticação (`routers/auth.py`):**
  - `POST /api/v1/auth/register`:
    - Validar unicidade do email (`get_user_by_email`). Se já cadastrado, disparar `BadRequestException` (HTTP 400).
    - Criptografar senha com `hash_password`.
    - Persistir usuário via `create_user`.
    - Retornar status `201 Created` com schema `UserResponse` (sem expor o hash da senha).
  - `POST /api/v1/auth/login`:
    - Buscar usuário por email.
    - Se inexistente ou senha incorreta (`verify_password`), lançar `UnauthorizedException` (HTTP 401).
    - Gerar token JWT com `sub = str(user["id"])` e `role = user["role"]`.
    - Retornar status `200 OK` com `AuthTokenResponse`.
  - `GET /api/v1/auth/me`:
    - Injetar dependência `get_current_user`.
    - Retornar status `200 OK` com os dados do usuário autenticado (`UserResponse`).
- [x] **6.2. Roteador de Alunos (`routers/students.py`):**
  - `GET /api/v1/students`:
    - Exclusivo para `require_personal`.
    - Query params: `page` (ge=1, def=1), `limit` (ge=1, le=100, def=10), `search` (opcional), `goal` (opcional `FitnessGoal`).
    - Chamar `database.list_students_by_personal`.
    - Retornar status `200 OK` com `PaginatedStudentsResponse`.
  - `POST /api/v1/students`:
    - Exclusivo para `require_personal`.
    - Receber payload validado `CreateStudentDTO`.
    - Verificar unicidade do email (HTTP 400 se já cadastrado).
    - Criar conta de aluno vinculada automaticamente ao personal logado (`personalId = current_user["id"]`).
    - Retornar status `201 Created` com `StudentResponse` e cabeçalho HTTP `Location: /api/v1/students/{id}`.
  - `GET /api/v1/students/{studentId}`:
    - Injetar `get_current_user`.
    - Validar formato UUID de `{studentId}`.
    - Checar UUID de simulação `00000000-0000-0000-0000-000000000000` (lançar `EntityNotFoundException` HTTP 404).
    - Buscar aluno no banco; se inexistente, lançar `EntityNotFoundException`.
    - Regra de Acesso: Apenas o personal responsável pelo aluno OU o próprio aluno logado podem acessar (caso contrário, lançar `ForbiddenException` HTTP 403).
    - Retornar status `200 OK` com `StudentResponse`.
  - `PATCH /api/v1/students/{studentId}`:
    - Exclusivo para `require_personal`.
    - Validar UUID de `{studentId}` e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Buscar aluno e validar se pertence ao personal logado (HTTP 404 se não for aluno dele).
    - Aplicar atualização parcial com campos recebidos em `UpdateStudentDTO`.
    - Retornar status `200 OK` com `StudentResponse` atualizado.
  - `DELETE /api/v1/students/{studentId}`:
    - Exclusivo para `require_personal`.
    - Validar UUID e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Validar vínculo com personal logado; remover aluno via `database.delete_student`.
    - Retornar status `204 No Content` com corpo vazio (`Response(status_code=204)`).
- [x] **6.3. Roteador de Planos de Treino, Rotinas e Exercícios (`routers/workouts.py`):**
  - `GET /api/v1/workouts`:
    - Injetar `get_current_user`.
    - Query params: `page`, `limit`, `search`, `studentId`, `status`.
    - Se perfil `PERSONAL`: lista treinos criados por ele.
    - Se perfil `STUDENT`: lista treinos atribuídos a ele.
    - Retornar status `200 OK` com `PaginatedWorkoutsResponse`.
  - `POST /api/v1/workouts`:
    - Exclusivo para `require_personal`.
    - Receber payload validado `CreateWorkoutPlanDTO`.
    - Validar se o aluno associado (`studentId`) existe e pertence ao personal logado (lançar HTTP 404 se não encontrado).
    - Persistir plano de treino e eventuais rotinas/exercícios aninhados.
    - Retornar status `201 Created` com `WorkoutPlanResponse` e cabeçalho `Location: /api/v1/workouts/{id}`.
  - `GET /api/v1/workouts/{workoutId}`:
    - Injetar `get_current_user`.
    - Validar UUID e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Buscar plano completo no banco. Se inexistente, lançar `EntityNotFoundException`.
    - Validar permissão: personal criador ou aluno destinatário.
    - Retornar status `200 OK` com `WorkoutPlanResponse` (rotinas e exercícios ordenados).
  - `PATCH /api/v1/workouts/{workoutId}`:
    - Exclusivo para `require_personal`.
    - Validar UUID e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Validar se o personal é o criador do treino.
    - Atualizar campos (`title`, `description`, `startDate`, `endDate`, `status`).
    - Retornar status `200 OK` com `WorkoutPlanResponse` atualizado.
  - `DELETE /api/v1/workouts/{workoutId}`:
    - Exclusivo para `require_personal`.
    - Validar UUID e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Remover plano do banco. Retornar status `204 No Content` sem corpo.
  - `POST /api/v1/workouts/{workoutId}/routines`:
    - Exclusivo para `require_personal`.
    - Validar UUID do plano e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Adicionar divisão de treino via `database.add_routine`.
    - Retornar status `201 Created` com `WorkoutRoutineResponse`.
  - `POST /api/v1/routines/{routineId}/exercises`:
    - Exclusivo para `require_personal`.
    - Validar UUID da rotina e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Adicionar exercício à rotina via `database.add_exercise`.
    - Retornar status `201 Created` com `WorkoutExerciseResponse`.
  - `DELETE /api/v1/exercises/{exerciseId}`:
    - Exclusivo para `require_personal`.
    - Validar UUID do exercício e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Remover exercício do banco.
    - Retornar status `204 No Content` sem corpo.
- [x] **6.4. Roteador de Execuções e Feedback (`routers/executions.py`):**
  - `POST /api/v1/routines/{routineId}/executions`:
    - Exclusivo para `require_student`.
    - Validar UUID de `{routineId}` e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Validar se a rotina existe e pertence a um treino atribuído a este aluno.
    - Receber payload validado `CreateExecutionDTO` (`durationMinutes`, `rpeScore`, `feedback`).
    - Registrar execução via `database.record_execution`.
    - Retornar status `201 Created` com `ExecutionResponse`.
  - `GET /api/v1/students/{studentId}/executions`:
    - Injetar `get_current_user`.
    - Validar UUID de `{studentId}` e checar UUID de simulação `00000000-0000-...` (HTTP 404).
    - Validar permissão: personal responsável pelo aluno OU o próprio aluno logado.
    - Consultar histórico via `database.list_executions_by_student`.
    - Retornar status `200 OK` com `List[ExecutionResponse]`.

---

### FASE 7: Suíte Completa de Testes Automatizados com Pytest (`tests/`)
- [x] **7.1. Fixtures e Reset de Estado (`tests/conftest.py`):**
  - Instanciar `client = TestClient(app)`.
  - Criar fixture com `autouse=True` que executa `database.reset_database()` antes de cada teste.
  - Fixture `personal_token`: gera token JWT válido para o personal seed (`11111111-1111-1111-1111-111111111111`).
  - Fixture `student_token`: gera token JWT válido para o aluno seed (`22222222-2222-2222-2222-222222222222`).
  - Fixture `personal_headers`: dicionário com `Authorization: Bearer <personal_token>`.
  - Fixture `student_headers`: dicionário com `Authorization: Bearer <student_token>`.
- [x] **7.2. Testes de Autenticação e Perfil (`tests/test_auth.py`):**
  - `test_register_personal_success`: Cadastro de personal com CREF preenchido -> Retorna 201 Created.
  - `test_register_personal_missing_cref`: Cadastro de personal sem CREF -> Retorna 422 Unprocessable Entity com `invalidParams`.
  - `test_register_student_success`: Cadastro de aluno público -> Retorna 201 Created.
  - `test_register_duplicate_email`: Tentativa de cadastrar e-mail já existente -> Retorna 400 Bad Request RFC 9457.
  - `test_login_success`: Login com credenciais válidas -> Retorna 200 OK com token JWT e dados do usuário.
  - `test_login_invalid_password`: Login com senha incorreta -> Retorna 401 Unauthorized RFC 9457.
  - `test_me_authenticated`: Acesso ao endpoint `/api/v1/auth/me` com token válido -> Retorna 200 OK.
  - `test_me_unauthenticated`: Acesso a `/api/v1/auth/me` sem token -> Retorna 401 Unauthorized RFC 9457.
- [x] **7.3. Testes da Carteira de Alunos (`tests/test_students.py`):**
  - `test_list_students_by_personal`: Personal lista seus alunos -> Retorna 200 OK com envelope de paginação.
  - `test_student_cannot_list_students`: Aluno tenta listar alunos -> Retorna 403 Forbidden RFC 9457.
  - `test_create_student_by_personal`: Personal cadastra novo aluno -> Retorna 201 Created com cabeçalho `Location`.
  - `test_get_student_detail_by_personal`: Personal consulta detalhes de seu aluno -> Retorna 200 OK.
  - `test_get_student_detail_by_student_himself`: Aluno consulta seu próprio cadastro -> Retorna 200 OK.
  - `test_get_student_detail_forbidden_for_other_student`: Aluno tenta acessar cadastro de outro aluno -> Retorna 403 Forbidden RFC 9457.
  - `test_patch_student_profile`: Personal atualiza dados de peso e meta do aluno -> Retorna 200 OK.
  - `test_delete_student_by_personal`: Personal desvincula aluno -> Retorna 204 No Content sem corpo.
- [x] **7.4. Testes de Treinos, Rotinas e Exercícios (`tests/test_workouts.py`):**
  - `test_personal_creates_complete_workout_plan`: Personal cria plano de treino com rotinas e exercícios em cascata -> Retorna 201 Created com header `Location`.
  - `test_student_cannot_create_workout_plan`: Aluno tenta criar plano de treino -> Retorna 403 Forbidden RFC 9457.
  - `test_student_views_assigned_workout`: Aluno consulta ficha de treino atribuída a ele -> Retorna 200 OK com rotinas e exercícios ordenados.
  - `test_patch_workout_plan`: Personal atualiza título e status do treino -> Retorna 200 OK.
  - `test_delete_workout_plan`: Personal remove plano de treino -> Retorna 204 No Content sem corpo.
  - `test_add_routine_to_workout`: Personal adiciona rotina (Treino B) a um plano -> Retorna 201 Created.
  - `test_add_exercise_to_routine`: Personal adiciona exercício à rotina -> Retorna 201 Created.
  - `test_delete_exercise_returns_204`: Personal remove exercício -> Retorna 204 No Content sem corpo.
- [x] **7.5. Testes de Execução e Feedback (`tests/test_executions.py`):**
  - `test_student_records_execution_success`: Aluno registra check-in com duração, RPE e feedback -> Retorna 201 Created.
  - `test_personal_cannot_record_execution`: Personal tenta registrar execução de treino -> Retorna 403 Forbidden RFC 9457.
  - `test_list_student_executions_by_personal`: Personal audita o histórico de execuções do aluno -> Retorna 200 OK.
  - `test_list_student_executions_by_student_himself`: Aluno visualiza seu histórico -> Retorna 200 OK.
- [x] **7.6. Testes de Resiliência e Conformidade RFC 9457 (`tests/test_errors.py`):**
  - `test_malformed_json_returns_400_rfc9457`: Enviar JSON sintaticamente corrompido em requisição POST com `application/json` -> Retorna 400 Bad Request no formato `ApiError`.
  - `test_simulation_uuid_returns_404_rfc9457`: Acessar qualquer endpoint com UUID `00000000-0000-0000-0000-000000000000` -> Retorna 404 Not Found RFC 9457.
  - `test_validation_error_returns_422_with_invalid_params`: Enviar payload com campo inválido (ex: `name` curto ou `rpeScore > 10`) -> Retorna 422 Unprocessable Entity com `invalidParams` preenchido.
  - `test_no_fastapi_default_detail_leak`: Garantir que nenhuma resposta de erro da aplicação contenha a chave isolada `{"detail": "..."}`.

---

## 4. Matriz de Rastreabilidade e Critérios de Homologação (Definition of Done)

| Item da Especificação | Requisito Técnico | Componente / Arquivo | Critério de Aceite | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Pydantic v2 Schemas** | Schema-first estrito alinhado à especificação | `src/api/schemas.py` | Modelos tipados com enums, validações e conversão camelCase | **Aprovado** |
| **Segurança & RBAC** | Autenticação JWT e segregação de perfis | `security.py` / `dependencies.py` | Emissão/validação JWT; 401 e 403 padronizados | **Aprovado** |
| **Persistência Isolada** | Thread-safe in-memory storage | `src/api/database.py` | Mutações com `threading.RLock`, seeds e `reset_database()` | **Aprovado** |
| **RFC 9457 Error Handling** | Erros no formato `ApiError` | `src/api/exceptions.py` | 100% dos erros HTTP compatíveis com Problem Details | **Aprovado** |
| **JSON Malformado** | Interceptação de sintaxe inválida | `src/api/main.py` | Middleware responde 400 RFC 9457 antes dos endpoints | **Aprovado** |
| **Headers HTTP & Verbos** | Location no POST, 204 sem body no DELETE | `routers/` | `Location: /api/v1/.../{id}` no 201; 204 sem corpo no DELETE | **Aprovado** |
| **UUID de Simulação 404** | `00000000-0000-0000-0000-000000000000` | `database.py` / `routers/` | Retorna determinístico 404 Recurso Inexistente | **Aprovado** |
| **Suíte de Testes** | 100% dos fluxos e regras testados | `src/api/tests/` | 32 testes passando sem falhas (`pytest -v`) | **Aprovado** |
