"""Students Router: student management, profiles, and access control."""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from api.database import (
    SIMULATION_404_UUID,
    create_student_by_personal,
    delete_student,
    get_student_by_id,
    get_user_by_email,
    list_students_by_personal,
    update_student,
)
from api.dependencies import get_current_user, require_personal
from api.exceptions import (
    BadRequestException,
    EntityNotFoundException,
    ForbiddenException,
    InvalidUUIDException,
)
from api.schemas import (
    CreateStudentDTO,
    FitnessGoal,
    PaginatedStudentsResponse,
    PaginationMeta,
    StudentResponse,
    UpdateStudentDTO,
)
from api.security import hash_password

router = APIRouter(prefix="/api/v1/students", tags=["Students"])


def _validate_student_uuid(student_id: str) -> str:
    try:
        val = str(UUID(student_id))
    except (ValueError, TypeError, AttributeError):
        raise InvalidUUIDException(param_name="studentId", value=student_id)
    if val == SIMULATION_404_UUID:
        raise EntityNotFoundException(entity_name="Aluno", entity_id=student_id)
    return val


@router.get(
    "",
    response_model=PaginatedStudentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar alunos vinculados ao Personal Trainer",
)
async def list_students(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Quantidade por página"),
    search: Optional[str] = Query(None, description="Filtro por nome ou e-mail"),
    goal: Optional[FitnessGoal] = Query(None, description="Filtro por objetivo físico"),
    current_user: dict = Depends(require_personal),
) -> PaginatedStudentsResponse:
    goal_val = goal.value if goal else None
    students_data, total_items = list_students_by_personal(
        personal_id=str(current_user["id"]),
        page=page,
        limit=limit,
        search=search,
        goal=goal_val,
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
    return PaginatedStudentsResponse(
        data=[StudentResponse.model_validate(s) for s in students_data],
        meta=meta,
    )


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo aluno vinculado ao Personal Trainer",
)
async def create_student(
    dto: CreateStudentDTO,
    response: Response,
    current_user: dict = Depends(require_personal),
) -> StudentResponse:
    existing = get_user_by_email(dto.email)
    if existing:
        raise BadRequestException(
            detail=f"O e-mail '{dto.email}' já está em uso por outro usuário.",
            invalid_params=[{"name": "email", "reason": "E-mail já cadastrado no sistema."}],
        )

    hashed_pwd = hash_password(dto.password)
    student = create_student_by_personal(
        personal_id=str(current_user["id"]),
        dto=dto,
        hashed_pwd=hashed_pwd,
    )
    response.headers["Location"] = f"/api/v1/students/{student['id']}"
    return StudentResponse.model_validate(student)


@router.get(
    "/{studentId}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes de um aluno",
)
async def get_student(
    student_id: str = Path(..., alias="studentId"),
    current_user: dict = Depends(get_current_user),
) -> StudentResponse:
    valid_id = _validate_student_uuid(student_id)
    student = get_student_by_id(valid_id)
    if not student:
        raise EntityNotFoundException(entity_name="Aluno", entity_id=student_id)

    # RBAC: Only responsible personal or the student themselves
    user_id = str(current_user["id"])
    is_personal_owner = (
        current_user.get("role") == "PERSONAL" and str(student.get("personal_id")) == user_id
    )
    is_student_self = current_user.get("role") == "STUDENT" and str(student["id"]) == user_id

    if not (is_personal_owner or is_student_self):
        raise ForbiddenException("Acesso negado aos dados deste aluno.")

    return StudentResponse.model_validate(student)


@router.patch(
    "/{studentId}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados cadastrais e perfil físico do aluno",
)
async def patch_student(
    dto: UpdateStudentDTO,
    student_id: str = Path(..., alias="studentId"),
    current_user: dict = Depends(require_personal),
) -> StudentResponse:
    valid_id = _validate_student_uuid(student_id)
    student = get_student_by_id(valid_id)
    if not student or str(student.get("personal_id")) != str(current_user["id"]):
        raise EntityNotFoundException(entity_name="Aluno", entity_id=student_id)

    updated = update_student(valid_id, dto)
    return StudentResponse.model_validate(updated)


@router.delete(
    "/{studentId}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover aluno da carteira do Personal",
)
async def remove_student(
    student_id: str = Path(..., alias="studentId"),
    current_user: dict = Depends(require_personal),
) -> Response:
    valid_id = _validate_student_uuid(student_id)
    student = get_student_by_id(valid_id)
    if not student or str(student.get("personal_id")) != str(current_user["id"]):
        raise EntityNotFoundException(entity_name="Aluno", entity_id=student_id)

    delete_student(valid_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
