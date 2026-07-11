from fastapi.testclient import TestClient
from backend.routers import feedback
from backend.main import app
from backend.routers.feedback import get_feedback_database_path


client = TestClient(app)


def test_create_feedback_endpoint(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_feedback_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/feedback",
        json={
            "question": "新员工什么时候完成安全培训？",
            "answer": "新员工需要在 30 天内完成安全培训。",
            "rating": "helpful",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["question"] == "新员工什么时候完成安全培训？"
    assert data["rating"] == "helpful"


def test_create_feedback_endpoint_rejects_invalid_rating(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_feedback_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/feedback",
        json={
            "question": "新员工什么时候完成安全培训？",
            "answer": "新员工需要在 30 天内完成安全培训。",
            "rating": "bad",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_list_feedback_endpoint(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_feedback_database_path] = lambda: str(database_path)

    client.post(
        "/api/v1/feedback",
        json={
            "question": "新员工什么时候完成安全培训？",
            "answer": "新员工需要在 30 天内完成安全培训。",
            "rating": "helpful",
        },
    )

    response = client.get("/api/v1/feedback")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["rating"] == "helpful"


def test_feedback_summary_endpoint(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_feedback_database_path] = lambda: str(database_path)

    client.post(
        "/api/v1/feedback",
        json={
            "question": "问题1",
            "answer": "回答1",
            "rating": "helpful",
        },
    )
    client.post(
        "/api/v1/feedback",
        json={
            "question": "问题2",
            "answer": "回答2",
            "rating": "not_helpful",
        },
    )

    response = client.get("/api/v1/feedback/summary")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "total": 2,
        "helpful": 1,
        "not_helpful": 1,
    }


def test_feedback_endpoint_uses_config_database_path(tmp_path, monkeypatch):
    app.dependency_overrides.clear()
    database_path = tmp_path / "configured.db"
    monkeypatch.setattr(feedback, "DATABASE_PATH", str(database_path))

    response = client.post(
        "/api/v1/feedback",
        json={
            "question": "新员工什么时候完成安全培训？",
            "answer": "新员工需要在 30 天内完成安全培训。",
            "rating": "helpful",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert database_path.exists()