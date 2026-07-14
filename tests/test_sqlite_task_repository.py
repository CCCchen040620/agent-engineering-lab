import sqlite3

from backend.services.sqlite_task_repository import (
    create_tasks_table,
    create_task,
    list_tasks,
    find_task_by_id,
)


def create_test_connection():
    return sqlite3.connect(":memory:")


def test_create_tasks_table():
    connection = create_test_connection()

    create_tasks_table(connection)

    cursor = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    )
    row = cursor.fetchone()

    assert row is not None


def test_create_task():
    connection = create_test_connection()
    create_tasks_table(connection)

    task = create_task(
        connection,
        task_type="postgresql_embedding_backfill",
        payload={"source": "postgresql"},
    )

    assert task == {
        "id": 1,
        "type": "postgresql_embedding_backfill",
        "status": "pending",
        "payload": {"source": "postgresql"},
        "result": {},
        "error": "",
    }


def test_list_and_find_tasks():
    connection = create_test_connection()
    create_tasks_table(connection)

    created_task = create_task(
        connection,
        task_type="postgresql_embedding_backfill",
        payload={},
    )

    tasks = list_tasks(connection)
    found_task = find_task_by_id(connection, created_task["id"])

    assert tasks == [created_task]
    assert found_task == created_task