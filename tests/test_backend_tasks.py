from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.tasks import get_task_queue
from backend.services.task_queue_service import InMemoryTaskQueue


client = TestClient(app)


def setup_function():
    app.dependency_overrides.clear()


def test_create_task_endpoint():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(
        "/api/v1/tasks",
        json={
            "type": "embedding_backfill",
            "payload": {"backend": "postgresql"},
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["type"] == "embedding_backfill"
    assert data["status"] == "pending"
    assert data["payload"] == {"backend": "postgresql"}
    assert data["result"] == {}
    assert data["error"] == ""


def test_get_task_endpoint():
    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="embedding_backfill",
        payload={"backend": "postgresql"},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get(f"/api/v1/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == task


def test_get_task_endpoint_returns_404_when_task_not_found():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks/999")

    assert response.status_code == 404