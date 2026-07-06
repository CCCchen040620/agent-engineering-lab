from backend.services.document_indexing_service import (
    create_document_with_chunks_and_embeddings,
)
from backend.services.sqlite_document_repository import create_connection
from backend.services.sqlite_precomputed_embedding_search_service import (
    list_chunks_with_embeddings,
    search_sqlite_chunks_by_precomputed_embedding,
)


def test_list_chunks_with_embeddings(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    def fake_embedder(text: str) -> list[float]:
        return [1.0, 0.0]

    create_document_with_chunks_and_embeddings(
        connection,
        title="远程办公制度",
        file_type="md",
        content="员工可以远程办公。",
        embedder=fake_embedder,
    )

    chunks = list_chunks_with_embeddings(connection)

    connection.close()

    assert len(chunks) == 1
    assert chunks[0]["document_title"] == "远程办公制度"
    assert chunks[0]["text"] == "员工可以远程办公。"


def test_search_sqlite_chunks_by_precomputed_embedding(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    embeddings = {
        "员工可以远程办公。": [0.9, 0.1],
        "员工报销需要提交发票。": [0.0, 1.0],
    }

    def chunk_embedder(text: str) -> list[float]:
        return embeddings[text]

    create_document_with_chunks_and_embeddings(
        connection,
        title="远程办公制度",
        file_type="md",
        content="员工可以远程办公。员工报销需要提交发票。",
        embedder=chunk_embedder,
    )

    connection.close()

    def query_embedder(text: str) -> list[float]:
        return [1.0, 0.0]

    results = search_sqlite_chunks_by_precomputed_embedding(
        database_path=str(database_path),
        query="远程办公怎么申请？",
        top_k=1,
        embedder=query_embedder,
    )

    assert len(results) == 1
    assert results[0]["title"] == "远程办公制度"
    assert results[0]["text"] == "员工可以远程办公。"
    assert results[0]["score"] > 0.9