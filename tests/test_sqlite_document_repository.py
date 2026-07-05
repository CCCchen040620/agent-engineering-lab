import sqlite3
import pytest

from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    list_documents_from_db,
    insert_document_to_db,
    try_insert_document_to_db,
)


def test_list_documents_from_empty_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    documents = list_documents_from_db(connection)

    connection.close()

    assert documents == []


def test_insert_document_to_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    documents = list_documents_from_db(connection)

    connection.close()

    assert document["id"] == 1
    assert document["title"] == "员工手册"
    assert document["is_indexed"] == True
    assert len(documents) == 1


def test_insert_document_to_db_rejects_duplicate_title(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    with pytest.raises(sqlite3.IntegrityError):
        insert_document_to_db(
            connection,
            title="员工手册",
            file_type="md",
            chunk_count=12,
            is_indexed=True,
        )

    connection.close()


def test_try_insert_document_to_db_returns_none_for_duplicate_title(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    first_document = try_insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    second_document = try_insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    connection.close()

    assert first_document is not None
    assert second_document is None