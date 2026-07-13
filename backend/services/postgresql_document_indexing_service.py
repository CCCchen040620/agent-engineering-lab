from typing import Callable

from backend.config import EMBEDDING_MODEL
from backend.services.document_indexing_service import split_text_into_chunks
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_document_repository import (
    insert_chunk_to_postgresql,
    insert_document_to_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    insert_chunk_embedding_to_postgresql,
)


def create_postgresql_document_with_chunks_and_embeddings(
    connection,
    title: str,
    file_type: str,
    content: str,
    embedder: Callable[[str], list[float]] | None = None,
    embedding_model: str = EMBEDDING_MODEL,
) -> dict | None:
    if embedder is None:
        embedder = embed_with_ollama

    chunks = split_text_into_chunks(content)

    if chunks == []:
        return None

    document = insert_document_to_postgresql(
        connection,
        title=title,
        file_type=file_type,
        chunk_count=len(chunks),
        is_indexed=True,
    )

    inserted_chunks = []
    inserted_embeddings = []

    for chunk_index, chunk_text in enumerate(chunks):
        chunk = insert_chunk_to_postgresql(
            connection,
            document_id=document["id"],
            text=chunk_text,
            chunk_index=chunk_index,
        )

        embedding = embedder(chunk_text)

        chunk_embedding = insert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=chunk["id"],
            embedding=embedding,
            model=embedding_model,
        )

        inserted_chunks.append(chunk)
        inserted_embeddings.append(chunk_embedding)

    return {
        "document": document,
        "chunks": inserted_chunks,
        "embeddings": inserted_embeddings,
    }