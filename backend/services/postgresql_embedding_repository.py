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


def upsert_chunk_embedding_to_postgresql(
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
            ON CONFLICT (chunk_id) DO UPDATE
            SET embedding = EXCLUDED.embedding,
                model = EXCLUDED.model
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


def summarize_document_embedding_status_from_postgresql(connection) -> list[dict]:
    """统计每份 PostgreSQL 文档的 chunks 是否已经完成 embedding 索引。"""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                documents.id,
                documents.title,
                documents.chunk_count,
                COUNT(chunk_embeddings.id) AS embedding_count
            FROM documents
            LEFT JOIN chunks ON chunks.document_id = documents.id
            LEFT JOIN chunk_embeddings ON chunk_embeddings.chunk_id = chunks.id
            GROUP BY documents.id, documents.title, documents.chunk_count
            ORDER BY documents.id
            """
        )

        rows = cursor.fetchall()

    results = []

    for row in rows:
        chunk_count = row[2]
        embedding_count = row[3]

        results.append(
            {
                "document_id": row[0],
                "title": row[1],
                "chunk_count": chunk_count,
                "embedding_count": embedding_count,
                "is_embedding_complete": chunk_count == embedding_count,
            }
        )

    return results
