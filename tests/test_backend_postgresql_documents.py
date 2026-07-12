from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.postgresql_documents import get_postgresql_database_url


client = TestClient(app)


class FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


def clear_dependency_overrides():
    app.dependency_overrides.clear()


def test_list_postgresql_documents_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_list_documents(connection):
        return [
            {
                "id": 1,
                "title": "PostgreSQL 测试文档",
                "file_type": "md",
                "chunk_count": 1,
                "is_indexed": True,
            }
        ]

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.list_documents_from_postgresql",
        fake_list_documents,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.get("/api/v1/postgresql/documents")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert len(data) == 1
    assert data[0]["title"] == "PostgreSQL 测试文档"


def test_list_postgresql_documents_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.get("/api/v1/postgresql/documents")

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]


def test_list_postgresql_document_chunks_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_list_chunks(connection, document_id: int):
        captured["document_id"] = document_id

        return [
            {
                "id": 1,
                "document_id": document_id,
                "text": "员工每天需要完成 8 小时工作。",
                "chunk_index": 0,
            }
        ]

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.list_chunks_by_document_from_postgresql",
        fake_list_chunks,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.get("/api/v1/postgresql/documents/2/chunks")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert captured["document_id"] == 2
    assert len(data) == 1
    assert data[0]["text"] == "员工每天需要完成 8 小时工作。"


def test_list_postgresql_document_chunks_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.get("/api/v1/postgresql/documents/2/chunks")

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]


def test_search_postgresql_chunks_by_vector_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_search_chunks(connection, query_embedding: list[float], top_k: int):
        captured["query_embedding"] = query_embedding
        captured["top_k"] = top_k

        return [
            {
                "chunk_id": 1,
                "document_id": 2,
                "document_title": "PostgreSQL RAG 存储测试文档",
                "text": "这是一条写入 PostgreSQL pgvector 的测试片段。",
                "distance": 0.0,
                "score": 1.0,
            }
        ]

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.search_chunks_by_vector_from_postgresql",
        fake_search_chunks,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post(
        "/api/v1/postgresql/search/vector",
        json={
            "embedding": [0.1, 0.2, 0.3],
            "top_k": 2,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert captured["query_embedding"] == [0.1, 0.2, 0.3]
    assert captured["top_k"] == 2
    assert len(data) == 1
    assert data[0]["chunk_id"] == 1
    assert data[0]["score"] == 1.0


def test_search_postgresql_chunks_by_vector_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.post(
        "/api/v1/postgresql/search/vector",
        json={
            "embedding": [0.1, 0.2, 0.3],
            "top_k": 2,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]