from backend.services.postgresql_vector_search_repository import (
    row_to_vector_search_result,
    search_chunks_by_vector_from_postgresql,
)


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.params = None
        self.rows = []

    def execute(self, sql: str, params=None):
        self.sql = sql
        self.params = params

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance


def test_row_to_vector_search_result():
    row = (
        1,
        10,
        2,
        "员工手册",
        "员工每天需要完成 8 小时工作。",
        0.2,
    )

    result = row_to_vector_search_result(row)

    assert result == {
        "chunk_id": 1,
        "document_id": 10,
        "document_title": "员工手册",
        "text": "员工每天需要完成 8 小时工作。",
        "distance": 0.2,
        "score": 0.8,
    }


def test_search_chunks_by_vector_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.rows = [
        (
            1,
            10,
            2,
            "员工手册",
            "员工每天需要完成 8 小时工作。",
            0.2,
        )
    ]

    results = search_chunks_by_vector_from_postgresql(
        connection,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=3,
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == 1
    assert results[0]["document_title"] == "员工手册"
    assert results[0]["score"] == 0.8

    assert "chunk_embeddings.embedding <=> %s::vector" in (
        connection.cursor_instance.sql
    )
    assert "ORDER BY distance ASC" in connection.cursor_instance.sql
    assert "LIMIT %s" in connection.cursor_instance.sql

    assert connection.cursor_instance.params == (
        "[0.1,0.2,0.3]",
        3,
    )