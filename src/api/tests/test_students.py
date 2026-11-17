"""Tests for Students portfolio management and RBAC segregation."""

from api.security import create_access_token


def test_list_students_by_personal(client, personal_headers):
    response = client.get("/api/v1/students?page=1&limit=10", headers=personal_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["page"] == 1
    assert data["meta"]["limit"] == 10
    assert data["meta"]["totalItems"] >= 1
    assert any(s["email"] == "rodrigo@gymflow.dev" for s in data["data"])


def test_student_cannot_list_students(client, student_headers):
    response = client.get("/api/v1/students", headers=student_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/forbidden"


def test_create_student_by_personal(client, personal_headers):
    payload = {
        "name": "Camila Nova Aluna",
        "email": "camila@gymflow.dev",
        "password": "SenhaCamila123#",
        "phone": "+5511977778888",
        "profile": {
            "weightKg": 62.0,
            "heightCm": 165.0,
            "goal": "WEIGHT_LOSS",
            "notes": "Iniciante em musculação",
        },
    }
    response = client.post("/api/v1/students", json=payload, headers=personal_headers)
    assert response.status_code == 201
    assert "Location" in response.headers
    data = response.json()
    assert data["name"] == "Camila Nova Aluna"
    assert data["email"] == "camila@gymflow.dev"
    assert data["profile"]["goal"] == "WEIGHT_LOSS"
    assert response.headers["Location"] == f"/api/v1/students/{data['id']}"


def test_get_student_detail_by_personal(client, personal_headers):
    student_id = "22222222-2222-2222-2222-222222222222"
    response = client.get(f"/api/v1/students/{student_id}", headers=personal_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_id
    assert data["name"] == "Rodrigo Aluno"
    assert data["profile"]["goal"] == "HYPERTROPHY"


def test_get_student_detail_by_student_himself(client, student_headers):
    student_id = "22222222-2222-2222-2222-222222222222"
    response = client.get(f"/api/v1/students/{student_id}", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == student_id
    assert data["email"] == "rodrigo@gymflow.dev"


def test_get_student_detail_forbidden_for_other_student(client):
    # Register another legitimate student in the system
    other_student_payload = {
        "name": "Outro Aluno",
        "email": "outro.aluno@gymflow.dev",
        "password": "SenhaOutro123#",
        "role": "STUDENT",
    }
    reg_resp = client.post("/api/v1/auth/register", json=other_student_payload)
    other_student_id = reg_resp.json()["id"]

    other_token = create_access_token({
        "sub": other_student_id,
        "role": "STUDENT",
    })
    headers = {"Authorization": f"Bearer {other_token}"}
    target_student_id = "22222222-2222-2222-2222-222222222222"
    response = client.get(f"/api/v1/students/{target_student_id}", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/forbidden"


def test_patch_student_profile(client, personal_headers):
    student_id = "22222222-2222-2222-2222-222222222222"
    payload = {
        "profile": {
            "weightKg": 80.0,
            "goal": "HYPERTROPHY",
            "notes": "Evolução de peso positiva",
        }
    }
    response = client.patch(f"/api/v1/students/{student_id}", json=payload, headers=personal_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["weightKg"] == 80.0
    assert data["profile"]["notes"] == "Evolução de peso positiva"


def test_delete_student_by_personal(client, personal_headers):
    student_id = "22222222-2222-2222-2222-222222222222"
    response = client.delete(f"/api/v1/students/{student_id}", headers=personal_headers)
    assert response.status_code == 204
    assert response.content == b""

    # Confirm it's gone
    check = client.get(f"/api/v1/students/{student_id}", headers=personal_headers)
    assert check.status_code == 404
