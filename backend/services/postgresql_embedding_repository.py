def embedding_to_postgresql_vector(embedding: list[float]) -> str:
    values = []

    for value in embedding:
        values.append(str(value))

    return "[" + ",".join(values) + "]"


def postgresql_vector_to_embedding(vector_value: str) -> list[float]:
    text = vector_value.strip()

    if text == "[]":
        return []

    text = text.removeprefix("[")
    text = text.removesuffix("]")

    values = text.split(",")

    embedding = []

    for value in values:
        embedding.append(float(value))

    return embedding


def row_to_chunk_embedding(row) -> dict:
    return {
        "id": row[0],
        "chunk_id": row[1],
        "embedding": postgresql_vector_to_embedding(row[2]),
        "model": row[3],
    }


def insert_chunk_embedding_to_postgresql(
    connection,
    chunk_id: int,
    embedding: list[float],
    model: str,
) -> dict:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO chunk_embeddings (chunk_id, embedding, model)
            VALUES (%s, %s::vector, %s)
            RETURNING id, chunk_id, embedding::text, model
            """,
            (
                chunk_id,
                embedding_to_postgresql_vector(embedding),
                model,
            ),
        )

        row = cursor.fetchone()

    connection.commit()

    return row_to_chunk_embedding(row)


def find_chunk_embedding_by_chunk_id_from_postgresql(
    connection,
    chunk_id: int,
) -> dict | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, chunk_id, embedding::text, model
            FROM chunk_embeddings
            WHERE chunk_id = %s
            """,
            (chunk_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return None

    return row_to_chunk_embedding(row)