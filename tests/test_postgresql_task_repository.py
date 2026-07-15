import pytest

import backend.services.postgresql_task_repository as repository
from backend.services.postgresql_task_repository import (
    PostgresqlTaskQueue,
    create_tasks_table_in_postgresql,
    decode_json,
    encode_json,
    find_task_from_postgresql,
    insert_task_to_postgresql,
    list_tasks_from_postgresql,
    row_to_task,
    update_task_status_in_postgresql,
)
from backend.services.task_queue_service import (
    InvalidTaskStatusTransitionError,
    TaskNotFoundError,
)


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.executed_sql = []
        self.params = None
        self.rows = []
        self.row = None

    def execute(self, sql: str, params=None):
        self.sql = sql
        self.executed_sql.append(sql)
        self.params = params

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def test_encode_and_decode_json():
    value = {"message": "你好", "count": 2}

    encoded = encode_json(value)

    assert decode_json(encoded) == value


def test_decode_json_defaults_to_empty_dict():
    assert decode_json(None) == {}


def test_row_to_task():
    row = (
        1,
        "postgresql_embedding_backfill",
        "pending",
        {"source": "postgresql"},
        {"updated_embeddings": 3},
        "",
    )

    task = row_to_task(row)

    assert task == {
        "id": 1,
        "type": "postgresql_embedding_backfill",
        "status": "pending",
        "payload": {"source": "postgresql"},
        "result": {"updated_embeddings": 3},
        "error": "",
        "progress_percent": 0,
        "progress_message": "等待执行",
        "retry_of_task_id": None,
    }


def test_create_tasks_table_in_postgresql():
    connection = FakeConnection()

    create_tasks_table_in_postgresql(connection)

    sql_text = "\n".join(connection.cursor_instance.executed_sql)

    assert "CREATE TABLE IF NOT EXISTS tasks" in sql_text
    assert "payload JSONB" in sql_text
    assert "result JSONB" in sql_text
    assert "progress_percent INTEGER" in sql_text
    assert "progress_message TEXT" in sql_text
    assert "ADD COLUMN IF NOT EXISTS progress_percent" in sql_text
    assert "ADD COLUMN IF NOT EXISTS progress_message" in sql_text
    assert connection.committed is True


def test_insert_task_to_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (
        1,
        "postgresql_embedding_backfill",
        "pending",
        {"source": "postgresql"},
        {},
        "",
    )

    task = insert_task_to_postgresql(
        connection,
        task_type="postgresql_embedding_backfill",
        payload={"source": "postgresql"},
    )

    assert task["id"] == 1
    assert task["status"] == "pending"
    assert task["progress_percent"] == 0
    assert task["progress_message"] == "等待执行"
    assert connection.cursor_instance.params == (
        "postgresql_embedding_backfill",
        '{"source": "postgresql"}',
        None,
    )
    assert "INSERT INTO tasks" in connection.cursor_instance.sql
    assert "RETURNING id, type, status, payload, result, error" in (
        connection.cursor_instance.sql
    )
    assert "progress_percent, progress_message" in connection.cursor_instance.sql
    assert connection.committed is True


def test_insert_retry_task_to_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (
        2,
        "postgresql_embedding_backfill",
        "pending",
        {},
        {},
        "",
        0,
        "等待执行",
        1,
    )

    task = insert_task_to_postgresql(
        connection,
        task_type="postgresql_embedding_backfill",
        payload={},
        retry_of_task_id=1,
    )

    assert task["id"] == 2
    assert task["retry_of_task_id"] == 1
    assert connection.cursor_instance.params == (
        "postgresql_embedding_backfill",
        "{}",
        1,
    )


def test_list_tasks_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (1, "echo", "pending", {"message": "first"}, {}, ""),
        (2, "rag_evaluation", "failed", {}, {}, "failed"),
    ]

    tasks = list_tasks_from_postgresql(connection)

    assert len(tasks) == 2
    assert tasks[0]["type"] == "echo"
    assert tasks[1]["status"] == "failed"
    assert "FROM tasks" in connection.cursor_instance.sql
    assert "ORDER BY id DESC" in connection.cursor_instance.sql
    assert connection.cursor_instance.params == ()


def test_list_tasks_from_postgresql_can_filter_sort_and_limit():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (3, "rag_evaluation", "failed", {}, {}, "failed"),
    ]

    tasks = list_tasks_from_postgresql(
        connection,
        status="failed",
        order="desc",
        limit=2,
    )

    assert tasks[0]["id"] == 3
    assert "WHERE status = %s" in connection.cursor_instance.sql
    assert "ORDER BY id DESC" in connection.cursor_instance.sql
    assert "LIMIT %s" in connection.cursor_instance.sql
    assert connection.cursor_instance.params == ("failed", 2)


def test_find_task_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (
        1,
        "echo",
        "pending",
        {"message": "hello"},
        {},
        "",
    )

    task = find_task_from_postgresql(connection, task_id=1)

    assert task["payload"] == {"message": "hello"}
    assert connection.cursor_instance.params == (1,)
    assert "WHERE id = %s" in connection.cursor_instance.sql


def test_find_task_from_postgresql_returns_none_when_missing():
    connection = FakeConnection()
    connection.cursor_instance.row = None

    task = find_task_from_postgresql(connection, task_id=999)

    assert task is None


def test_update_task_status_in_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (
        1,
        "echo",
        "succeeded",
        {"message": "hello"},
        {"message": "hello"},
        "",
    )

    task = update_task_status_in_postgresql(
        connection,
        task_id=1,
        status="succeeded",
        result={"message": "hello"},
        error="",
    )

    assert task["status"] == "succeeded"
    assert task["result"] == {"message": "hello"}
    assert task["progress_percent"] == 100
    assert task["progress_message"] == "任务完成"
    assert connection.cursor_instance.params == (
        "succeeded",
        '{"message": "hello"}',
        "",
        100,
        "任务完成",
        1,
    )
    assert "UPDATE tasks" in connection.cursor_instance.sql
    assert "updated_at = NOW()" in connection.cursor_instance.sql
    assert connection.committed is True


def test_update_task_status_in_postgresql_raises_when_missing():
    connection = FakeConnection()
    connection.cursor_instance.row = None

    with pytest.raises(TaskNotFoundError):
        update_task_status_in_postgresql(
            connection,
            task_id=404,
            status="running",
            result={},
            error="",
        )


def test_postgresql_task_queue_marks_task_running(monkeypatch):
    connection = FakeConnection()
    tasks = {
        1: {
            "id": 1,
            "type": "echo",
            "status": "pending",
            "payload": {},
            "result": {},
            "error": "",
            "progress_percent": 0,
            "progress_message": "等待执行",
        }
    }

    def fake_find_task_from_postgresql(connection, task_id: int):
        return dict(tasks[task_id])

    def fake_update_task_status_in_postgresql(
        connection,
        task_id: int,
        status: str,
        result: dict,
        error: str,
    ):
        tasks[task_id]["status"] = status
        tasks[task_id]["result"] = result
        tasks[task_id]["error"] = error
        return dict(tasks[task_id])

    monkeypatch.setattr(
        repository,
        "find_task_from_postgresql",
        fake_find_task_from_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "update_task_status_in_postgresql",
        fake_update_task_status_in_postgresql,
    )

    queue = PostgresqlTaskQueue(connection_factory=lambda: connection)

    task = queue.mark_task_running(1)

    assert task["status"] == "running"


def test_postgresql_task_queue_marks_task_canceled(monkeypatch):
    connection = FakeConnection()
    tasks = {
        1: {
            "id": 1,
            "type": "echo",
            "status": "pending",
            "payload": {},
            "result": {},
            "error": "",
            "progress_percent": 0,
            "progress_message": "等待执行",
            "retry_of_task_id": None,
        }
    }

    def fake_find_task_from_postgresql(connection, task_id: int):
        return dict(tasks[task_id])

    def fake_update_task_status_in_postgresql(
        connection,
        task_id: int,
        status: str,
        result: dict,
        error: str,
    ):
        tasks[task_id]["status"] = status
        tasks[task_id]["result"] = result
        tasks[task_id]["error"] = error
        tasks[task_id]["progress_percent"] = 100
        tasks[task_id]["progress_message"] = "任务已取消"
        return dict(tasks[task_id])

    monkeypatch.setattr(
        repository,
        "find_task_from_postgresql",
        fake_find_task_from_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "update_task_status_in_postgresql",
        fake_update_task_status_in_postgresql,
    )

    queue = PostgresqlTaskQueue(connection_factory=lambda: connection)

    task = queue.mark_task_canceled(1)

    assert task["status"] == "canceled"
    assert task["progress_message"] == "任务已取消"


def test_postgresql_task_queue_auto_initializes_tasks_table(monkeypatch):
    connection = FakeConnection()
    calls = {
        "create_table": 0,
        "insert": 0,
    }

    def fake_create_tasks_table_in_postgresql(connection):
        calls["create_table"] += 1

    def fake_insert_task_to_postgresql(
        connection,
        task_type: str,
        payload: dict,
        retry_of_task_id: int | None = None,
    ):
        calls["insert"] += 1

        return {
            "id": calls["insert"],
            "type": task_type,
            "status": "pending",
            "payload": payload,
            "result": {},
            "error": "",
            "progress_percent": 0,
            "progress_message": "等待执行",
            "retry_of_task_id": retry_of_task_id,
        }

    monkeypatch.setattr(
        repository,
        "create_tasks_table_in_postgresql",
        fake_create_tasks_table_in_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "insert_task_to_postgresql",
        fake_insert_task_to_postgresql,
    )

    queue = PostgresqlTaskQueue(connection_factory=lambda: connection)

    first_task = queue.create_task("echo", {"message": "first"})
    second_task = queue.create_task("echo", {"message": "second"})

    assert first_task["id"] == 1
    assert second_task["id"] == 2
    assert calls == {
        "create_table": 1,
        "insert": 2,
    }
    assert queue.tasks_table_ready is True


def test_postgresql_task_queue_can_disable_auto_initialize(monkeypatch):
    connection = FakeConnection()
    calls = {
        "create_table": 0,
        "insert": 0,
    }

    def fake_create_tasks_table_in_postgresql(connection):
        calls["create_table"] += 1

    def fake_insert_task_to_postgresql(
        connection,
        task_type: str,
        payload: dict,
        retry_of_task_id: int | None = None,
    ):
        calls["insert"] += 1

        return {
            "id": 1,
            "type": task_type,
            "status": "pending",
            "payload": payload,
            "result": {},
            "error": "",
            "progress_percent": 0,
            "progress_message": "等待执行",
            "retry_of_task_id": retry_of_task_id,
        }

    monkeypatch.setattr(
        repository,
        "create_tasks_table_in_postgresql",
        fake_create_tasks_table_in_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "insert_task_to_postgresql",
        fake_insert_task_to_postgresql,
    )

    queue = PostgresqlTaskQueue(
        connection_factory=lambda: connection,
        auto_initialize=False,
    )

    task = queue.create_task("echo", {"message": "hello"})

    assert task["payload"] == {"message": "hello"}
    assert calls == {
        "create_table": 0,
        "insert": 1,
    }
    assert queue.tasks_table_ready is False


def test_postgresql_task_queue_reads_task_after_queue_is_recreated(monkeypatch):
    connection = FakeConnection()
    persistent_tasks = {}
    next_id = {"value": 1}

    def fake_create_tasks_table_in_postgresql(connection):
        pass

    def fake_insert_task_to_postgresql(
        connection,
        task_type: str,
        payload: dict,
        retry_of_task_id: int | None = None,
    ):
        task_id = next_id["value"]
        next_id["value"] += 1
        task = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "payload": payload,
            "result": {},
            "error": "",
            "progress_percent": 0,
            "progress_message": "等待执行",
            "retry_of_task_id": retry_of_task_id,
        }
        persistent_tasks[task_id] = task

        return dict(task)

    def fake_find_task_from_postgresql(connection, task_id: int):
        task = persistent_tasks.get(task_id)

        if task is None:
            return None

        return dict(task)

    def fake_list_tasks_from_postgresql(
        connection,
        status=None,
        order="desc",
        limit=None,
    ):
        tasks = list(persistent_tasks.values())

        if status not in (None, ""):
            tasks = [
                task
                for task in tasks
                if task["status"] == status
            ]

        tasks = sorted(
            tasks,
            key=lambda task: task["id"],
            reverse=order == "desc",
        )

        if limit is not None:
            tasks = tasks[:limit]

        return [dict(task) for task in tasks]

    def fake_update_task_status_in_postgresql(
        connection,
        task_id: int,
        status: str,
        result: dict,
        error: str,
    ):
        persistent_tasks[task_id]["status"] = status
        persistent_tasks[task_id]["result"] = result
        persistent_tasks[task_id]["error"] = error
        if status == "running":
            persistent_tasks[task_id]["progress_percent"] = 50
            persistent_tasks[task_id]["progress_message"] = "任务运行中"
        elif status == "succeeded":
            persistent_tasks[task_id]["progress_percent"] = 100
            persistent_tasks[task_id]["progress_message"] = "任务完成"
        elif status == "failed":
            persistent_tasks[task_id]["progress_percent"] = 100
            persistent_tasks[task_id]["progress_message"] = "任务失败"

        return dict(persistent_tasks[task_id])

    monkeypatch.setattr(
        repository,
        "create_tasks_table_in_postgresql",
        fake_create_tasks_table_in_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "insert_task_to_postgresql",
        fake_insert_task_to_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "find_task_from_postgresql",
        fake_find_task_from_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "list_tasks_from_postgresql",
        fake_list_tasks_from_postgresql,
    )
    monkeypatch.setattr(
        repository,
        "update_task_status_in_postgresql",
        fake_update_task_status_in_postgresql,
    )

    first_queue_instance = PostgresqlTaskQueue(connection_factory=lambda: connection)
    created_task = first_queue_instance.create_task(
        "echo",
        {"message": "persist me"},
    )
    first_queue_instance.mark_task_running(created_task["id"])
    first_queue_instance.mark_task_succeeded(
        created_task["id"],
        {"message": "persist me"},
    )

    recreated_queue_instance = PostgresqlTaskQueue(connection_factory=lambda: connection)

    found_task = recreated_queue_instance.get_task(created_task["id"])
    listed_tasks = recreated_queue_instance.list_tasks()

    assert found_task == {
        "id": created_task["id"],
        "type": "echo",
        "status": "succeeded",
        "payload": {"message": "persist me"},
        "result": {"message": "persist me"},
        "error": "",
        "progress_percent": 100,
        "progress_message": "任务完成",
        "retry_of_task_id": None,
    }
    assert listed_tasks == [found_task]
    assert recreated_queue_instance is not first_queue_instance


def test_postgresql_task_queue_rejects_invalid_status_transition(monkeypatch):
    connection = FakeConnection()

    def fake_find_task_from_postgresql(connection, task_id: int):
        return {
            "id": task_id,
            "type": "echo",
            "status": "succeeded",
            "payload": {},
            "result": {},
            "error": "",
        }

    monkeypatch.setattr(
        repository,
        "find_task_from_postgresql",
        fake_find_task_from_postgresql,
    )

    queue = PostgresqlTaskQueue(connection_factory=lambda: connection)

    with pytest.raises(InvalidTaskStatusTransitionError):
        queue.mark_task_running(1)
