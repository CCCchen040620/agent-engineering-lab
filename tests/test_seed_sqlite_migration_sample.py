from backend.services.sqlite_document_repository import (
    create_connection,
    list_chunks_by_document_id,
    list_documents_from_db,
)
from week10.seed_sqlite_migration_sample import (
    SQLITE_MIGRATION_SAMPLE_CHUNKS,
    SQLITE_MIGRATION_SAMPLE_TITLE,
    seed_sqlite_migration_sample,
)


def test_seed_sqlite_migration_sample_creates_document_and_chunks(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    result = seed_sqlite_migration_sample(connection)

    documents = list_documents_from_db(connection)
    chunks = list_chunks_by_document_id(
        connection,
        document_id=result["document"]["id"],
    )

    connection.close()

    assert result["created"] is True
    assert result["document"]["title"] == SQLITE_MIGRATION_SAMPLE_TITLE
    assert result["inserted_chunks"] == len(SQLITE_MIGRATION_SAMPLE_CHUNKS)
    assert result["chunk_count"] == len(SQLITE_MIGRATION_SAMPLE_CHUNKS)

    assert len(documents) == 1
    assert documents[0]["title"] == SQLITE_MIGRATION_SAMPLE_TITLE
    assert documents[0]["chunk_count"] == len(SQLITE_MIGRATION_SAMPLE_CHUNKS)
    assert documents[0]["is_indexed"] is True

    assert len(chunks) == len(SQLITE_MIGRATION_SAMPLE_CHUNKS)
    assert chunks[0]["text"] == SQLITE_MIGRATION_SAMPLE_CHUNKS[0]
    assert chunks[1]["text"] == SQLITE_MIGRATION_SAMPLE_CHUNKS[1]


def test_seed_sqlite_migration_sample_is_idempotent(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    first_result = seed_sqlite_migration_sample(connection)
    second_result = seed_sqlite_migration_sample(connection)

    documents = list_documents_from_db(connection)
    chunks = list_chunks_by_document_id(
        connection,
        document_id=first_result["document"]["id"],
    )

    connection.close()

    assert first_result["created"] is True
    assert second_result["created"] is False
    assert second_result["inserted_chunks"] == 0
    assert second_result["chunk_count"] == len(SQLITE_MIGRATION_SAMPLE_CHUNKS)

    assert len(documents) == 1
    assert len(chunks) == len(SQLITE_MIGRATION_SAMPLE_CHUNKS)
