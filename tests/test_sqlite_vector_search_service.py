from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_vector_search_service import search_sqlite_chunks_by_similarity


def test_search_sqlite_chunks_by_similarity(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="报销制度",
        file_type="md",
        chunk_count=2,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工报销需要提交发票。",
    )
    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工请假需要提前申请。",
    )

    connection.close()

    results = search_sqlite_chunks_by_similarity(
        database_path=str(database_path),
        query="报销 发票",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["text"] == "员工报销需要提交发票。"
    assert results[0]["score"] > 0