"""SQLAlchemy 2.0 ORM-backed persistence with deterministic seeding and full CRUD support."""

import copy
import math
import threading
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import create_engine, select, or_, and_, delete
from sqlalchemy.orm import sessionmaker, Session, selectinload
from sqlalchemy.pool import StaticPool

from api.models import Base, User, StudentProfile, WorkoutPlan, WorkoutRoutine, WorkoutExercise, Execution
from api.schemas import (
    CreateExecutionDTO,
    CreateStudentDTO,
    CreateWorkoutPlanDTO,
    RegisterUserDTO,
    UpdateStudentDTO,
    UpdateWorkoutPlanDTO,
    WorkoutExerciseDTO,
    WorkoutRoutineDTO,
)
from api.security import hash_password

SIMULATION_404_UUID = "00000000-0000-0000-0000-000000000000"

# Thread-safe in-memory SQLite database via StaticPool for blazing fast tests and isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_lock = threading.RLock()

# Precomputed seed hashes for instant resets
_PERSONAL_SEED_HASH = hash_password("Personal123#")
_STUDENT_SEED_HASH = hash_password("Aluno123#")


def get_db():
    """FastAPI dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database() -> None:
    """Clear all records and restore deterministic seeds via SQLAlchemy ORM."""
    with _lock:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        with SessionLocal() as session:
            # Seed Personal Trainer
            personal_id = "11111111-1111-1111-1111-111111111111"
            personal = User(
                id=personal_id,
                name="Carlos Personal",
                email="carlos@gymflow.dev",
                password=_PERSONAL_SEED_HASH,
                role="PERSONAL",
                cref="012345-G/SP",
                phone="+5511999990001",
                personal_id=None,
                created_at=datetime(2026, 2, 10, 8, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 2, 10, 8, 0, 0, tzinfo=timezone.utc),
            )
            session.add(personal)

            # Seed Student
            student_id = "22222222-2222-2222-2222-222222222222"
            student = User(
                id=student_id,
                name="Rodrigo Aluno",
                email="rodrigo@gymflow.dev",
                password=_STUDENT_SEED_HASH,
                role="STUDENT",
                cref=None,
                phone="+5511999990002",
                personal_id=personal_id,
                created_at=datetime(2026, 2, 10, 9, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 2, 10, 9, 0, 0, tzinfo=timezone.utc),
            )
            session.add(student)

            student_profile = StudentProfile(
                student_id=student_id,
                birth_date=None,
                weight_kg=78.5,
                height_cm=178.0,
                goal="HYPERTROPHY",
                notes="Foco em ganho de massa",
            )
            session.add(student_profile)

            # Seed Workout Plan
            workout_id = "55555555-5555-5555-5555-555555555555"
            plan = WorkoutPlan(
                id=workout_id,
                personal_id=personal_id,
                student_id=student_id,
                title="Ciclo Hipertrofia 1 - Upper/Lower",
                description="Periodização inicial com foco em membros superiores e inferiores.",
                status="ACTIVE",
                start_date=date(2026, 2, 10),
                end_date=None,
                created_at=datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc),
            )
            session.add(plan)

            # Seed Routine
            routine_id = "33333333-3333-3333-3333-333333333333"
            routine = WorkoutRoutine(
                id=routine_id,
                workout_plan_id=workout_id,
                name="Treino A — Peito, Tríceps e Deltoides",
                day_of_week="Segunda-feira",
                order=1,
                created_at=datetime(2026, 2, 10, 10, 5, 0, tzinfo=timezone.utc),
            )
            session.add(routine)

            # Seed Exercise
            exercise_id = "44444444-4444-4444-4444-444444444444"
            exercise = WorkoutExercise(
                id=exercise_id,
                routine_id=routine_id,
                name="Supino Reto com Barra",
                muscle_group="CHEST",
                sets=4,
                reps="8-12",
                rest_seconds=90,
                weight_kg=60.0,
                notes="Manter escápulas aduzidas",
                order=1,
                created_at=datetime(2026, 2, 10, 10, 10, 0, tzinfo=timezone.utc),
            )
            session.add(exercise)

            session.commit()


# Initialize DB on module import
reset_database()


# ---------------------------------------------------------------------------
# Helper Serializers
# ---------------------------------------------------------------------------
def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "password": user.password,
        "role": user.role,
        "cref": user.cref,
        "phone": user.phone,
        "personal_id": user.personal_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _profile_to_dict(p: Optional[StudentProfile]) -> Optional[dict]:
    if not p:
        return None
    return {
        "birth_date": p.birth_date,
        "weight_kg": p.weight_kg,
        "height_cm": p.height_cm,
        "goal": p.goal,
        "notes": p.notes,
    }


def _exercise_to_dict(e: WorkoutExercise) -> dict:
    return {
        "id": e.id,
        "routine_id": e.routine_id,
        "name": e.name,
        "muscle_group": e.muscle_group,
        "sets": e.sets,
        "reps": e.reps,
        "rest_seconds": e.rest_seconds,
        "weight_kg": e.weight_kg,
        "notes": e.notes,
        "order": e.order,
        "created_at": e.created_at,
    }


def _routine_to_dict(r: WorkoutRoutine) -> dict:
    exercises = [_exercise_to_dict(e) for e in sorted(r.exercises, key=lambda x: x.order)]
    return {
        "id": r.id,
        "workout_plan_id": r.workout_plan_id,
        "name": r.name,
        "day_of_week": r.day_of_week,
        "order": r.order,
        "exercises": exercises,
        "created_at": r.created_at,
    }


def _workout_to_dict(w: WorkoutPlan) -> dict:
    routines = [_routine_to_dict(r) for r in sorted(w.routines, key=lambda x: x.order)]
    return {
        "id": w.id,
        "personal_id": w.personal_id,
        "student_id": w.student_id,
        "title": w.title,
        "description": w.description,
        "status": w.status,
        "start_date": w.start_date,
        "end_date": w.end_date,
        "routines": routines,
        "created_at": w.created_at,
        "updated_at": w.updated_at,
    }


# ---------------------------------------------------------------------------
# User CRUD Methods
# ---------------------------------------------------------------------------
def get_user_by_email(email: str) -> Optional[dict]:
    with _lock:
        with SessionLocal() as session:
            stmt = select(User).where(User.email == email.strip().lower())
            user = session.scalars(stmt).first()
            return _user_to_dict(user) if user else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    with _lock:
        if user_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            user = session.get(User, str(user_id))
            return _user_to_dict(user) if user else None


def create_user(dto: RegisterUserDTO, hashed_pwd: str) -> dict:
    with _lock:
        with SessionLocal() as session:
            user = User(
                name=dto.name,
                email=dto.email.strip().lower(),
                password=hashed_pwd,
                role=dto.role.value if hasattr(dto.role, "value") else dto.role,
                cref=dto.cref,
                phone=dto.phone,
                personal_id=None,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return _user_to_dict(user)


# ---------------------------------------------------------------------------
# Student CRUD Methods
# ---------------------------------------------------------------------------
def list_students_by_personal(
    personal_id: str,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    goal: Optional[str] = None,
) -> Tuple[List[dict], int]:
    with _lock:
        with SessionLocal() as session:
            stmt = (
                select(User)
                .options(selectinload(User.profile))
                .where(and_(User.role == "STUDENT", User.personal_id == str(personal_id)))
            )
            users = session.scalars(stmt).all()

            results: List[dict] = []
            for u in users:
                user_dict = _user_to_dict(u)
                user_dict["profile"] = _profile_to_dict(u.profile)

                if search:
                    s = search.strip().lower()
                    if s not in user_dict["name"].lower() and s not in user_dict["email"].lower():
                        continue

                if goal:
                    user_goal = user_dict["profile"].get("goal") if user_dict["profile"] else None
                    if user_goal != goal:
                        continue

                results.append(user_dict)

            results.sort(key=lambda x: x["created_at"], reverse=True)
            total_items = len(results)

            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_data = results[start_idx:end_idx]

            return paginated_data, total_items


def get_student_by_id(student_id: str) -> Optional[dict]:
    with _lock:
        if student_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            stmt = select(User).options(selectinload(User.profile)).where(and_(User.id == str(student_id), User.role == "STUDENT"))
            u = session.scalars(stmt).first()
            if not u:
                return None
            res = _user_to_dict(u)
            res["profile"] = _profile_to_dict(u.profile)
            return res


def create_student_by_personal(personal_id: str, dto: CreateStudentDTO, hashed_pwd: str) -> dict:
    with _lock:
        with SessionLocal() as session:
            student = User(
                name=dto.name,
                email=dto.email.strip().lower(),
                password=hashed_pwd,
                role="STUDENT",
                cref=None,
                phone=dto.phone,
                personal_id=str(personal_id),
            )
            session.add(student)
            session.flush()

            if dto.profile:
                profile = StudentProfile(
                    student_id=student.id,
                    birth_date=dto.profile.birth_date,
                    weight_kg=dto.profile.weight_kg,
                    height_cm=dto.profile.height_cm,
                    goal=dto.profile.goal.value if hasattr(dto.profile.goal, "value") else dto.profile.goal,
                    notes=dto.profile.notes,
                )
                session.add(profile)

            session.commit()
            return get_student_by_id(student.id)  # type: ignore


def update_student(student_id: str, dto: UpdateStudentDTO) -> Optional[dict]:
    with _lock:
        if student_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            stmt = select(User).options(selectinload(User.profile)).where(and_(User.id == str(student_id), User.role == "STUDENT"))
            u = session.scalars(stmt).first()
            if not u:
                return None

            if dto.name is not None:
                u.name = dto.name
            if dto.phone is not None:
                u.phone = dto.phone

            u.updated_at = datetime.now(timezone.utc)

            if dto.profile is not None:
                if not u.profile:
                    u.profile = StudentProfile(student_id=u.id, goal="GENERAL_FITNESS")
                    session.add(u.profile)
                if dto.profile.birth_date is not None:
                    u.profile.birth_date = dto.profile.birth_date
                if dto.profile.weight_kg is not None:
                    u.profile.weight_kg = dto.profile.weight_kg
                if dto.profile.height_cm is not None:
                    u.profile.height_cm = dto.profile.height_cm
                if dto.profile.goal is not None:
                    u.profile.goal = dto.profile.goal.value if hasattr(dto.profile.goal, "value") else dto.profile.goal
                if dto.profile.notes is not None:
                    u.profile.notes = dto.profile.notes

            session.commit()
            return get_student_by_id(student_id)


def delete_student(student_id: str) -> bool:
    with _lock:
        if student_id == SIMULATION_404_UUID:
            return False
        with SessionLocal() as session:
            u = session.get(User, str(student_id))
            if not u or u.role != "STUDENT":
                return False
            session.delete(u)
            session.commit()
            return True


# ---------------------------------------------------------------------------
# Workout Plan, Routine & Exercise Methods
# ---------------------------------------------------------------------------
def get_workout_full(workout_id: str) -> Optional[dict]:
    with _lock:
        if workout_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            stmt = (
                select(WorkoutPlan)
                .options(
                    selectinload(WorkoutPlan.routines).selectinload(WorkoutRoutine.exercises)
                )
                .where(WorkoutPlan.id == str(workout_id))
            )
            w = session.scalars(stmt).first()
            return _workout_to_dict(w) if w else None


def list_workouts(
    user_id: str,
    role: str,
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[dict], int]:
    with _lock:
        with SessionLocal() as session:
            stmt = select(WorkoutPlan).options(
                selectinload(WorkoutPlan.routines).selectinload(WorkoutRoutine.exercises)
            )
            if role == "PERSONAL":
                stmt = stmt.where(WorkoutPlan.personal_id == str(user_id))
            elif role == "STUDENT":
                stmt = stmt.where(WorkoutPlan.student_id == str(user_id))

            if student_id:
                stmt = stmt.where(WorkoutPlan.student_id == str(student_id))

            if status:
                stmt = stmt.where(WorkoutPlan.status == status)

            plans = session.scalars(stmt).all()
            filtered: List[dict] = []
            for p in plans:
                if search:
                    s = search.strip().lower()
                    desc = p.description or ""
                    if s not in p.title.lower() and s not in desc.lower():
                        continue
                filtered.append(_workout_to_dict(p))

            filtered.sort(key=lambda x: x["created_at"], reverse=True)
            total_items = len(filtered)

            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_data = filtered[start_idx:end_idx]

            return paginated_data, total_items


def create_workout_plan(personal_id: str, dto: CreateWorkoutPlanDTO) -> dict:
    with _lock:
        with SessionLocal() as session:
            plan = WorkoutPlan(
                personal_id=str(personal_id),
                student_id=str(dto.student_id),
                title=dto.title,
                description=dto.description,
                status=dto.status.value if hasattr(dto.status, "value") else dto.status,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )
            session.add(plan)
            session.flush()

            if dto.routines:
                for r_dto in dto.routines:
                    routine = WorkoutRoutine(
                        workout_plan_id=plan.id,
                        name=r_dto.name,
                        day_of_week=r_dto.day_of_week,
                        order=r_dto.order,
                    )
                    session.add(routine)
                    session.flush()

                    if r_dto.exercises:
                        for e_dto in r_dto.exercises:
                            ex = WorkoutExercise(
                                routine_id=routine.id,
                                name=e_dto.name,
                                muscle_group=(
                                    e_dto.muscle_group.value
                                    if hasattr(e_dto.muscle_group, "value")
                                    else e_dto.muscle_group
                                ),
                                sets=e_dto.sets,
                                reps=e_dto.reps,
                                rest_seconds=e_dto.rest_seconds,
                                weight_kg=e_dto.weight_kg,
                                notes=e_dto.notes,
                                order=e_dto.order,
                            )
                            session.add(ex)

            session.commit()
            return get_workout_full(plan.id)  # type: ignore


def update_workout_plan(workout_id: str, dto: UpdateWorkoutPlanDTO) -> Optional[dict]:
    with _lock:
        if workout_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            plan = session.get(WorkoutPlan, str(workout_id))
            if not plan:
                return None

            if dto.title is not None:
                plan.title = dto.title
            if dto.description is not None:
                plan.description = dto.description
            if dto.start_date is not None:
                plan.start_date = dto.start_date
            if dto.end_date is not None:
                plan.end_date = dto.end_date
            if dto.status is not None:
                plan.status = dto.status.value if hasattr(dto.status, "value") else dto.status

            plan.updated_at = datetime.now(timezone.utc)
            session.commit()
            return get_workout_full(workout_id)


def delete_workout_plan(workout_id: str) -> bool:
    with _lock:
        if workout_id == SIMULATION_404_UUID:
            return False
        with SessionLocal() as session:
            plan = session.get(WorkoutPlan, str(workout_id))
            if not plan:
                return False
            session.delete(plan)
            session.commit()
            return True


def get_routine_by_id(routine_id: str) -> Optional[dict]:
    with _lock:
        if routine_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            stmt = select(WorkoutRoutine).options(selectinload(WorkoutRoutine.exercises)).where(WorkoutRoutine.id == str(routine_id))
            r = session.scalars(stmt).first()
            return _routine_to_dict(r) if r else None


def add_routine(workout_id: str, dto: WorkoutRoutineDTO) -> dict:
    with _lock:
        with SessionLocal() as session:
            routine = WorkoutRoutine(
                workout_plan_id=str(workout_id),
                name=dto.name,
                day_of_week=dto.day_of_week,
                order=dto.order,
            )
            session.add(routine)
            session.flush()

            if dto.exercises:
                for e_dto in dto.exercises:
                    ex = WorkoutExercise(
                        routine_id=routine.id,
                        name=e_dto.name,
                        muscle_group=(
                            e_dto.muscle_group.value
                            if hasattr(e_dto.muscle_group, "value")
                            else e_dto.muscle_group
                        ),
                        sets=e_dto.sets,
                        reps=e_dto.reps,
                        rest_seconds=e_dto.rest_seconds,
                        weight_kg=e_dto.weight_kg,
                        notes=e_dto.notes,
                        order=e_dto.order,
                    )
                    session.add(ex)

            session.commit()
            return get_routine_by_id(routine.id)  # type: ignore


def get_exercise_by_id(exercise_id: str) -> Optional[dict]:
    with _lock:
        if exercise_id == SIMULATION_404_UUID:
            return None
        with SessionLocal() as session:
            ex = session.get(WorkoutExercise, str(exercise_id))
            return _exercise_to_dict(ex) if ex else None


def add_exercise(routine_id: str, dto: WorkoutExerciseDTO) -> dict:
    with _lock:
        with SessionLocal() as session:
            ex = WorkoutExercise(
                routine_id=str(routine_id),
                name=dto.name,
                muscle_group=(
                    dto.muscle_group.value
                    if hasattr(dto.muscle_group, "value")
                    else dto.muscle_group
                ),
                sets=dto.sets,
                reps=dto.reps,
                rest_seconds=dto.rest_seconds,
                weight_kg=dto.weight_kg,
                notes=dto.notes,
                order=dto.order,
            )
            session.add(ex)
            session.commit()
            session.refresh(ex)
            return _exercise_to_dict(ex)


def delete_exercise(exercise_id: str) -> bool:
    with _lock:
        if exercise_id == SIMULATION_404_UUID:
            return False
        with SessionLocal() as session:
            ex = session.get(WorkoutExercise, str(exercise_id))
            if not ex:
                return False
            session.delete(ex)
            session.commit()
            return True


# ---------------------------------------------------------------------------
# Workout Execution Methods
# ---------------------------------------------------------------------------
def record_execution(student_id: str, routine_id: str, dto: CreateExecutionDTO) -> dict:
    with _lock:
        now = datetime.now(timezone.utc)
        completed = dto.completed_at if dto.completed_at else now
        with SessionLocal() as session:
            execution = Execution(
                student_id=str(student_id),
                routine_id=str(routine_id),
                duration_minutes=dto.duration_minutes,
                rpe_score=dto.rpe_score,
                feedback=dto.feedback,
                completed_at=completed,
            )
            session.add(execution)
            session.commit()
            session.refresh(execution)
            return {
                "id": execution.id,
                "student_id": execution.student_id,
                "routine_id": execution.routine_id,
                "duration_minutes": execution.duration_minutes,
                "rpe_score": execution.rpe_score,
                "feedback": execution.feedback,
                "completed_at": execution.completed_at,
                "created_at": execution.created_at,
            }


def list_executions_by_student(student_id: str) -> List[dict]:
    with _lock:
        if student_id == SIMULATION_404_UUID:
            return []
        with SessionLocal() as session:
            stmt = select(Execution).where(Execution.student_id == str(student_id)).order_by(Execution.completed_at.desc())
            execs = session.scalars(stmt).all()
            return [
                {
                    "id": e.id,
                    "student_id": e.student_id,
                    "routine_id": e.routine_id,
                    "duration_minutes": e.duration_minutes,
                    "rpe_score": e.rpe_score,
                    "feedback": e.feedback,
                    "completed_at": e.completed_at,
                    "created_at": e.created_at,
                }
                for e in execs
            ]
