from typing import Callable

from backend.services.embedding_similarity_service import cosine_similarity
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
)
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
)


def list_chunks_with_embeddings(connection) -> list[dict]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            chunks.id,
            chunks.document_id,
            documents.title,
            chunks.text,
            chunk_embeddings.embedding_json
        FROM chunks
        JOIN documents ON chunks.document_id = documents.id
        JOIN chunk_embeddings ON chunk_embeddings.chunk_id = chunks.id
        """
    )

    rows = cursor.fetchall()

    results = []

    for row in rows:
        results.append(
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "document_title": row[2],
                "text": row[3],
                "embedding_json": row[4],
            }
        )

    return results


def search_sqlite_chunks_by_precomputed_embedding(
    database_path: str,
    query: str,
    top_k: int = 3,
    embedder: Callable[[str], list[float]] | None = None,
) -> list[dict]:
    if embedder is None:
        embedder = embed_with_ollama

    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    chunks = list_chunks_with_embeddings(connection)

    connection.close()

    query_embedding = embedder(query)

    results = []

    for chunk in chunks:
        import json

        chunk_embedding = json.loads(chunk["embedding_json"])
        score = cosine_similarity(query_embedding, chunk_embedding)

        results.append(
            {
                "title": chunk["document_title"],
                "path": "sqlite://" + str(chunk["document_id"]),
                "text": chunk["text"],
                "score": score,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:top_k]