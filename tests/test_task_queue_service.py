from backend.services.task_queue_service import InMemoryTaskQueue


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