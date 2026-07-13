from typing import Callable

from backend.config import EMBEDDING_MODEL
from backend.services.document_indexing_service import split_text_into_chunks
from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_document_repository import (
    find_document_by_title_from_postgresql,
    insert_chunk_to_postgresql,
    insert_document_to_postgresql,
)
from backend.services.postgresql_embedding_repository import (
    insert_chunk_embedding_to_postgresql,
)


POSTGRESQL_INDEXING_ERROR_MESSAGE = (
    "PostgreSQL 文档索引失败：Embedding 模型不可用，请确认 Ollama 和 bge-m3 已启动。"
)


class PostgreSQLDocumentIndexingError(Exception):
    pass


def create_embeddings_for_chunks(
    chunks: list[str],
    embedder: Callable[[str], list[float]],
) -> list[list[float]]:
    embeddings = []

    for chunk in chunks:
        try:
            embeddings.append(embedder(chunk))
        except Exception as error:
            raise PostgreSQLDocumentIndexingError(
                POSTGRESQL_INDEXING_ERROR_MESSAGE
            ) from error

    return embeddings


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

    if find_document_by_title_from_postgresql(connection, title) is not None:
        return None

    embeddings = create_embeddings_for_chunks(chunks, embedder)

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

        chunk_embedding = insert_chunk_embedding_to_postgresql(
            connection,
            chunk_id=chunk["id"],
            embedding=embeddings[chunk_index],
            model=embedding_model,
        )

        inserted_chunks.append(chunk)
        inserted_embeddings.append(chunk_embedding)

    return {
        "document": document,
        "chunks": inserted_chunks,
        "embeddings": inserted_embeddings,
    }