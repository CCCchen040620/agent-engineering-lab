from typing import Callable

from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
    insert_chunk_embedding_to_db,
)
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_documents_table,
    find_document_from_db_by_title,
    insert_chunk_to_db,
    try_insert_document_to_db,
)


class DocumentIndexingError(Exception):
    pass


INDEXING_ERROR_MESSAGE = (
    "文档索引失败：本地 Embedding 模型不可用，请确认 Ollama 和 bge-m3 已启动。"
)


def split_long_text(text: str, max_chunk_size: int) -> list[str]:
    chunks = []

    for start in range(0, len(text), max_chunk_size):
        chunks.append(text[start : start + max_chunk_size])

    return chunks


def split_text_into_chunks(
    content: str,
    max_chunk_size: int = 120,
) -> list[str]:
    normalized_content = content.replace("\n", "。")

    for separator in ["！", "？", "!", "?"]:
        normalized_content = normalized_content.replace(separator, "。")

    raw_chunks = normalized_content.split("。")

    chunks = []

    for raw_chunk in raw_chunks:
        chunk = raw_chunk.strip()

        if chunk == "":
            continue

        chunk = chunk + "。"

        if len(chunk) <= max_chunk_size:
            chunks.append(chunk)
        else:
            chunks.extend(split_long_text(chunk, max_chunk_size))

    return chunks


def create_document_with_chunks(
    connection,
    title: str,
    file_type: str,
    content: str,
) -> dict | None:
    create_documents_table(connection)
    create_chunks_table(connection)

    chunks = split_text_into_chunks(content)
    
    if chunks == []:
       return None

    document = try_insert_document_to_db(
        connection,
        title=title,
        file_type=file_type,
        chunk_count=len(chunks),
        is_indexed=len(chunks) > 0,
    )

    if document is None:
        return None

    for chunk in chunks:
        insert_chunk_to_db(
            connection,
            document_id=document["id"],
            text=chunk,
        )

    return document


def create_document_with_chunks_and_embeddings(
    connection,
    title: str,
    file_type: str,
    content: str,
    embedder: Callable[[str], list[float]] | None = None,
) -> dict | None:
    if embedder is None:
        embedder = embed_with_ollama

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    chunks = split_text_into_chunks(content)

    if chunks == []:
        return None

    if find_document_from_db_by_title(connection, title) is not None:
        return None

    embeddings = []

    for chunk_text in chunks:
        try:
            embeddings.append(embedder(chunk_text))
        except Exception as error:
            raise DocumentIndexingError(INDEXING_ERROR_MESSAGE) from error

    document = try_insert_document_to_db(
        connection,
        title=title,
        file_type=file_type,
        chunk_count=len(chunks),
        is_indexed=True,
    )

    if document is None:
        return None

    for chunk_text, embedding in zip(chunks, embeddings):
        chunk = insert_chunk_to_db(
            connection,
            document_id=document["id"],
            text=chunk_text,
        )

        insert_chunk_embedding_to_db(
            connection,
            chunk_id=chunk["id"],
            embedding=embedding,
        )

    return document
