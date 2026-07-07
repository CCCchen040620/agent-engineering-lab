from backend.services.agent_tools import list_documents_tool
from backend.services.sqlite_document_repository import (
    create_connection,
    create_documents_table,
    insert_document_to_db,
)


def test_list_documents_tool(tmp_path):
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

    connection.close()

    result = list_documents_tool(str(database_path))

    assert result["count"] == 1
    assert result["documents"][0]["title"] == "员工手册"
    assert result["documents"][0]["is_indexed"] == True