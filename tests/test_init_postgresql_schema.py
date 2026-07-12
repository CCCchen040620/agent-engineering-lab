import pytest

from week10 import init_postgresql_schema
from week10.init_postgresql_schema import initialize_schema_from_database_url


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def test_initialize_schema_from_database_url_connects_to_postgresql(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["connection"] = connection

        return {
            "vector_extension_ready": True,
            "documents_table_ready": True,
            "chunks_table_ready": True,
            "chunk_embeddings_table_ready": True,
        }

    monkeypatch.setattr(init_postgresql_schema.psycopg, "connect", fake_connect)
    monkeypatch.setattr(
        init_postgresql_schema,
        "initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )

    result = initialize_schema_from_database_url(
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert isinstance(captured["connection"], FakeConnection)
    assert result["documents_table_ready"] is True
    assert result["chunks_table_ready"] is True
    assert result["chunk_embeddings_table_ready"] is True


def test_initialize_schema_from_database_url_rejects_sqlite_url():
    with pytest.raises(ValueError) as error:
        initialize_schema_from_database_url("sqlite:///data/app.db")

    assert "PostgreSQL URL" in str(error.value)


def test_main_prints_schema_initialization_result(monkeypatch, capsys):
    monkeypatch.setattr(
        init_postgresql_schema,
        "DATABASE_URL",
        "postgresql://agent_user:agent_password@localhost:5432/agent_db",
    )

    def fake_initialize_schema_from_database_url(database_url: str):
        return {
            "vector_extension_ready": True,
            "documents_table_ready": True,
            "chunks_table_ready": True,
            "chunk_embeddings_table_ready": True,
        }

    monkeypatch.setattr(
        init_postgresql_schema,
        "initialize_schema_from_database_url",
        fake_initialize_schema_from_database_url,
    )

    init_postgresql_schema.main()

    output = capsys.readouterr().out

    assert "PostgreSQL knowledge schema initialized." in output
    assert "documents_table_ready" in output