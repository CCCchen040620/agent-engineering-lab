import json


def create_chunk_embeddings_table(connection) -> None:
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            id INTEGER PRIMARY KEY,
            chunk_id INTEGER NOT NULL UNIQUE,
            embedding_json TEXT NOT NULL,
            FOREIGN KEY (chunk_id) REFERENCES chunks (id)
        )
        """
    )

    connection.commit()


def row_to_chunk_embedding(row) -> dict:
    return {
        "id": row[0],
        "chunk_id": row[1],
        "embedding": json.loads(row[2]),
    }


def insert_chunk_embedding_to_db(
    connection,
    chunk_id: int,
    embedding: list[float],
) -> dict:
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chunk_embeddings (chunk_id, embedding_json)
        VALUES (?, ?)
        """,
        (chunk_id, json.dumps(embedding)),
    )

    connection.commit()

    embedding_id = cursor.lastrowid

    cursor.execute(
        """
        SELECT id, chunk_id, embedding_json
        FROM chunk_embeddings
        WHERE id = ?
        """,
        (embedding_id,),
    )

    row = cursor.fetchone()

    return row_to_chunk_embedding(row)


def find_chunk_embedding_by_chunk_id(connection, chunk_id: int) -> dict | None:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, chunk_id, embedding_json
        FROM chunk_embeddings
        WHERE chunk_id = ?
        """,
        (chunk_id,),
    )

    row = cursor.fetchone()

    if row is None:
        return None

    return row_to_chunk_embedding(row)


def list_chunk_embeddings_from_db(connection) -> list[dict]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, chunk_id, embedding_json
        FROM chunk_embeddings
        """
    )

    rows = cursor.fetchall()

    embeddings = []

    for row in rows:
        embeddings.append(row_to_chunk_embedding(row))

    return embeddings