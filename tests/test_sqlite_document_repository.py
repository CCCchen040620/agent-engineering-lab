import sqlite3
import pytest

from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    list_documents_from_db,
    insert_document_to_db,
    try_insert_document_to_db,
    list_documents_from_db_filtered,
    find_document_from_db_by_id,
    delete_document_from_db_by_id,
    create_chunks_table,
    insert_chunk_to_db,
    list_chunks_by_document_id,
    search_chunks_by_text,
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


def test_list_documents_from_db_filtered_by_indexed_only(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    insert_document_to_db(connection, "员工手册", "md", 12, True)
    insert_document_to_db(connection, "报销制度", "pdf", 8, False)

    documents = list_documents_from_db_filtered(connection, indexed_only=True)

    connection.close()

    assert len(documents) == 1
    assert documents[0]["title"] == "员工手册"


def test_list_documents_from_db_filtered_by_file_type(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    insert_document_to_db(connection, "员工手册", "md", 12, True)
    insert_document_to_db(connection, "报销制度", "pdf", 8, False)

    documents = list_documents_from_db_filtered(connection, file_type="pdf")

    connection.close()

    assert len(documents) == 1
    assert documents[0]["title"] == "报销制度"


def test_find_document_from_db_by_id(tmp_path):
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

    found_document = find_document_from_db_by_id(connection, document["id"])

    connection.close()

    assert found_document is not None
    assert found_document["title"] == "员工手册"


def test_find_document_from_db_by_id_returns_none_when_not_found(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    found_document = find_document_from_db_by_id(connection, 999)

    connection.close()

    assert found_document is None


def test_delete_document_from_db_by_id(tmp_path):
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

    deleted = delete_document_from_db_by_id(connection, document["id"])
    documents = list_documents_from_db(connection)

    connection.close()

    assert deleted == True
    assert documents == []


def test_delete_document_from_db_by_id_returns_false_when_not_found(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    deleted = delete_document_from_db_by_id(connection, 999)

    connection.close()

    assert deleted == False


def test_create_chunks_table(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'chunks'
        """
    )

    row = cursor.fetchone()

    connection.close()

    assert row is not None
    assert row[0] == "chunks"


def test_insert_chunk_to_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    chunk = insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    connection.close()

    assert chunk["id"] == 1
    assert chunk["document_id"] == document["id"]
    assert chunk["text"] == "新员工入职后需要在 30 天内完成安全培训。"


def test_list_chunks_by_document_id(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=2,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工每天需要完成 8 小时工作。",
    )
    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    chunks = list_chunks_by_document_id(connection, document["id"])

    connection.close()

    assert len(chunks) == 2
    assert chunks[0]["document_id"] == document["id"]
    assert chunks[1]["text"] == "新员工入职后需要在 30 天内完成安全培训。"


def test_search_chunks_by_text(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=2,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工每天需要完成 8 小时工作。",
    )
    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    chunks = search_chunks_by_text(connection, "安全培训")

    connection.close()

    assert len(chunks) == 1
    assert chunks[0]["text"] == "新员工入职后需要在 30 天内完成安全培训。"