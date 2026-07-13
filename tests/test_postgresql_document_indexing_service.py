import pytest

from backend.services.postgresql_document_indexing_service import (
    PostgreSQLDocumentIndexingError,
    create_postgresql_document_with_chunks_and_embeddings,
)
from backend.services.postgresql_document_indexing_service import (
    create_postgresql_document_with_chunks_and_embeddings,
)


def test_create_postgresql_document_with_chunks_and_embeddings(monkeypatch):
    connection = object()

    inserted_chunks = []
    inserted_embeddings = []

    def fake_insert_document(
        connection,
        title,
        file_type,
        chunk_count,
        is_indexed,
    ):
        return {
            "id": 1,
            "title": title,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "is_indexed": is_indexed,
        }

    def fake_insert_chunk(connection, document_id, text, chunk_index):
        chunk = {
            "id": len(inserted_chunks) + 1,
            "document_id": document_id,
            "text": text,
            "chunk_index": chunk_index,
        }

        inserted_chunks.append(chunk)

        return chunk

    def fake_insert_embedding(connection, chunk_id, embedding, model):
        chunk_embedding = {
            "id": len(inserted_embeddings) + 1,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "model": model,
        }

        inserted_embeddings.append(chunk_embedding)

        return chunk_embedding

    def fake_embedder(text):
        return [1.0, 0.0, 0.0]

    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_document_to_postgresql",
        fake_insert_document,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_chunk_to_postgresql",
        fake_insert_chunk,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_chunk_embedding_to_postgresql",
        fake_insert_embedding,
    )

    result = create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title="PostgreSQL 入库测试文档",
        file_type="md",
        content="员工每天需要完成 8 小时工作。新员工需要完成安全培训。",
        embedder=fake_embedder,
        embedding_model="fake-model",
    )

    assert result["document"]["title"] == "PostgreSQL 入库测试文档"
    assert result["document"]["chunk_count"] == 2
    assert result["document"]["is_indexed"] is True

    assert len(result["chunks"]) == 2
    assert result["chunks"][0]["text"] == "员工每天需要完成 8 小时工作。"
    assert result["chunks"][0]["chunk_index"] == 0
    assert result["chunks"][1]["text"] == "新员工需要完成安全培训。"
    assert result["chunks"][1]["chunk_index"] == 1

    assert len(result["embeddings"]) == 2
    assert result["embeddings"][0]["chunk_id"] == 1
    assert result["embeddings"][0]["embedding"] == [1.0, 0.0, 0.0]
    assert result["embeddings"][0]["model"] == "fake-model"


def test_create_postgresql_document_returns_none_when_content_has_no_chunks(
    monkeypatch,
):
    connection = object()
    insert_called = False

    def fake_insert_document(
        connection,
        title,
        file_type,
        chunk_count,
        is_indexed,
    ):
        nonlocal insert_called
        insert_called = True

        return {
            "id": 1,
            "title": title,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "is_indexed": is_indexed,
        }

    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_document_to_postgresql",
        fake_insert_document,
    )

    result = create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title="空文档",
        file_type="md",
        content="   \n   ",
        embedder=lambda text: [1.0],
        embedding_model="fake-model",
    )

    assert result is None
    assert insert_called is False


def test_create_postgresql_document_raises_error_when_embedding_fails(
    monkeypatch,
):
    connection = object()
    insert_document_called = False
    insert_chunk_called = False
    insert_embedding_called = False

    def fake_insert_document(
        connection,
        title,
        file_type,
        chunk_count,
        is_indexed,
    ):
        nonlocal insert_document_called
        insert_document_called = True

        return {
            "id": 1,
            "title": title,
            "file_type": file_type,
            "chunk_count": chunk_count,
            "is_indexed": is_indexed,
        }

    def fake_insert_chunk(connection, document_id, text, chunk_index):
        nonlocal insert_chunk_called
        insert_chunk_called = True

        return {
            "id": 1,
            "document_id": document_id,
            "text": text,
            "chunk_index": chunk_index,
        }

    def fake_insert_embedding(connection, chunk_id, embedding, model):
        nonlocal insert_embedding_called
        insert_embedding_called = True

        return {
            "id": 1,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "model": model,
        }

    def failing_embedder(text):
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_document_to_postgresql",
        fake_insert_document,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_chunk_to_postgresql",
        fake_insert_chunk,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_document_indexing_service."
        "insert_chunk_embedding_to_postgresql",
        fake_insert_embedding,
    )

    with pytest.raises(PostgreSQLDocumentIndexingError) as error:
        create_postgresql_document_with_chunks_and_embeddings(
            connection,
            title="Embedding 失败文档",
            file_type="md",
            content="员工每天需要完成 8 小时工作。",
            embedder=failing_embedder,
            embedding_model="fake-model",
        )

    assert "PostgreSQL 文档索引失败" in str(error.value)
    assert insert_document_called is False
    assert insert_chunk_called is False
    assert insert_embedding_called is False