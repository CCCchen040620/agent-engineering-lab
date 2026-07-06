from fastapi.testclient import TestClient

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