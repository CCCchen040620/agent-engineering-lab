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


def test_run_task_endpoint_marks_task_succeeded():
    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="echo",
        payload={"message": "hello"},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/run")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task["id"]
    assert data["status"] == "succeeded"
    assert data["result"] == {"message": "hello"}
    assert data["error"] == ""


def test_run_task_endpoint_returns_404_when_task_not_found():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post("/api/v1/tasks/999/run")

    assert response.status_code == 404


def test_run_task_endpoint_marks_task_failed_when_task_type_is_unsupported():
    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="unknown_task",
        payload={},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/run")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task["id"]
    assert data["status"] == "failed"
    assert "Unsupported task type" in data["error"]