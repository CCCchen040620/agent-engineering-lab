import json

from backend.services.task_queue_service import (
    TaskNotFoundError,
    build_task_progress,
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
    progress = build_task_progress(row[2])
    progress_percent = row[6] if len(row) > 6 else progress["progress_percent"]
    progress_message = row[7] if len(row) > 7 else progress["progress_message"]
    retry_of_task_id = row[8] if len(row) > 8 else None
    run_count = row[9] if len(row) > 9 else 0
    retry_count = row[10] if len(row) > 10 else 0

    return {
        "id": row[0],
        "type": row[1],
        "status": row[2],
        "payload": decode_json(row[3]),
        "result": decode_json(row[4]),
        "error": row[5],
        "progress_percent": progress_percent,
        "progress_message": progress_message,
        "retry_of_task_id": retry_of_task_id,
        "run_count": run_count,
        "retry_count": retry_count,
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
                progress_percent INTEGER NOT NULL DEFAULT 0,
                progress_message TEXT NOT NULL DEFAULT '等待执行',
                retry_of_task_id INTEGER,
                run_count INTEGER NOT NULL DEFAULT 0,
                retry_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS progress_percent INTEGER NOT NULL DEFAULT 0
            """
        )
        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS progress_message TEXT NOT NULL DEFAULT '等待执行'
            """
        )
        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS retry_of_task_id INTEGER
            """
        )
        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS run_count INTEGER NOT NULL DEFAULT 0
            """
        )
        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0
            """
        )

    connection.commit()


def insert_task_to_postgresql(
    connection,
    task_type: str,
    payload: dict,
    retry_of_task_id: int | None = None,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO tasks (type, payload, retry_of_task_id)
            VALUES (%s, %s::jsonb, %s)
            RETURNING id, type, status, payload, result, error,
                      progress_percent, progress_message, retry_of_task_id,
                      run_count, retry_count
            """,
            (task_type, encode_json(payload), retry_of_task_id),
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
                   , progress_percent, progress_message, retry_of_task_id,
                     run_count, retry_count
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
                   , progress_percent, progress_message, retry_of_task_id,
                     run_count, retry_count
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
    run_count: int | None = None,
    retry_count: int | None = None,
) -> dict:
    progress = build_task_progress(status)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET status = %s,
                result = %s::jsonb,
                error = %s,
                progress_percent = %s,
                progress_message = %s,
                run_count = COALESCE(%s, run_count),
                retry_count = COALESCE(%s, retry_count),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, type, status, payload, result, error,
                      progress_percent, progress_message, retry_of_task_id,
                      run_count, retry_count
            """,
            (
                status,
                encode_json(result),
                error,
                progress["progress_percent"],
                progress["progress_message"],
                run_count,
                retry_count,
                task_id,
            ),
        )

        row = cursor.fetchone()

    connection.commit()

    if row is None:
        raise TaskNotFoundError(f"Task not found: {task_id}")

    return row_to_task(row)


def increment_task_retry_count_in_postgresql(connection, task_id: int) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE tasks
            SET retry_count = retry_count + 1,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, type, status, payload, result, error,
                      progress_percent, progress_message, retry_of_task_id,
                      run_count, retry_count
            """,
            (task_id,),
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

    def create_task(
        self,
        task_type: str,
        payload: dict,
        retry_of_task_id: int | None = None,
    ) -> dict:
        self.ensure_tasks_table_ready()

        with self.connection_factory() as connection:
            return insert_task_to_postgresql(
                connection,
                task_type=task_type,
                payload=payload,
                retry_of_task_id=retry_of_task_id,
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
                run_count=task.get("run_count", 0) + 1,
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

    def mark_task_canceled(self, task_id: int) -> dict:
        task = self.get_task_or_raise(task_id)
        validate_task_status_transition(task, "canceled")

        with self.connection_factory() as connection:
            return update_task_status_in_postgresql(
                connection,
                task_id=task_id,
                status="canceled",
                result={},
                error="",
            )

    def increment_task_retry_count(self, task_id: int) -> dict:
        self.ensure_tasks_table_ready()

        with self.connection_factory() as connection:
            return increment_task_retry_count_in_postgresql(connection, task_id)
