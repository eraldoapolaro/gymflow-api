"""SQLAlchemy 2.0 Declarative ORM Models for GymFlow API."""

from datetime import date, datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class User(Base):
    """User entity: Personal Trainers and Students."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # PERSONAL or STUDENT
    cref: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    personal_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    profile: Mapped[Optional["StudentProfile"]] = relationship("StudentProfile", back_populates="student", uselist=False, cascade="all, delete-orphan")
    workout_plans: Mapped[List["WorkoutPlan"]] = relationship("WorkoutPlan", foreign_keys="WorkoutPlan.student_id", back_populates="student", cascade="all, delete-orphan")
    executions: Mapped[List["Execution"]] = relationship("Execution", back_populates="student", cascade="all, delete-orphan")


class StudentProfile(Base):
    """Student physical profile, biometric data, and goals."""
    __tablename__ = "student_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    goal: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="profile")


class WorkoutPlan(Base):
    """Workout plan / periodization entity."""
    __tablename__ = "workout_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    personal_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id], back_populates="workout_plans")
    routines: Mapped[List["WorkoutRoutine"]] = relationship("WorkoutRoutine", back_populates="workout_plan", cascade="all, delete-orphan", order_by="WorkoutRoutine.order")


class WorkoutRoutine(Base):
    """Workout division/routine (e.g., Treino A, Treino B, Upper, Lower)."""
    __tablename__ = "workout_routines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workout_plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    day_of_week: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    workout_plan: Mapped["WorkoutPlan"] = relationship("WorkoutPlan", back_populates="routines")
    exercises: Mapped[List["WorkoutExercise"]] = relationship("WorkoutExercise", back_populates="routine", cascade="all, delete-orphan", order_by="WorkoutExercise.order")
    executions: Mapped[List["Execution"]] = relationship("Execution", back_populates="routine", cascade="all, delete-orphan")


class WorkoutExercise(Base):
    """Technical exercise prescription within a routine."""
    __tablename__ = "workout_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    routine_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_routines.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(30), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[str] = mapped_column(String(30), nullable=False)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    routine: Mapped["WorkoutRoutine"] = relationship("WorkoutRoutine", back_populates="exercises")


class Execution(Base):
    """Workout execution check-in performed by a student."""
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    routine_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_routines.id", ondelete="CASCADE"), index=True, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rpe_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 10
    feedback: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="executions")
    routine: Mapped["WorkoutRoutine"] = relationship("WorkoutRoutine", back_populates="executions")
