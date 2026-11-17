"""Workouts Router: plans, routines, exercises, and assignment."""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from api.database import (
    SIMULATION_404_UUID,
    add_exercise,
    add_routine,
    create_workout_plan,
    delete_exercise,
    delete_workout_plan,
    get_exercise_by_id,
    get_routine_by_id,
    get_student_by_id,
    get_workout_full,
    list_workouts,
    update_workout_plan,
)
from api.dependencies import get_current_user, require_personal
from api.exceptions import (
    EntityNotFoundException,
    ForbiddenException,
    InvalidUUIDException,
)
from api.schemas import (
    CreateWorkoutPlanDTO,
    PaginatedWorkoutsResponse,
    PaginationMeta,
    UpdateWorkoutPlanDTO,
    WorkoutExerciseDTO,
    WorkoutExerciseResponse,
    WorkoutPlanResponse,
    WorkoutRoutineDTO,
    WorkoutRoutineResponse,
    WorkoutStatus,
)

router = APIRouter(tags=["Workouts"])


def _parse_uuid(value: str, param_name: str, entity_name: str) -> str:
    try:
        val = str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise InvalidUUIDException(param_name=param_name, value=value)
    if val == SIMULATION_404_UUID:
        raise EntityNotFoundException(entity_name=entity_name, entity_id=value)
    return val


@router.get(
    "/api/v1/workouts",
    response_model=PaginatedWorkoutsResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar planos de treino com paginação e filtros",
)
async def get_workouts(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Quantidade por página"),
    search: Optional[str] = Query(None, description="Filtro textual"),
    student_id: Optional[str] = Query(None, alias="studentId", description="Filtro por aluno"),
    status_filter: Optional[WorkoutStatus] = Query(None, alias="status", description="Filtro por status"),
    current_user: dict = Depends(get_current_user),
) -> PaginatedWorkoutsResponse:
    workouts_data, total_items = list_workouts(
        user_id=str(current_user["id"]),
        role=str(current_user["role"]),
        page=page,
        limit=limit,
        search=search,
        student_id=student_id,
        status=status_filter.value if status_filter else None,
    )
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0
    has_next = page < total_pages

    meta = PaginationMeta(
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
    )
    return PaginatedWorkoutsResponse(
        data=[WorkoutPlanResponse.model_validate(w) for w in workouts_data],
        meta=meta,
    )


@router.post(
    "/api/v1/workouts",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo plano de treino completo com rotinas e exercícios",
)
async def create_workout(
    dto: CreateWorkoutPlanDTO,
    response: Response,
    current_user: dict = Depends(require_personal),
) -> WorkoutPlanResponse:
    # Ensure student exists and belongs to the logged-in personal
    student_id_str = str(dto.student_id)
    if student_id_str == SIMULATION_404_UUID:
        raise EntityNotFoundException("Aluno", student_id_str)

    student = get_student_by_id(student_id_str)
    if not student or str(student.get("personal_id")) != str(current_user["id"]):
        raise EntityNotFoundException("Aluno", student_id_str)

    created_plan = create_workout_plan(personal_id=str(current_user["id"]), dto=dto)
    response.headers["Location"] = f"/api/v1/workouts/{created_plan['id']}"
    return WorkoutPlanResponse.model_validate(created_plan)


@router.get(
    "/api/v1/workouts/{workoutId}",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter plano de treino completo por ID",
)
async def get_workout(
    workout_id: str = Path(..., alias="workoutId"),
    current_user: dict = Depends(get_current_user),
) -> WorkoutPlanResponse:
    valid_id = _parse_uuid(workout_id, "workoutId", "Plano de Treino")
    plan = get_workout_full(valid_id)
    if not plan:
        raise EntityNotFoundException("Plano de Treino", workout_id)

    # Permission check: must be owner personal or assigned student
    user_id = str(current_user["id"])
    is_owner_personal = (
        current_user.get("role") == "PERSONAL" and str(plan.get("personal_id")) == user_id
    )
    is_assigned_student = (
        current_user.get("role") == "STUDENT" and str(plan.get("student_id")) == user_id
    )

    if not (is_owner_personal or is_assigned_student):
        raise ForbiddenException("Acesso negado a este plano de treino.")

    return WorkoutPlanResponse.model_validate(plan)


@router.patch(
    "/api/v1/workouts/{workoutId}",
    response_model=WorkoutPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar plano de treino parcialmente",
)
async def patch_workout(
    dto: UpdateWorkoutPlanDTO,
    workout_id: str = Path(..., alias="workoutId"),
    current_user: dict = Depends(require_personal),
) -> WorkoutPlanResponse:
    valid_id = _parse_uuid(workout_id, "workoutId", "Plano de Treino")
    plan = get_workout_full(valid_id)
    if not plan or str(plan.get("personal_id")) != str(current_user["id"]):
        raise EntityNotFoundException("Plano de Treino", workout_id)

    updated = update_workout_plan(valid_id, dto)
    return WorkoutPlanResponse.model_validate(updated)


@router.delete(
    "/api/v1/workouts/{workoutId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover plano de treino",
)
async def remove_workout(
    workout_id: str = Path(..., alias="workoutId"),
    current_user: dict = Depends(require_personal),
) -> Response:
    valid_id = _parse_uuid(workout_id, "workoutId", "Plano de Treino")
    plan = get_workout_full(valid_id)
    if not plan or str(plan.get("personal_id")) != str(current_user["id"]):
        raise EntityNotFoundException("Plano de Treino", workout_id)

    delete_workout_plan(valid_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/api/v1/workouts/{workoutId}/routines",
    response_model=WorkoutRoutineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar rotina (divisão de treino) ao plano",
)
async def add_routine_to_workout(
    dto: WorkoutRoutineDTO,
    workout_id: str = Path(..., alias="workoutId"),
    current_user: dict = Depends(require_personal),
) -> WorkoutRoutineResponse:
    valid_id = _parse_uuid(workout_id, "workoutId", "Plano de Treino")
    plan = get_workout_full(valid_id)
    if not plan or str(plan.get("personal_id")) != str(current_user["id"]):
        raise EntityNotFoundException("Plano de Treino", workout_id)

    created_routine = add_routine(valid_id, dto)
    return WorkoutRoutineResponse.model_validate(created_routine)


@router.post(
    "/api/v1/routines/{routineId}/exercises",
    response_model=WorkoutExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar exercício a uma rotina existente",
)
async def add_exercise_to_routine(
    dto: WorkoutExerciseDTO,
    routine_id: str = Path(..., alias="routineId"),
    current_user: dict = Depends(require_personal),
) -> WorkoutExerciseResponse:
    valid_id = _parse_uuid(routine_id, "routineId", "Rotina")
    routine = get_routine_by_id(valid_id)
    if not routine:
        raise EntityNotFoundException("Rotina", routine_id)

    plan = get_workout_full(str(routine["workout_plan_id"]))
    if not plan or str(plan.get("personal_id")) != str(current_user["id"]):
        raise ForbiddenException("Acesso negado: a rotina pertence a outro Personal Trainer.")

    created_exercise = add_exercise(valid_id, dto)
    return WorkoutExerciseResponse.model_validate(created_exercise)


@router.delete(
    "/api/v1/exercises/{exerciseId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover exercício de uma rotina",
)
async def remove_exercise(
    exercise_id: str = Path(..., alias="exerciseId"),
    current_user: dict = Depends(require_personal),
) -> Response:
    valid_id = _parse_uuid(exercise_id, "exerciseId", "Exercício")
    exercise = get_exercise_by_id(valid_id)
    if not exercise:
        raise EntityNotFoundException("Exercício", exercise_id)

    routine = get_routine_by_id(str(exercise["routine_id"]))
    if routine:
        plan = get_workout_full(str(routine["workout_plan_id"]))
        if plan and str(plan.get("personal_id")) != str(current_user["id"]):
            raise ForbiddenException("Acesso negado a este exercício.")

    delete_exercise(valid_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
