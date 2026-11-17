# STYLEGUIDE.md — Guia de Estilo e Convenções Técnicas

> **Projeto:** GymFlow API  
> **Padrões:** PEP 8, RFC 9457, Pydantic v2, SQLAlchemy 2.0  

---

## 1. Convenções de Código Python
- **Formatador e Linter:** Compatibilidade com Black / Flake8 e PEP 8.
- **Tipagem Estrita (Type Hints):** 100% das funções, métodos e parâmetros devem conter anotações de tipo explícitas (`Optional`, `List`, `Dict`, `Tuple`, etc.).
- **Async/Await:** Todos os handlers de rota no FastAPI devem ser assíncronos (`async def`).
- **Nomenclatura Interna:**
  - Módulos e funções: `snake_case` (`list_students_by_personal`, `get_workout_full`).
  - Classes e Modelos: `PascalCase` (`WorkoutPlanResponse`, `StudentProfile`).
  - Constantes globais: `UPPER_SNAKE_CASE` (`SIMULATION_404_UUID`, `SECRET_KEY`).

---

## 2. Convenções de Comunicação HTTP / REST
- **Nomenclatura no Wire:** Payloads JSON de entrada e saída devem utilizar **`camelCase`** rigorosamente (`personalId`, `studentId`, `workoutPlanId`, `restSeconds`, `rpeScore`, `durationMinutes`, `createdAt`).
- **Verbos HTTP Semânticos:**
  - `GET`: Idempotente e sem efeitos colaterais.
  - `POST`: Criação de recursos com retorno `201 Created` e cabeçalho `Location`.
  - `PATCH`: Atualização parcial do recurso com retorno `200 OK`.
  - `DELETE`: Remoção com retorno `204 No Content` sem corpo (`Response(status_code=204)`).
- **Tratamento de Erros:**
  - RFC 9457 com cabeçalho `Content-Type: application/problem+json`.
  - Campos obrigatórios: `type`, `title`, `status`, `detail`, `instance`.
  - Erros de validação (HTTP 422) ou parâmetros inválidos (HTTP 400) devem preencher `invalidParams: [{"name": ..., "reason": ...}]`.
