from week06.sqlite_intro import (
    create_connection,
    create_documents_table,
    insert_document,
    list_documents,
    find_document_by_title,
)


def test_sqlite_document_flow(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    document = insert_document(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    documents = list_documents(connection)

    connection.close()

    assert len(documents) == 1
    assert documents[0]["title"] == "员工手册"
    assert documents[0]["is_indexed"] == True
    assert document["title"] == "员工手册"


def test_sqlite_insert_document_prevents_duplicate_title(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    first_document = insert_document(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    second_document = insert_document(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    documents = list_documents(connection)

    connection.close()

    assert first_document is not None
    assert second_document is None
    assert len(documents) == 1


def test_sqlite_find_document_by_title(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    insert_document(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    document = find_document_by_title(connection, "员工手册")

    connection.close()

    assert document is not None
    assert document["title"] == "员工手册"