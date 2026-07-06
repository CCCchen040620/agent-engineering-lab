from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    list_chunks_with_documents,
)
from week07.simple_vector_search import search_chunks_by_similarity


def search_sqlite_chunks_by_similarity(
    database_path: str,
    query: str,
    top_k: int = 3,
    min_score: float = 0.0,
) -> list[dict]:
    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    chunks = list_chunks_with_documents(connection)

    connection.close()

    similarity_chunks = []

    for chunk in chunks:
        similarity_chunks.append(
            {
                "title": chunk["document_title"],
                "path": "sqlite://" + str(chunk["document_id"]),
                "text": chunk["text"],
            }
        )

    return search_chunks_by_similarity(
        query,
        similarity_chunks,
        top_k=top_k,
        min_score=min_score,
    )