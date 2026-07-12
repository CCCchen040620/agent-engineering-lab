from backend.services.postgresql_embedding_repository import (
    embedding_to_postgresql_vector,
    find_chunk_embedding_by_chunk_id_from_postgresql,
    insert_chunk_embedding_to_postgresql,
    postgresql_vector_to_embedding,
    row_to_chunk_embedding,
)


class FakeCursor:
    def __init__(self):
        self.sql = ""
        self.params = None
        self.row = None

    def execute(self, sql: str, params=None):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True


def test_embedding_to_postgresql_vector():
    result = embedding_to_postgresql_vector([0.1, 0.2, -0.3])

    assert result == "[0.1,0.2,-0.3]"


def test_postgresql_vector_to_embedding():
    result = postgresql_vector_to_embedding("[0.1,0.2,-0.3]")

    assert result == [0.1, 0.2, -0.3]


def test_row_to_chunk_embedding():
    row = (1, 10, "[0.1,0.2,-0.3]", "bge-m3:latest")

    result = row_to_chunk_embedding(row)

    assert result == {
        "id": 1,
        "chunk_id": 10,
        "embedding": [0.1, 0.2, -0.3],
        "model": "bge-m3:latest",
    }


def test_insert_chunk_embedding_to_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (1, 10, "[0.1,0.2,-0.3]", "bge-m3:latest")

    result = insert_chunk_embedding_to_postgresql(
        connection,
        chunk_id=10,
        embedding=[0.1, 0.2, -0.3],
        model="bge-m3:latest",
    )

    assert result["id"] == 1
    assert result["chunk_id"] == 10
    assert result["embedding"] == [0.1, 0.2, -0.3]
    assert result["model"] == "bge-m3:latest"
    assert connection.cursor_instance.params == (
        10,
        "[0.1,0.2,-0.3]",
        "bge-m3:latest",
    )
    assert "INSERT INTO chunk_embeddings" in connection.cursor_instance.sql
    assert "%s::vector" in connection.cursor_instance.sql
    assert connection.committed is True


def test_find_chunk_embedding_by_chunk_id_from_postgresql():
    connection = FakeConnection()
    connection.cursor_instance.row = (1, 10, "[0.1,0.2,-0.3]", "bge-m3:latest")

    result = find_chunk_embedding_by_chunk_id_from_postgresql(
        connection,
        chunk_id=10,
    )

    assert result["chunk_id"] == 10
    assert result["embedding"] == [0.1, 0.2, -0.3]
    assert connection.cursor_instance.params == (10,)
    assert "WHERE chunk_id = %s" in connection.cursor_instance.sql


def test_find_chunk_embedding_by_chunk_id_returns_none_when_missing():
    connection = FakeConnection()
    connection.cursor_instance.row = None

    result = find_chunk_embedding_by_chunk_id_from_postgresql(
        connection,
        chunk_id=999,
    )

    assert result is None