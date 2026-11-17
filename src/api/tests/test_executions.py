"""Tests for Student routine execution (check-in), RPE tracking, and feedback history."""


def test_student_records_execution_success(client, student_headers):
    routine_id = "33333333-3333-3333-3333-333333333333"
    payload = {
        "durationMinutes": 55,
        "rpeScore": 8,
        "feedback": "Treino intenso, consegui progredir carga no supino.",
    }
    response = client.post(
        f"/api/v1/routines/{routine_id}/executions",
        json=payload,
        headers=student_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["durationMinutes"] == 55
    assert data["rpeScore"] == 8
    assert data["feedback"] == "Treino intenso, consegui progredir carga no supino."
    assert data["studentId"] == "22222222-2222-2222-2222-222222222222"
    assert data["routineId"] == routine_id


def test_personal_cannot_record_execution(client, personal_headers):
    routine_id = "33333333-3333-3333-3333-333333333333"
    payload = {
        "durationMinutes": 45,
        "rpeScore": 7,
    }
    response = client.post(
        f"/api/v1/routines/{routine_id}/executions",
        json=payload,
        headers=personal_headers,
    )
    assert response.status_code == 403
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/forbidden"


def test_list_student_executions_by_personal(client, personal_headers, student_headers):
    # First record an execution as student
    routine_id = "33333333-3333-3333-3333-333333333333"
    payload = {
        "durationMinutes": 60,
        "rpeScore": 9,
        "feedback": "Fadiga alta no final",
    }
    client.post(
        f"/api/v1/routines/{routine_id}/executions",
        json=payload,
        headers=student_headers,
    )

    # Personal views history
    student_id = "22222222-2222-2222-2222-222222222222"
    response = client.get(f"/api/v1/students/{student_id}/executions", headers=personal_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["rpeScore"] == 9


def test_list_student_executions_by_student_himself(client, student_headers):
    student_id = "22222222-2222-2222-2222-222222222222"
    response = client.get(f"/api/v1/students/{student_id}/executions", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
