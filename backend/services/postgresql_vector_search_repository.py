from backend.services.postgresql_embedding_repository import (
    embedding_to_postgresql_vector,
)


def row_to_vector_search_result(row) -> dict:
    distance = float(row[5])

    return {
        "chunk_id": row[0],
        "document_id": row[1],
        "document_title": row[3],
        "text": row[4],
        "distance": distance,
        "score": 1 - distance,
    }


def search_chunks_by_vector_from_postgresql(
    connection,
    query_embedding: list[float],
    top_k: int = 3,
) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                chunks.id AS chunk_id,
                chunks.document_id,
                chunk_embeddings.id AS embedding_id,
                documents.title AS document_title,
                chunks.text,
                chunk_embeddings.embedding <=> %s::vector AS distance
            FROM chunk_embeddings
            JOIN chunks ON chunks.id = chunk_embeddings.chunk_id
            JOIN documents ON documents.id = chunks.document_id
            ORDER BY distance ASC
            LIMIT %s
            """,
            (
                embedding_to_postgresql_vector(query_embedding),
                top_k,
            ),
        )

        rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append(row_to_vector_search_result(row))

    return results