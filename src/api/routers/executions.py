"""Executions Router: student workout tracking, check-ins, RPE, and feedback."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from api.database import (
    SIMULATION_404_UUID,
    get_routine_by_id,
    get_student_by_id,
    get_workout_full,
    list_executions_by_student,
    record_execution,
)
from api.dependencies import get_current_user, require_student
from api.exceptions import (
    EntityNotFoundException,
    ForbiddenException,
    InvalidUUIDException,
)
from api.schemas import CreateExecutionDTO, ExecutionResponse

router = APIRouter(tags=["Executions"])


def _parse_uuid(value: str, param_name: str, entity_name: str) -> str:
    try:
        val = str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise InvalidUUIDException(param_name=param_name, value=value)
    if val == SIMULATION_404_UUID:
        raise EntityNotFoundException(entity_name=entity_name, entity_id=value)
    return val


@router.post(
    "/api/v1/routines/{routineId}/executions",
    response_model=ExecutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar execução de rotina de treino pelo aluno (check-in)",
)
async def create_routine_execution(
    dto: CreateExecutionDTO,
    routine_id: str = Path(..., alias="routineId"),
    current_user: dict = Depends(require_student),
) -> ExecutionResponse:
    valid_id = _parse_uuid(routine_id, "routineId", "Rotina")
    routine = get_routine_by_id(valid_id)
    if not routine:
        raise EntityNotFoundException("Rotina", routine_id)

    plan = get_workout_full(str(routine["workout_plan_id"]))
    if not plan or str(plan.get("student_id")) != str(current_user["id"]):
        raise ForbiddenException("Acesso negado: a rotina não pertence aos seus planos de treino.")

    created = record_execution(
        student_id=str(current_user["id"]),
        routine_id=valid_id,
        dto=dto,
    )
    return ExecutionResponse.model_validate(created)


@router.get(
    "/api/v1/students/{studentId}/executions",
    response_model=List[ExecutionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar histórico de execuções de um aluno",
)
async def get_student_executions(
    student_id: str = Path(..., alias="studentId"),
    current_user: dict = Depends(get_current_user),
) -> List[ExecutionResponse]:
    valid_id = _parse_uuid(student_id, "studentId", "Aluno")
    student = get_student_by_id(valid_id)
    if not student:
        raise EntityNotFoundException("Aluno", student_id)

    # RBAC check: personal owner or student self
    user_id = str(current_user["id"])
    is_personal_owner = (
        current_user.get("role") == "PERSONAL" and str(student.get("personal_id")) == user_id
    )
    is_student_self = current_user.get("role") == "STUDENT" and str(student["id"]) == user_id

    if not (is_personal_owner or is_student_self):
        raise ForbiddenException("Acesso negado ao histórico deste aluno.")

    history = list_executions_by_student(valid_id)
    return [ExecutionResponse.model_validate(e) for e in history]
