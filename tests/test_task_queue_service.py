import pytest

from backend.services.task_queue_service import (
    InMemoryTaskQueue,
    InvalidTaskStatusTransitionError,
    TaskNotFoundError,
)


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

    assert tasks == [first, second]


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