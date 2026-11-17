"""Tests for RFC 9457 Problem Details compliance, error interceptors, and resilience."""


def test_malformed_json_returns_400_rfc9457(client, personal_headers):
    # Send broken JSON syntax with Content-Type application/json
    broken_payload = '{"name": "Incompleto", "invalid_json": '
    response = client.post(
        "/api/v1/students",
        content=broken_payload,
        headers={"Authorization": personal_headers["Authorization"], "Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/bad-request"
    assert data["title"] == "Requisição Malformada"
    assert data["status"] == 400
    assert "detail" in data
    assert data["instance"] == "/api/v1/students"


def test_simulation_uuid_returns_404_rfc9457(client, personal_headers):
    sim_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/students/{sim_uuid}", headers=personal_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/not-found"
    assert data["title"] == "Recurso Inexistente"
    assert data["status"] == 404
    assert data["instance"] == f"/api/v1/students/{sim_uuid}"


def test_validation_error_returns_422_with_invalid_params(client, student_headers):
    routine_id = "33333333-3333-3333-3333-333333333333"
    # rpeScore is constrained to ge=1, le=10
    payload = {
        "durationMinutes": 45,
        "rpeScore": 15,  # Exceeds maximum 10
    }
    response = client.post(
        f"/api/v1/routines/{routine_id}/executions",
        json=payload,
        headers=student_headers,
    )
    assert response.status_code == 422
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/validation-error"
    assert data["title"] == "Erro de Validação Semântica"
    assert data["status"] == 422
    assert "invalidParams" in data
    assert any("rpescore" in p["name"].lower() or "rpescore" in p["reason"].lower() for p in data["invalidParams"])


def test_no_fastapi_default_detail_leak(client):
    # Calling non-existent route
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    # RFC 9457 requires type, title, status, detail, instance
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "instance" in data
    # Ensure it's not just FastAPI's default {"detail": "Not Found"}
    assert data["type"] == "https://api.gymflow.dev/errors/not-found"
