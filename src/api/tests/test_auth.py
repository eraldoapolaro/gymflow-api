"""Tests for Authentication and User Registration."""


def test_register_personal_success(client):
    payload = {
        "name": "Mariana Personal",
        "email": "mariana@gymflow.dev",
        "password": "SenhaForte123#",
        "role": "PERSONAL",
        "cref": "998877-G/SP",
        "phone": "+5511988887777",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Mariana Personal"
    assert data["email"] == "mariana@gymflow.dev"
    assert data["role"] == "PERSONAL"
    assert data["cref"] == "998877-G/SP"
    assert "password" not in data
    assert "id" in data


def test_register_personal_missing_cref(client):
    payload = {
        "name": "Mariana Sem Cref",
        "email": "semcref@gymflow.dev",
        "password": "SenhaForte123#",
        "role": "PERSONAL",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/validation-error"
    assert "invalidParams" in data
    assert any("cref" in p["name"].lower() or "cref" in p["reason"].lower() for p in data["invalidParams"])


def test_register_student_success(client):
    payload = {
        "name": "Lucas Aluno",
        "email": "lucas@gymflow.dev",
        "password": "SenhaAluno123#",
        "role": "STUDENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Lucas Aluno"
    assert data["email"] == "lucas@gymflow.dev"
    assert data["role"] == "STUDENT"
    assert data["cref"] is None


def test_register_duplicate_email(client):
    payload = {
        "name": "Outro Carlos",
        "email": "carlos@gymflow.dev",
        "password": "QualquerSenha123#",
        "role": "PERSONAL",
        "cref": "111222-G/SP",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/bad-request"
    assert "invalidParams" in data


def test_login_success(client):
    payload = {
        "email": "carlos@gymflow.dev",
        "password": "Personal123#",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert data["tokenType"] == "bearer"
    assert data["user"]["email"] == "carlos@gymflow.dev"


def test_login_invalid_password(client):
    payload = {
        "email": "carlos@gymflow.dev",
        "password": "SenhaErrada123#",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/unauthorized"
    assert data["status"] == 401


def test_me_authenticated(client, personal_headers):
    response = client.get("/api/v1/auth/me", headers=personal_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "carlos@gymflow.dev"
    assert data["role"] == "PERSONAL"


def test_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/unauthorized"
    assert data["status"] == 401
