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
        self.params = None
        self.rows = []
        self.row = None

    def execute(self, sql: str, params=None):
        self.sql = sql
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
    }


def test_create_tasks_table_in_postgresql():
    connection = FakeConnection()

    create_tasks_table_in_postgresql(connection)

    assert "CREATE TABLE IF NOT EXISTS tasks" in connection.cursor_instance.sql
    assert "payload JSONB" in connection.cursor_instance.sql
    assert "result JSONB" in connection.cursor_instance.sql
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
    assert connection.cursor_instance.params == (
        "postgresql_embedding_backfill",
        '{"source": "postgresql"}',
    )
    assert "INSERT INTO tasks" in connection.cursor_instance.sql
    assert "RETURNING id, type, status, payload, result, error" in (
        connection.cursor_instance.sql
    )
    assert connection.committed is True


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
    assert "ORDER BY id ASC" in connection.cursor_instance.sql
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
    assert connection.cursor_instance.params == (
        "succeeded",
        '{"message": "hello"}',
        "",
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
