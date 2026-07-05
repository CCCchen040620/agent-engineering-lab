from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    list_documents_from_db,
    insert_document_to_db,
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