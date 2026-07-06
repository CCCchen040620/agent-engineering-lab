from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_embedding_search_service import (
    search_sqlite_chunks_by_embedding,
)


def test_search_sqlite_chunks_by_embedding(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=2,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )
    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工报销需要提交发票。",
    )

    connection.close()

    embeddings = {
        "远程办公怎么申请？": [1.0, 0.0],
        "员工可以远程办公。": [0.9, 0.1],
        "员工报销需要提交发票。": [0.0, 1.0],
    }

    def fake_embedder(text: str) -> list[float]:
        return embeddings[text]

    results = search_sqlite_chunks_by_embedding(
        database_path=str(database_path),
        query="远程办公怎么申请？",
        top_k=1,
        embedder=fake_embedder,
    )

    assert len(results) == 1
    assert results[0]["title"] == "远程办公制度"
    assert results[0]["text"] == "员工可以远程办公。"
    assert results[0]["score"] > 0.9