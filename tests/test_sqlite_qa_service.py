from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_qa_service import build_sqlite_chat_response


def test_build_sqlite_chat_response_with_citation(tmp_path):
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

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    connection.close()

    response = build_sqlite_chat_response(
        "新员工什么时候完成安全培训？",
        database_path=str(database_path),
    )

    assert response.keyword == "安全培训"
    assert "新员工入职后需要在 30 天内完成安全培训。" in response.answer
    assert len(response.citations) == 1
    assert response.citations[0].title == "员工手册"


def test_build_sqlite_chat_response_refuses_unknown_question(tmp_path):
    database_path = tmp_path / "test.db"

    response = build_sqlite_chat_response(
        "公司有没有股票期权？",
        database_path=str(database_path),
    )

    assert "暂时无法回答" in response.answer
    assert response.citations == []