from backend.services.agent_tools import (
    list_documents_tool,
    read_document_chunks_tool,
)
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
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


def test_read_document_chunks_tool(tmp_path):
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
        text="新员工需要完成安全培训。",
    )

    connection.close()

    result = read_document_chunks_tool(
        document_id=document["id"],
        database_path=str(database_path),
    )

    assert result["found"] == True
    assert result["document"]["title"] == "员工手册"
    assert len(result["chunks"]) == 2
    assert result["chunks"][0]["text"] == "员工每天需要完成 8 小时工作。"


def test_read_document_chunks_tool_returns_not_found(tmp_path):
    database_path = tmp_path / "test.db"

    result = read_document_chunks_tool(
        document_id=999,
        database_path=str(database_path),
    )

    assert result["found"] == False
    assert result["document"] is None
    assert result["chunks"] == []