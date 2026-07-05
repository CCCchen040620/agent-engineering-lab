from week06.sqlite_intro import (
    create_connection,
    create_documents_table,
    insert_document,
    list_documents,
)


def test_sqlite_document_flow(tmp_path):
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

    documents = list_documents(connection)

    connection.close()

    assert len(documents) == 1
    assert documents[0]["title"] == "员工手册"
    assert documents[0]["is_indexed"] == True