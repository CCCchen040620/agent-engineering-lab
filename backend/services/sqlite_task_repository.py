import json


def create_tasks_table(connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            error TEXT NOT NULL
        )
        """
    )
    connection.commit()


def row_to_task(row) -> dict:
    return {
        "id": row[0],
        "type": row[1],
        "status": row[2],
        "payload": json.loads(row[3]),
        "result": json.loads(row[4]),
        "error": row[5],
    }


def create_task(connection, task_type: str, payload: dict) -> dict:
    cursor = connection.execute(
        """
        INSERT INTO tasks (type, status, payload_json, result_json, error)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            task_type,
            "pending",
            json.dumps(payload, ensure_ascii=False),
            json.dumps({}, ensure_ascii=False),
            "",
        ),
    )
    connection.commit()

    return find_task_by_id(connection, cursor.lastrowid)


def list_tasks(connection) -> list[dict]:
    cursor = connection.execute(
        """
        SELECT id, type, status, payload_json, result_json, error
        FROM tasks
        ORDER BY id
        """
    )

    return [row_to_task(row) for row in cursor.fetchall()]


def find_task_by_id(connection, task_id: int) -> dict | None:
    cursor = connection.execute(
        """
        SELECT id, type, status, payload_json, result_json, error
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return row_to_task(row)