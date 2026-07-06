from typing import Callable

from backend.services.embedding_search_service import search_chunks_by_embedding
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    list_chunks_with_documents,
)


def search_sqlite_chunks_by_embedding(
    database_path: str,
    query: str,
    top_k: int = 3,
    embedder: Callable[[str], list[float]] = embed_with_ollama,
) -> list[dict]:
    connection = create_connection(database_path)

    create_documents_table(connection)
    create_chunks_table(connection)

    chunks = list_chunks_with_documents(connection)

    connection.close()

    searchable_chunks = []

    for chunk in chunks:
        searchable_chunks.append(
            {
                "title": chunk["document_title"],
                "path": "sqlite://" + str(chunk["document_id"]),
                "text": chunk["text"],
            }
        )

    return search_chunks_by_embedding(
        query=query,
        chunks=searchable_chunks,
        top_k=top_k,
        embedder=embedder,
    )