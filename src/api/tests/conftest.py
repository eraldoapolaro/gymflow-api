"""Pytest fixtures for GymFlow API: TestClient, deterministic reset, and auth headers."""

import pytest
from fastapi.testclient import TestClient

from api.database import reset_database
from api.main import app
from api.security import create_access_token


@pytest.fixture(autouse=True)
def clean_database_state():
    """Reset the database to initial deterministic seed state before each test."""
    reset_database()
    yield
    reset_database()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def personal_token():
    """JWT token for seeded Personal Trainer Carlos."""
    return create_access_token({
        "sub": "11111111-1111-1111-1111-111111111111",
        "role": "PERSONAL",
    })


@pytest.fixture
def student_token():
    """JWT token for seeded Student Rodrigo."""
    return create_access_token({
        "sub": "22222222-2222-2222-2222-222222222222",
        "role": "STUDENT",
    })


@pytest.fixture
def personal_headers(personal_token):
    """Authorization header dictionary for Personal Trainer."""
    return {
        "Authorization": f"Bearer {personal_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def student_headers(student_token):
    """Authorization header dictionary for Student."""
    return {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json",
    }
