from fastapi.testclient import TestClient
from backend.main import app
from backend.routers.postgresql_documents import get_postgresql_database_url
from backend.services.postgresql_document_indexing_service import (
    PostgreSQLDocumentIndexingError,
)


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


def test_list_postgresql_embedding_status_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_summarize_embedding_status(connection):
        return [
            {
                "document_id": 1,
                "title": "PostgreSQL 测试文档",
                "chunk_count": 2,
                "embedding_count": 2,
                "is_embedding_complete": True,
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
        "backend.routers.postgresql_documents."
        "summarize_document_embedding_status_from_postgresql",
        fake_summarize_embedding_status,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.get("/api/v1/postgresql/documents/embedding-status")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert data == [
        {
            "document_id": 1,
            "title": "PostgreSQL 测试文档",
            "chunk_count": 2,
            "embedding_count": 2,
            "is_embedding_complete": True,
        }
    ]


def test_list_postgresql_embedding_status_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.get("/api/v1/postgresql/documents/embedding-status")

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]


def test_backfill_postgresql_embeddings_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_backfill_embeddings(connection):
        captured["backfilled"] = True

        return {
            "total_chunks": 3,
            "updated": 1,
            "skipped": 2,
            "model": "bge-m3:latest",
        }

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents."
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_embeddings,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post("/api/v1/postgresql/embeddings/backfill")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert captured["backfilled"] is True
    assert data == {
        "total_chunks": 3,
        "updated": 1,
        "skipped": 2,
        "model": "bge-m3:latest",
    }


def test_backfill_postgresql_embeddings_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.post("/api/v1/postgresql/embeddings/backfill")

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]


def test_backfill_postgresql_embeddings_returns_503_when_backfill_fails(
    monkeypatch,
):
    def fake_connect(database_url: str):
        return FakeConnection()

    def fake_initialize_schema(connection):
        pass

    def fake_backfill_embeddings(connection):
        raise RuntimeError("Ollama embedding failed")

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents."
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_embeddings,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post("/api/v1/postgresql/embeddings/backfill")

    clear_dependency_overrides()

    assert response.status_code == 503
    assert "PostgreSQL embedding 回填失败" in response.json()["detail"]


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


def test_search_postgresql_chunks_by_question_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_search_by_question(
        connection,
        question: str,
        top_k: int,
        min_score: float,
    ):
        captured["question"] = question
        captured["top_k"] = top_k
        captured["min_score"] = min_score

        return {
            "question": question,
            "embedding_size": 1024,
            "results": [
                {
                    "chunk_id": 1,
                    "document_id": 3,
                    "document_title": "员工手册",
                    "text": "员工每天需要完成 8 小时工作。",
                    "distance": 0.0,
                    "score": 1.0,
                }
            ],
        }

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.search_postgresql_chunks_by_question",
        fake_search_by_question,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post(
        "/api/v1/postgresql/search/question",
        json={
            "question": "员工每天需要工作多久？",
            "top_k": 2,
            "min_score": 0.6,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert captured["question"] == "员工每天需要工作多久？"
    assert captured["top_k"] == 2
    assert captured["min_score"] == 0.6

    assert data["question"] == "员工每天需要工作多久？"
    assert data["embedding_size"] == 1024
    assert len(data["results"]) == 1
    assert data["results"][0]["document_title"] == "员工手册"


def test_search_postgresql_chunks_by_question_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.post(
        "/api/v1/postgresql/search/question",
        json={
            "question": "员工每天需要工作多久？",
            "top_k": 2,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]


def test_create_postgresql_document_with_content_endpoint(monkeypatch):
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return FakeConnection()

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_create_document(
        connection,
        title: str,
        file_type: str,
        content: str,
    ):
        captured["title"] = title
        captured["file_type"] = file_type
        captured["content"] = content

        return {
            "document": {
                "id": 1,
                "title": title,
                "file_type": file_type,
                "chunk_count": 2,
                "is_indexed": True,
            },
            "chunks": [
                {
                    "id": 1,
                    "document_id": 1,
                    "text": "员工每周可以申请一天远程办公。",
                    "chunk_index": 0,
                },
                {
                    "id": 2,
                    "document_id": 1,
                    "text": "远程办公需要提前提交申请。",
                    "chunk_index": 1,
                },
            ],
            "embeddings": [
                {
                    "id": 1,
                    "chunk_id": 1,
                    "embedding": [1.0, 0.0, 0.0],
                    "model": "fake-model",
                },
                {
                    "id": 2,
                    "chunk_id": 2,
                    "embedding": [0.0, 1.0, 0.0],
                    "model": "fake-model",
                },
            ],
        }

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents."
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_document,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post(
        "/api/v1/postgresql/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "员工每周可以申请一天远程办公。远程办公需要提前提交申请。",
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 201

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["schema_initialized"] is True
    assert captured["title"] == "远程办公制度"
    assert captured["file_type"] == "md"
    assert captured["content"] == (
        "员工每周可以申请一天远程办公。远程办公需要提前提交申请。"
    )

    assert data == {
        "id": 1,
        "title": "远程办公制度",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
    }


def test_create_postgresql_document_with_content_rejects_sqlite_url():
    app.dependency_overrides[get_postgresql_database_url] = lambda: "sqlite:///data/app.db"

    response = client.post(
        "/api/v1/postgresql/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "员工每周可以申请一天远程办公。",
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 400
    assert "PostgreSQL URL" in response.json()["detail"]


def test_create_postgresql_document_with_content_returns_409_when_not_created(
    monkeypatch,
):
    def fake_connect(database_url: str):
        return FakeConnection()

    def fake_initialize_schema(connection):
        pass

    def fake_create_document(
        connection,
        title: str,
        file_type: str,
        content: str,
    ):
        return None

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents."
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_document,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post(
        "/api/v1/postgresql/documents/with-content",
        json={
            "title": "重复文档",
            "file_type": "md",
            "content": "员工每天需要完成 8 小时工作。",
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 409
    assert "文档创建失败" in response.json()["detail"]


def test_create_postgresql_document_with_content_returns_503_when_embedding_fails(
    monkeypatch,
):
    def fake_connect(database_url: str):
        return FakeConnection()

    def fake_initialize_schema(connection):
        pass

    def fake_create_document(
        connection,
        title: str,
        file_type: str,
        content: str,
    ):
        raise PostgreSQLDocumentIndexingError("PostgreSQL 文档索引失败")

    monkeypatch.setattr(
        "backend.routers.postgresql_documents.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "backend.routers.postgresql_documents."
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_document,
    )

    app.dependency_overrides[get_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post(
        "/api/v1/postgresql/documents/with-content",
        json={
            "title": "Embedding 失败文档",
            "file_type": "md",
            "content": "员工每天需要完成 8 小时工作。",
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 503
    assert "PostgreSQL 文档索引失败" in response.json()["detail"]
