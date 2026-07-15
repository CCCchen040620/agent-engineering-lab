import time
from threading import Event

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import tasks as tasks_router
from backend.routers.tasks import get_task_queue
from backend.services.postgresql_task_repository import PostgresqlTaskQueue
from backend.services.task_queue_service import InMemoryTaskQueue


client = TestClient(app)


class FakePostgreSQLConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service):
    monkeypatch.setattr(
        task_dispatcher_service.psycopg,
        "connect",
        lambda database_url: FakePostgreSQLConnection(),
    )
    monkeypatch.setattr(
        task_dispatcher_service,
        "initialize_postgresql_knowledge_schema",
        lambda connection: None,
    )


def setup_function():
    app.dependency_overrides.clear()


def wait_for_task_status(
    queue: InMemoryTaskQueue,
    task_id: int,
    expected_status: str,
    timeout_seconds: float = 1.0,
) -> dict:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        task = queue.get_task(task_id)

        if task is not None and task["status"] == expected_status:
            return task

        time.sleep(0.01)

    raise AssertionError(f"Task {task_id} did not become {expected_status}.")


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


def test_build_default_task_queue_uses_memory_for_sqlite():
    queue = tasks_router.build_default_task_queue("sqlite:///data/app.db")

    assert isinstance(queue, InMemoryTaskQueue)


def test_build_default_task_queue_uses_postgresql_for_postgresql_url():
    queue = tasks_router.build_default_task_queue(
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    assert isinstance(queue, PostgresqlTaskQueue)


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


def test_run_task_async_endpoint_returns_running_then_succeeded(monkeypatch):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)
    handler_started = Event()
    release_handler = Event()

    def fake_backfill_missing_postgresql_chunk_embeddings(connection):
        handler_started.set()
        assert release_handler.wait(timeout=1)

        return {
            "total_chunks": 3,
            "updated_embeddings": 2,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_missing_postgresql_chunk_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/run-async")

    assert response.status_code == 202

    data = response.json()
    assert data["id"] == task["id"]
    assert data["status"] == "running"

    assert handler_started.wait(timeout=1)
    assert test_queue.get_task(task["id"])["status"] == "running"

    release_handler.set()
    completed_task = wait_for_task_status(test_queue, task["id"], "succeeded")

    assert completed_task["result"] == {
        "total_chunks": 3,
        "updated_embeddings": 2,
        "skipped_embeddings": 1,
        "model": "fake-model",
    }


def test_run_task_async_endpoint_returns_404_when_task_not_found():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post("/api/v1/tasks/999/run-async")

    assert response.status_code == 404


def test_retry_task_async_endpoint_creates_new_running_task_from_failed_task(
    monkeypatch,
):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)
    handler_started = Event()
    release_handler = Event()

    def fake_backfill_missing_postgresql_chunk_embeddings(connection):
        handler_started.set()
        assert release_handler.wait(timeout=1)

        return {
            "total_chunks": 3,
            "updated_embeddings": 2,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_missing_postgresql_chunk_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    failed_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    test_queue.mark_task_failed(failed_task["id"], "Ollama unavailable")
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{failed_task['id']}/retry-async")

    assert response.status_code == 202

    data = response.json()
    assert data["id"] != failed_task["id"]
    assert data["type"] == failed_task["type"]
    assert data["payload"] == failed_task["payload"]
    assert data["status"] == "running"
    assert data["retry_of_task_id"] == failed_task["id"]

    assert test_queue.get_task(failed_task["id"])["status"] == "failed"
    assert handler_started.wait(timeout=1)

    release_handler.set()
    completed_task = wait_for_task_status(test_queue, data["id"], "succeeded")

    assert completed_task["result"] == {
        "total_chunks": 3,
        "updated_embeddings": 2,
        "skipped_embeddings": 1,
        "model": "fake-model",
    }


def test_retry_task_async_endpoint_rejects_non_failed_task():
    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="echo",
        payload={"message": "hello"},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/retry-async")

    assert response.status_code == 409
    assert response.json()["detail"] == "只有失败任务可以重试。"


def test_retry_task_async_endpoint_returns_404_when_task_not_found():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post("/api/v1/tasks/999/retry-async")

    assert response.status_code == 404


def test_cancel_task_endpoint_cancels_pending_task():
    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="echo",
        payload={"message": "hello"},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/cancel")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == task["id"]
    assert data["status"] == "canceled"
    assert data["progress_percent"] == 100
    assert data["progress_message"] == "任务已取消"


def test_cancel_task_endpoint_rejects_running_task():
    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="echo",
        payload={"message": "hello"},
    )
    test_queue.mark_task_running(task["id"])
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/cancel")

    assert response.status_code == 409
    assert response.json()["detail"] == "只有等待执行的任务可以取消。"


def test_cancel_task_endpoint_returns_404_when_task_not_found():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post("/api/v1/tasks/999/cancel")

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

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)

    def fake_backfill_missing_postgresql_chunk_embeddings(connection):
        return {
            "total_chunks": 3,
            "updated_embeddings": 2,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_missing_postgresql_chunk_embeddings,
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


def test_run_task_endpoint_can_run_postgresql_document_ingestion(monkeypatch):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        return {
            "document": {
                "id": 9,
                "title": title,
                "file_type": file_type,
                "chunk_count": 2,
                "is_indexed": True,
                "source": source,
            },
            "chunks": [
                {"id": 1},
                {"id": 2},
            ],
            "embeddings": [
                {"id": 1},
                {"id": 2},
            ],
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    task = test_queue.create_task(
        task_type="postgresql_document_ingestion",
        payload={
            "title": "PostgreSQL 任务入库文档",
            "file_type": "md",
            "content": "员工参加外部培训需要提前提交申请。",
        },
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(f"/api/v1/tasks/{task['id']}/run")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "succeeded"
    assert data["result"] == {
        "document_id": 9,
        "title": "PostgreSQL 任务入库文档",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "production",
        "embedding_count": 2,
    }


def test_create_and_run_postgresql_embedding_backfill_task(monkeypatch):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)

    def fake_backfill_missing_postgresql_chunk_embeddings(connection):
        return {
            "total_chunks": 5,
            "updated_embeddings": 4,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_missing_postgresql_chunk_embeddings,
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


def test_create_and_run_postgresql_embedding_backfill_task_returns_failed_task_when_error(
    monkeypatch,
):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)

    def fake_backfill_missing_postgresql_chunk_embeddings(connection):
        raise RuntimeError("Ollama is not available")

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_missing_postgresql_chunk_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post("/api/v1/tasks/postgresql-embedding-backfill")

    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "postgresql_embedding_backfill"
    assert data["status"] == "failed"
    assert data["result"] == {}
    assert "Ollama is not available" in data["error"]


def test_create_and_run_postgresql_document_ingestion_task(monkeypatch):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        return {
            "document": {
                "id": 10,
                "title": title,
                "file_type": file_type,
                "chunk_count": 2,
                "is_indexed": True,
                "source": source,
            },
            "chunks": [
                {"id": 1},
                {"id": 2},
            ],
            "embeddings": [
                {"id": 1},
                {"id": 2},
            ],
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(
        "/api/v1/tasks/postgresql-document-ingestion",
        json={
            "title": "PostgreSQL 专用任务入库文档",
            "file_type": "md",
            "content": "员工参加外部培训需要提前提交申请。",
            "source": "production",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "postgresql_document_ingestion"
    assert data["status"] == "succeeded"
    assert data["payload"] == {
        "title": "PostgreSQL 专用任务入库文档",
        "file_type": "md",
        "content": "员工参加外部培训需要提前提交申请。",
        "source": "production",
    }
    assert data["result"] == {
        "document_id": 10,
        "title": "PostgreSQL 专用任务入库文档",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "production",
        "embedding_count": 2,
    }


def test_create_and_run_postgresql_document_ingestion_task_async(monkeypatch):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)
    handler_started = Event()
    release_handler = Event()

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        handler_started.set()
        assert release_handler.wait(timeout=1)

        return {
            "document": {
                "id": 11,
                "title": title,
                "file_type": file_type,
                "chunk_count": 2,
                "is_indexed": True,
                "source": source,
            },
            "chunks": [
                {"id": 1},
                {"id": 2},
            ],
            "embeddings": [
                {"id": 1},
                {"id": 2},
            ],
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(
        "/api/v1/tasks/postgresql-document-ingestion/run-async",
        json={
            "title": "PostgreSQL 异步任务入库文档",
            "file_type": "md",
            "content": "员工参加外部培训需要提前提交申请。",
            "source": "production",
        },
    )

    assert response.status_code == 202

    data = response.json()
    assert data["type"] == "postgresql_document_ingestion"
    assert data["status"] == "running"
    assert data["payload"] == {
        "title": "PostgreSQL 异步任务入库文档",
        "file_type": "md",
        "content": "员工参加外部培训需要提前提交申请。",
        "source": "production",
    }

    assert handler_started.wait(timeout=1)
    assert test_queue.get_task(data["id"])["status"] == "running"

    release_handler.set()
    completed_task = wait_for_task_status(test_queue, data["id"], "succeeded")

    assert completed_task["result"] == {
        "document_id": 11,
        "title": "PostgreSQL 异步任务入库文档",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "production",
        "embedding_count": 2,
    }


def test_create_and_run_postgresql_document_ingestion_task_marks_failed_when_not_created(
    monkeypatch,
):
    from backend.services import task_dispatcher_service

    isolate_postgresql_backfill_connection(monkeypatch, task_dispatcher_service)

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        return None

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(
        "/api/v1/tasks/postgresql-document-ingestion",
        json={
            "title": "重复文档",
            "file_type": "md",
            "content": "员工参加外部培训需要提前提交申请。",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["type"] == "postgresql_document_ingestion"
    assert data["status"] == "failed"
    assert data["result"] == {}
    assert "duplicate title or empty content" in data["error"]


def test_create_and_run_postgresql_document_ingestion_task_rejects_invalid_payload():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.post(
        "/api/v1/tasks/postgresql-document-ingestion",
        json={
            "title": "",
            "file_type": "md",
            "content": "员工参加外部培训需要提前提交申请。",
        },
    )

    assert response.status_code == 422


def test_list_tasks_endpoint():
    test_queue = InMemoryTaskQueue()
    first_task = test_queue.create_task(
        task_type="echo",
        payload={"message": "first"},
    )
    second_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks")

    assert response.status_code == 200
    assert response.json() == [second_task, first_task]


def test_list_tasks_endpoint_can_filter_by_status():
    test_queue = InMemoryTaskQueue()
    first_task = test_queue.create_task(
        task_type="echo",
        payload={"message": "first"},
    )
    second_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    test_queue.mark_task_failed(first_task["id"], "Task failed")
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks?status=pending")

    assert response.status_code == 200
    assert response.json() == [second_task]


def test_list_tasks_endpoint_can_sort_by_order_desc():
    test_queue = InMemoryTaskQueue()
    first_task = test_queue.create_task(
        task_type="echo",
        payload={"message": "first"},
    )
    second_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks?order=desc")

    assert response.status_code == 200
    assert response.json() == [second_task, first_task]


def test_list_tasks_endpoint_can_filter_and_sort():
    test_queue = InMemoryTaskQueue()
    first_task = test_queue.create_task(
        task_type="echo",
        payload={"message": "first"},
    )
    second_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    third_task = test_queue.create_task(
        task_type="rag_evaluation",
        payload={},
    )
    test_queue.mark_task_failed(first_task["id"], "Task failed")
    test_queue.mark_task_failed(third_task["id"], "Task failed")
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks?status=failed&order=desc")

    assert response.status_code == 200
    assert response.json() == [third_task, first_task]
    assert second_task not in response.json()


def test_list_tasks_endpoint_can_limit_results():
    test_queue = InMemoryTaskQueue()
    first_task = test_queue.create_task(
        task_type="echo",
        payload={"message": "first"},
    )
    second_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    third_task = test_queue.create_task(
        task_type="rag_evaluation",
        payload={},
    )
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks?limit=2")

    assert response.status_code == 200
    assert response.json() == [third_task, second_task]
    assert first_task not in response.json()


def test_list_tasks_endpoint_can_filter_sort_and_limit():
    test_queue = InMemoryTaskQueue()
    first_task = test_queue.create_task(
        task_type="echo",
        payload={"message": "first"},
    )
    second_task = test_queue.create_task(
        task_type="postgresql_embedding_backfill",
        payload={},
    )
    third_task = test_queue.create_task(
        task_type="rag_evaluation",
        payload={},
    )
    test_queue.mark_task_failed(first_task["id"], "Task failed")
    test_queue.mark_task_failed(second_task["id"], "Task failed")
    test_queue.mark_task_failed(third_task["id"], "Task failed")
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks?status=failed&order=desc&limit=2")

    assert response.status_code == 200
    assert response.json() == [third_task, second_task]
    assert first_task not in response.json()


def test_list_tasks_endpoint_rejects_invalid_limit():
    test_queue = InMemoryTaskQueue()
    app.dependency_overrides[get_task_queue] = lambda: test_queue

    response = client.get("/api/v1/tasks?limit=0")

    assert response.status_code == 422
