from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    list_documents_from_db,
)


def test_list_documents_from_empty_db(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    documents = list_documents_from_db(connection)

    connection.close()

    assert documents == []