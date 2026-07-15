import pytest

from backend.services.task_queue_service import (
    InMemoryTaskQueue,
    InvalidTaskStatusTransitionError,
    TaskNotFoundError,
    TaskRunner,
)
from backend.services.task_error_service import TaskExecutionError


def test_create_task():
    queue = InMemoryTaskQueue()

    task = queue.create_task(
        task_type="embedding_backfill",
        payload={"source": "postgresql"},
    )

    assert task["id"] == 1
    assert task["type"] == "embedding_backfill"
    assert task["status"] == "pending"
    assert task["payload"] == {"source": "postgresql"}
    assert task["result"] == {}
    assert task["error"] == ""


def test_list_tasks():
    queue = InMemoryTaskQueue()

    first = queue.create_task(
        task_type="embedding_backfill",
        payload={"source": "postgresql"},
    )
    second = queue.create_task(
        task_type="rag_evaluation",
        payload={"scope": "lightweight"},
    )

    tasks = queue.list_tasks()

    assert tasks == [second, first]


def test_list_tasks_can_filter_by_status():
    queue = InMemoryTaskQueue()

    first = queue.create_task(
        task_type="embedding_backfill",
        payload={"source": "postgresql"},
    )
    second = queue.create_task(
        task_type="rag_evaluation",
        payload={"scope": "lightweight"},
    )

    queue.mark_task_failed(first["id"], "Ollama unavailable")

    tasks = queue.list_tasks(status="pending")

    assert tasks == [second]


def test_list_tasks_can_sort_by_id_desc():
    queue = InMemoryTaskQueue()

    first = queue.create_task(
        task_type="embedding_backfill",
        payload={"source": "postgresql"},
    )
    second = queue.create_task(
        task_type="rag_evaluation",
        payload={"scope": "lightweight"},
    )

    tasks = queue.list_tasks(order="desc")

    assert tasks == [second, first]


def test_list_tasks_can_filter_and_sort():
    queue = InMemoryTaskQueue()

    first = queue.create_task("embedding_backfill", {})
    second = queue.create_task("rag_evaluation", {})
    third = queue.create_task("postgresql_embedding_backfill", {})

    queue.mark_task_failed(first["id"], "Ollama unavailable")
    queue.mark_task_failed(third["id"], "PostgreSQL unavailable")

    tasks = queue.list_tasks(status="failed", order="desc")

    assert tasks == [third, first]
    assert second not in tasks


def test_list_tasks_can_limit_results():
    queue = InMemoryTaskQueue()

    first = queue.create_task("embedding_backfill", {})
    second = queue.create_task("rag_evaluation", {})
    third = queue.create_task("postgresql_embedding_backfill", {})

    tasks = queue.list_tasks(limit=2)

    assert tasks == [third, second]
    assert first not in tasks


def test_list_tasks_can_filter_sort_and_limit():
    queue = InMemoryTaskQueue()

    first = queue.create_task("embedding_backfill", {})
    second = queue.create_task("rag_evaluation", {})
    third = queue.create_task("postgresql_embedding_backfill", {})

    queue.mark_task_failed(first["id"], "Ollama unavailable")
    queue.mark_task_failed(second["id"], "PostgreSQL unavailable")
    queue.mark_task_failed(third["id"], "Unknown error")

    tasks = queue.list_tasks(status="failed", order="desc", limit=2)

    assert tasks == [third, second]
    assert first not in tasks


def test_get_task_by_id():
    queue = InMemoryTaskQueue()

    task = queue.create_task(
        task_type="embedding_backfill",
        payload={"source": "postgresql"},
    )

    found = queue.get_task(task["id"])
    missing = queue.get_task(999)

    assert found == task
    assert missing is None


def test_mark_task_running():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})

    updated = queue.mark_task_running(task["id"])

    assert updated["status"] == "running"


def test_mark_task_succeeded():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})

    queue.mark_task_running(task["id"])

    updated = queue.mark_task_succeeded(
        task_id=task["id"],
        result={"updated": 10},
    )

    assert updated["status"] == "succeeded"
    assert updated["result"] == {"updated": 10}
    assert updated["error"] == ""


def test_mark_task_failed():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})

    updated = queue.mark_task_failed(
        task_id=task["id"],
        error="Ollama unavailable",
    )

    assert updated["status"] == "failed"
    assert updated["result"] == {}
    assert updated["error"] == "Ollama unavailable"


def test_succeeded_task_cannot_be_marked_running_again():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})

    queue.mark_task_running(task["id"])
    queue.mark_task_succeeded(task["id"], {"updated": 10})

    with pytest.raises(InvalidTaskStatusTransitionError):
        queue.mark_task_running(task["id"])


def test_pending_task_cannot_be_marked_succeeded_directly():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})

    with pytest.raises(InvalidTaskStatusTransitionError):
        queue.mark_task_succeeded(task["id"], {"updated": 10})


def test_failed_task_cannot_be_marked_succeeded():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})

    queue.mark_task_failed(task["id"], "Ollama unavailable")

    with pytest.raises(InvalidTaskStatusTransitionError):
        queue.mark_task_succeeded(task["id"], {"updated": 10})


def test_missing_task_raises_task_not_found_error():
    queue = InMemoryTaskQueue()

    with pytest.raises(TaskNotFoundError):
        queue.mark_task_running(999)


def test_task_runner_marks_task_succeeded_when_handler_returns_result():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {"source": "postgresql"})
    runner = TaskRunner(queue)

    def handler(payload):
        return {"updated": 10, "source": payload["source"]}

    result = runner.run_task(task["id"], handler)

    assert result["status"] == "succeeded"
    assert result["result"] == {"updated": 10, "source": "postgresql"}
    assert result["error"] == ""


def test_task_runner_marks_task_failed_when_handler_raises_error():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})
    runner = TaskRunner(queue)

    def handler(payload):
        raise RuntimeError("Ollama unavailable")

    result = runner.run_task(task["id"], handler)

    assert result["status"] == "failed"
    assert result["result"] == {}
    assert result["error"] == "unexpected_error: Ollama unavailable"


def test_task_runner_preserves_structured_task_error_code():
    queue = InMemoryTaskQueue()
    task = queue.create_task("postgresql_document_ingestion", {})
    runner = TaskRunner(queue)

    def handler(payload):
        raise TaskExecutionError(
            "embedding_generation_error",
            "Ollama embedding model unavailable",
        )

    result = runner.run_task(task["id"], handler)

    assert result["status"] == "failed"
    assert result["error"] == (
        "embedding_generation_error: Ollama embedding model unavailable"
    )


def test_task_runner_passes_payload_to_handler():
    queue = InMemoryTaskQueue()
    task = queue.create_task("rag_evaluation", {"scope": "lightweight"})
    runner = TaskRunner(queue)
    captured = {}

    def handler(payload):
        captured["payload"] = payload
        return {"ok": True}

    runner.run_task(task["id"], handler)

    assert captured["payload"] == {"scope": "lightweight"}


def test_task_runner_finishes_running_task_when_handler_returns_result():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {"source": "postgresql"})
    queue.mark_task_running(task["id"])
    runner = TaskRunner(queue)

    def handler(payload):
        return {"updated": 10, "source": payload["source"]}

    result = runner.finish_running_task(task["id"], handler)

    assert result["status"] == "succeeded"
    assert result["result"] == {"updated": 10, "source": "postgresql"}
    assert result["error"] == ""


def test_task_runner_marks_running_task_failed_when_handler_raises_error():
    queue = InMemoryTaskQueue()
    task = queue.create_task("embedding_backfill", {})
    queue.mark_task_running(task["id"])
    runner = TaskRunner(queue)

    def handler(payload):
        raise RuntimeError("Ollama unavailable")

    result = runner.finish_running_task(task["id"], handler)

    assert result["status"] == "failed"
    assert result["result"] == {}
    assert result["error"] == "unexpected_error: Ollama unavailable"
