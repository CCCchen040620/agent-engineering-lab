from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


class FakeCursor:
    def __init__(self):
        self.executed_sql = []

    def execute(self, sql: str):
        self.executed_sql.append(sql)

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


def test_initialize_postgresql_knowledge_schema_creates_core_tables():
    connection = FakeConnection()

    result = initialize_postgresql_knowledge_schema(connection)

    sql_text = "\n".join(connection.cursor_instance.executed_sql)

    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql_text
    assert "CREATE TABLE IF NOT EXISTS documents" in sql_text
    assert "source TEXT NOT NULL DEFAULT 'production'" in sql_text
    assert "ADD COLUMN IF NOT EXISTS source" in sql_text
    assert "CREATE TABLE IF NOT EXISTS chunks" in sql_text
    assert "CREATE TABLE IF NOT EXISTS chunk_embeddings" in sql_text
    assert "vector(1024)" in sql_text
    assert connection.committed is True

    assert result == {
        "vector_extension_ready": True,
        "documents_table_ready": True,
        "documents_source_column_ready": True,
        "chunks_table_ready": True,
        "chunk_embeddings_table_ready": True,
    }
