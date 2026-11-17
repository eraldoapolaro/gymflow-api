"""Tests for Workout plans, routines, and exercise prescription."""


def test_personal_creates_complete_workout_plan(client, personal_headers):
    payload = {
        "studentId": "22222222-2222-2222-2222-222222222222",
        "title": "Treino ABC Força",
        "description": "Periodização focada em força pura",
        "startDate": "2026-03-01",
        "status": "ACTIVE",
        "routines": [
            {
                "name": "Treino A - Inferiores",
                "dayOfWeek": "Segunda-feira",
                "order": 1,
                "exercises": [
                    {
                        "name": "Agachamento Livre",
                        "muscleGroup": "LEGS",
                        "sets": 4,
                        "reps": "6-8",
                        "restSeconds": 120,
                        "weightKg": 90.0,
                        "notes": "Descer até 90 graus",
                        "order": 1,
                    }
                ],
            }
        ],
    }
    response = client.post("/api/v1/workouts", json=payload, headers=personal_headers)
    assert response.status_code == 201
    assert "Location" in response.headers
    data = response.json()
    assert data["title"] == "Treino ABC Força"
    assert len(data["routines"]) == 1
    assert data["routines"][0]["name"] == "Treino A - Inferiores"
    assert len(data["routines"][0]["exercises"]) == 1
    assert data["routines"][0]["exercises"][0]["name"] == "Agachamento Livre"


def test_student_cannot_create_workout_plan(client, student_headers):
    payload = {
        "studentId": "22222222-2222-2222-2222-222222222222",
        "title": "Tentativa Invalida",
        "startDate": "2026-03-01",
    }
    response = client.post("/api/v1/workouts", json=payload, headers=student_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["type"] == "https://api.gymflow.dev/errors/forbidden"


def test_student_views_assigned_workout(client, student_headers):
    workout_id = "55555555-5555-5555-5555-555555555555"
    response = client.get(f"/api/v1/workouts/{workout_id}", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == workout_id
    assert data["title"] == "Ciclo Hipertrofia 1 - Upper/Lower"
    assert len(data["routines"]) >= 1
    assert data["routines"][0]["exercises"][0]["name"] == "Supino Reto com Barra"


def test_patch_workout_plan(client, personal_headers):
    workout_id = "55555555-5555-5555-5555-555555555555"
    payload = {
        "title": "Ciclo Hipertrofia 1 - Atualizado",
        "status": "INACTIVE",
    }
    response = client.patch(f"/api/v1/workouts/{workout_id}", json=payload, headers=personal_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Ciclo Hipertrofia 1 - Atualizado"
    assert data["status"] == "INACTIVE"


def test_delete_workout_plan(client, personal_headers):
    workout_id = "55555555-5555-5555-5555-555555555555"
    response = client.delete(f"/api/v1/workouts/{workout_id}", headers=personal_headers)
    assert response.status_code == 204
    assert response.content == b""

    # Confirm it is deleted
    check = client.get(f"/api/v1/workouts/{workout_id}", headers=personal_headers)
    assert check.status_code == 404


def test_add_routine_to_workout(client, personal_headers):
    workout_id = "55555555-5555-5555-5555-555555555555"
    payload = {
        "name": "Treino B — Costas e Bíceps",
        "dayOfWeek": "Quarta-feira",
        "order": 2,
    }
    response = client.post(f"/api/v1/workouts/{workout_id}/routines", json=payload, headers=personal_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Treino B — Costas e Bíceps"
    assert data["order"] == 2


def test_add_exercise_to_routine(client, personal_headers):
    routine_id = "33333333-3333-3333-3333-333333333333"
    payload = {
        "name": "Desenvolvimento com Halteres",
        "muscleGroup": "SHOULDERS",
        "sets": 3,
        "reps": "10-12",
        "restSeconds": 60,
        "weightKg": 16.0,
        "order": 2,
    }
    response = client.post(f"/api/v1/routines/{routine_id}/exercises", json=payload, headers=personal_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Desenvolvimento com Halteres"
    assert data["muscleGroup"] == "SHOULDERS"
    assert data["routineId"] == routine_id


def test_delete_exercise_returns_204(client, personal_headers):
    exercise_id = "44444444-4444-4444-4444-444444444444"
    response = client.delete(f"/api/v1/exercises/{exercise_id}", headers=personal_headers)
    assert response.status_code == 204
    assert response.content == b""
