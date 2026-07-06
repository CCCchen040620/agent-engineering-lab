def create_feedback_table(connection) -> None:
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            rating TEXT NOT NULL
        )
        """
    )

    connection.commit()


def row_to_feedback(row) -> dict:
    return {
        "id": row[0],
        "question": row[1],
        "answer": row[2],
        "rating": row[3],
    }


def insert_feedback_to_db(
    connection,
    question: str,
    answer: str,
    rating: str,
) -> dict:
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO feedback (question, answer, rating)
        VALUES (?, ?, ?)
        """,
        (question, answer, rating),
    )

    connection.commit()

    feedback_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT id, question, answer, rating
        FROM feedback
        WHERE id = ?
        """,
        (feedback_id,),
    )

    row = cursor.fetchone()

    return row_to_feedback(row)


def list_feedback_from_db(connection) -> list[dict]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, question, answer, rating
        FROM feedback
        """
    )

    rows = cursor.fetchall()

    feedback_items = []

    for row in rows:
        feedback_items.append(row_to_feedback(row))

    return feedback_items