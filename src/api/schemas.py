"""Pydantic v2 schemas for GymFlow API adhering to OpenAPI contract and RFC 9457."""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from pydantic.alias_generators import to_camel


# ---------------------------------------------------------------------------
# Base Model with camelCase alias generator
# ---------------------------------------------------------------------------
class CamelModel(BaseModel):
    """Base model that automatically aliases snake_case fields to camelCase."""

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
        from_attributes=True,
    )


# ---------------------------------------------------------------------------
# Domain Enums
# ---------------------------------------------------------------------------
class UserRole(str, Enum):
    PERSONAL = "PERSONAL"
    STUDENT = "STUDENT"


class FitnessGoal(str, Enum):
    HYPERTROPHY = "HYPERTROPHY"
    WEIGHT_LOSS = "WEIGHT_LOSS"
    CONDITIONING = "CONDITIONING"
    REHABILITATION = "REHABILITATION"
    GENERAL_FITNESS = "GENERAL_FITNESS"


class MuscleGroup(str, Enum):
    CHEST = "CHEST"
    BACK = "BACK"
    LEGS = "LEGS"
    SHOULDERS = "SHOULDERS"
    BICEPS = "BICEPS"
    TRICEPS = "TRICEPS"
    CORE = "CORE"
    CARDIO = "CARDIO"
    FULL_BODY = "FULL_BODY"


class WorkoutStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# RFC 9457 Problem Details Models
# ---------------------------------------------------------------------------
class InvalidParam(CamelModel):
    name: str
    reason: str


class ApiError(CamelModel):
    type: str
    title: str
    status: int
    detail: str
    instance: str
    invalid_params: Optional[List[InvalidParam]] = None


# ---------------------------------------------------------------------------
# Pagination Meta Model
# ---------------------------------------------------------------------------
class PaginationMeta(CamelModel):
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    has_next: bool


# ---------------------------------------------------------------------------
# User & Authentication Schemas
# ---------------------------------------------------------------------------
class RegisterUserDTO(CamelModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole
    phone: Optional[str] = None
    cref: Optional[str] = None

    @model_validator(mode="after")
    def validate_cref_for_personal(self) -> "RegisterUserDTO":
        if self.role == UserRole.PERSONAL:
            if not self.cref or not self.cref.strip():
                raise ValueError("O campo 'cref' é obrigatório para o perfil PERSONAL.")
        return self


class LoginRequestDTO(CamelModel):
    email: EmailStr
    password: str


class UserResponse(CamelModel):
    id: UUID
    name: str
    email: str
    role: UserRole
    phone: Optional[str] = None
    cref: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AuthTokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Student & Physical Profile Schemas
# ---------------------------------------------------------------------------
class StudentProfileDTO(CamelModel):
    birth_date: Optional[date] = None
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    goal: FitnessGoal
    notes: Optional[str] = Field(None, max_length=500)


class CreateStudentDTO(CamelModel):
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    profile: Optional[StudentProfileDTO] = None


class UpdateStudentDTO(CamelModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    phone: Optional[str] = None
    profile: Optional[StudentProfileDTO] = None


class StudentResponse(CamelModel):
    id: UUID
    personal_id: UUID
    name: str
    email: str
    role: UserRole = UserRole.STUDENT
    phone: Optional[str] = None
    profile: Optional[StudentProfileDTO] = None
    created_at: datetime
    updated_at: datetime


class PaginatedStudentsResponse(CamelModel):
    data: List[StudentResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Exercise, Routine & Workout Plan Schemas
# ---------------------------------------------------------------------------
class WorkoutExerciseDTO(CamelModel):
    name: str = Field(..., min_length=2, max_length=100)
    muscle_group: MuscleGroup
    sets: int = Field(..., ge=1, le=20)
    reps: str = Field(..., max_length=30)
    rest_seconds: int = Field(..., ge=0, le=600)
    weight_kg: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=300)
    order: int = Field(..., ge=1)


class WorkoutExerciseResponse(CamelModel):
    id: UUID
    routine_id: UUID
    name: str
    muscle_group: MuscleGroup
    sets: int
    reps: str
    rest_seconds: int
    weight_kg: Optional[float] = None
    notes: Optional[str] = None
    order: int
    created_at: datetime


class WorkoutRoutineDTO(CamelModel):
    name: str = Field(..., min_length=2, max_length=80)
    day_of_week: Optional[str] = None
    order: int = Field(..., ge=1)
    exercises: Optional[List[WorkoutExerciseDTO]] = Field(default_factory=list)


class WorkoutRoutineResponse(CamelModel):
    id: UUID
    workout_plan_id: UUID
    name: str
    day_of_week: Optional[str] = None
    order: int
    exercises: List[WorkoutExerciseResponse] = Field(default_factory=list)
    created_at: datetime


class CreateWorkoutPlanDTO(CamelModel):
    student_id: UUID
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_date: date
    end_date: Optional[date] = None
    status: WorkoutStatus = WorkoutStatus.ACTIVE
    routines: Optional[List[WorkoutRoutineDTO]] = Field(default_factory=list)


class UpdateWorkoutPlanDTO(CamelModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[WorkoutStatus] = None


class WorkoutPlanResponse(CamelModel):
    id: UUID
    personal_id: UUID
    student_id: UUID
    title: str
    description: Optional[str] = None
    status: WorkoutStatus
    start_date: date
    end_date: Optional[date] = None
    routines: List[WorkoutRoutineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PaginatedWorkoutsResponse(CamelModel):
    data: List[WorkoutPlanResponse]
    meta: PaginationMeta


# ---------------------------------------------------------------------------
# Workout Execution Schemas
# ---------------------------------------------------------------------------
class CreateExecutionDTO(CamelModel):
    duration_minutes: int = Field(..., ge=1, le=360)
    rpe_score: int = Field(..., ge=1, le=10)
    feedback: Optional[str] = Field(None, max_length=500)
    completed_at: Optional[datetime] = None


class ExecutionResponse(CamelModel):
    id: UUID
    student_id: UUID
    routine_id: UUID
    duration_minutes: int
    rpe_score: int
    feedback: Optional[str] = None
    completed_at: datetime
    created_at: datetime
