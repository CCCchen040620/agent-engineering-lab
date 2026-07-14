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


def test_run_task_endpoint_can_run_postgresql_embedding_backfill(monkeypatch):
    from backend.services import task_dispatcher_service

    def fake_backfill_postgresql_chunk_embeddings():
        return {
            "total_chunks": 3,
            "updated_embeddings": 2,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_postgresql_chunk_embeddings",
        fake_backfill_postgresql_chunk_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/run")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "succeeded"
    assert data["result"] == {
        "total_chunks": 3,
        "updated_embeddings": 2,
        "skipped_embeddings": 1,
        "model": "fake-model",
    }


def test_create_and_run_postgresql_embedding_backfill_task(monkeypatch):
    from backend.services import task_dispatcher_service

    def fake_backfill_postgresql_chunk_embeddings():
        return {
            "total_chunks": 5,
            "updated_embeddings": 4,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_postgresql_chunk_embeddings",
        fake_backfill_postgresql_chunk_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post("/api/v1/tasks/postgresql-embedding-backfill")

    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "postgresql_embedding_backfill"
    assert data["status"] == "succeeded"
    assert data["result"] == {
        "total_chunks": 5,
        "updated_embeddings": 4,
        "skipped_embeddings": 1,
        "model": "fake-model",
    }