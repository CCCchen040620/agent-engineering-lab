from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_embedding_repository import (
    create_chunk_embeddings_table,
    find_chunk_embedding_by_chunk_id,
)
from week08.backfill_chunk_embeddings import backfill_chunk_embeddings


def test_backfill_chunk_embeddings(monkeypatch, tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )
    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )

    connection.close()

    def fake_embed_with_ollama(text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(
        "week08.backfill_chunk_embeddings.embed_with_ollama",
        fake_embed_with_ollama,
    )

    result = backfill_chunk_embeddings(str(database_path))

    connection = create_connection(str(database_path))
    embedding = find_chunk_embedding_by_chunk_id(connection, chunk["id"])
    connection.close()

    assert result == {
        "total_chunks": 1,
        "created": 1,
        "skipped": 0,
    }
    assert embedding["embedding"] == [0.1, 0.2, 0.3]


def test_backfill_chunk_embeddings_skips_existing_embeddings(monkeypatch, tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_chunk_embeddings_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )
    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )

    connection.close()

    def fake_embed_with_ollama(text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(
        "week08.backfill_chunk_embeddings.embed_with_ollama",
        fake_embed_with_ollama,
    )

    first_result = backfill_chunk_embeddings(str(database_path))
    second_result = backfill_chunk_embeddings(str(database_path))

    assert first_result["created"] == 1
    assert second_result["created"] == 0
    assert second_result["skipped"] == 1