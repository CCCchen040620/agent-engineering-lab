import json

from backend.services.task_queue_service import (
    TaskNotFoundError,
    validate_task_status_transition,
)


def encode_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False)


def decode_json(value) -> dict:
    if value is None:
        return {}

    if isinstance(value, str):
        return json.loads(value)

    return value


def row_to_task(row) -> dict:
    return {
        "id": row[0],
        "type": row[1],
        "status": row[2],
        "payload": decode_json(row[3]),
        "result": decode_json(row[4]),
        "error": row[5],
    }


def create_tasks_table_in_postgresql(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                result JSONB NOT NULL DEFAULT '{}'::jsonb,
                error TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    connection.commit()


def insert_task_to_postgresql(
    connection,
    task_type: str,
    payload: dict,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tasks (type, payload)
            VALUES (%s, %s::jsonb)
            RETURNING id, type, status, payload, result, error
            """,
            (task_type, encode_json(payload)),
        )

        row = cursor.fetchone()

    connection.commit()

    return row_to_task(row)


def list_tasks_from_postgresql(
    connection,
    status: str | None = None,
    order: str = "desc",
    limit: int | None = None,
) -> list[dict]:
    order_sql = "DESC" if order == "desc" else "ASC"
    params = []
    where_sql = ""
    limit_sql = ""

    if status not in (None, ""):
        where_sql = "WHERE status = %s"
        params.append(status)

    if limit is not None:
        limit_sql = "LIMIT %s"
        params.append(limit)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id, type, status, payload, result, error
            FROM tasks
            {where_sql}
            ORDER BY id {order_sql}
            {limit_sql}
            """,
            tuple(params),
        )

        rows = cursor.fetchall()

    return [row_to_task(row) for row in rows]


def find_task_from_postgresql(connection, task_id: int) -> dict | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, type, status, payload, result, error
            FROM tasks
            WHERE id = %s
            """,
            (task_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return row_to_task(row)


def update_task_status_in_postgresql(
    connection,
    task_id: int,
    status: str,
    result: dict,
    error: str,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET status = %s,
                result = %s::jsonb,
                error = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, type, status, payload, result, error
            """,
            (status, encode_json(result), error, task_id),
        )

        row = cursor.fetchone()

    connection.commit()

    if row is None:
        raise TaskNotFoundError(f"Task not found: {task_id}")

    return row_to_task(row)


class PostgresqlTaskQueue:
    def __init__(self, connection_factory, auto_initialize: bool = True):
        self.connection_factory = connection_factory
        self.auto_initialize = auto_initialize
        self.tasks_table_ready = False

    def ensure_tasks_table_ready(self) -> None:
        if not self.auto_initialize or self.tasks_table_ready:
            return

        with self.connection_factory() as connection:
            create_tasks_table_in_postgresql(connection)

        self.tasks_table_ready = True

    def create_task(self, task_type: str, payload: dict) -> dict:
        self.ensure_tasks_table_ready()

        with self.connection_factory() as connection:
            return insert_task_to_postgresql(
                connection,
                task_type=task_type,
                payload=payload,
            )

    def list_tasks(
        self,
        status: str | None = None,
        order: str = "desc",
        limit: int | None = None,
    ) -> list[dict]:
        self.ensure_tasks_table_ready()

        with self.connection_factory() as connection:
            return list_tasks_from_postgresql(
                connection,
                status=status,
                order=order,
                limit=limit,
            )

    def get_task(self, task_id: int) -> dict | None:
        self.ensure_tasks_table_ready()

        with self.connection_factory() as connection:
            return find_task_from_postgresql(connection, task_id)

    def get_task_or_raise(self, task_id: int) -> dict:
        task = self.get_task(task_id)

        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        return task

    def mark_task_running(self, task_id: int) -> dict:
        task = self.get_task_or_raise(task_id)
        validate_task_status_transition(task, "running")

        with self.connection_factory() as connection:
            return update_task_status_in_postgresql(
                connection,
                task_id=task_id,
                status="running",
                result=task["result"],
                error=task["error"],
            )

    def mark_task_succeeded(self, task_id: int, result: dict) -> dict:
        task = self.get_task_or_raise(task_id)
        validate_task_status_transition(task, "succeeded")

        with self.connection_factory() as connection:
            return update_task_status_in_postgresql(
                connection,
                task_id=task_id,
                status="succeeded",
                result=result,
                error="",
            )

    def mark_task_failed(self, task_id: int, error: str) -> dict:
        task = self.get_task_or_raise(task_id)
        validate_task_status_transition(task, "failed")

        with self.connection_factory() as connection:
            return update_task_status_in_postgresql(
                connection,
                task_id=task_id,
                status="failed",
                result={},
                error=error,
            )
