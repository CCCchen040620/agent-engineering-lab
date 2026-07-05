from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)


client = TestClient(app)


def test_list_db_documents_endpoint():
    response = client.get("/api/v1/db/documents")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "员工手册"


def test_list_db_documents_endpoint_with_indexed_only():
    response = client.get("/api/v1/db/documents?indexed_only=true")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for document in data:
        assert document["is_indexed"] == True


def test_list_db_documents_endpoint_with_file_type():
    response = client.get("/api/v1/db/documents?file_type=md")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for document in data:
        assert document["file_type"] == "md"


def use_temp_database(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    return database_path


def clear_dependency_overrides():
    app.dependency_overrides.clear()


def test_create_db_document_endpoint(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/documents",
        json={
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "培训资料"
    assert data["is_indexed"] == False


def test_create_db_document_endpoint_returns_409_for_duplicate_title(tmp_path):
    use_temp_database(tmp_path)

    first_response = client.post(
        "/api/v1/db/documents",
        json={
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
        },
    )

    second_response = client.post(
        "/api/v1/db/documents",
        json={
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
        },
    )

    clear_dependency_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "文档已存在。"


def test_get_db_document_by_id(tmp_path):
    use_temp_database(tmp_path)

    create_response = client.post(
        "/api/v1/db/documents",
        json={
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
    )

    document_id = create_response.json()["id"]

    response = client.get(f"/api/v1/db/documents/{document_id}")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == document_id
    assert data["title"] == "员工手册"


def test_get_db_document_by_id_returns_404_when_not_found(tmp_path):
    use_temp_database(tmp_path)

    response = client.get("/api/v1/db/documents/999")

    clear_dependency_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "文档不存在。"


def test_delete_db_document_by_id(tmp_path):
    use_temp_database(tmp_path)

    create_response = client.post(
        "/api/v1/db/documents",
        json={
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
    )

    document_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/db/documents/{document_id}")

    list_response = client.get("/api/v1/db/documents")

    clear_dependency_overrides()

    assert response.status_code == 200
    assert response.json() == {"message": "文档已删除。", "id": document_id}
    assert list_response.json() == []


def test_delete_db_document_by_id_returns_404_when_not_found(tmp_path):
    use_temp_database(tmp_path)

    response = client.delete("/api/v1/db/documents/999")

    clear_dependency_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "文档不存在。"


def test_sqlite_chat_endpoint(tmp_path):
    database_path = use_temp_database(tmp_path)

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

    response = client.post(
        "/api/v1/db/chat",
        json={"question": "新员工什么时候完成安全培训？"},
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["keyword"] == "安全培训"
    assert "新员工入职后需要在 30 天内完成安全培训。" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["title"] == "员工手册"


def test_sqlite_chat_endpoint_refuses_unknown_question(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/chat",
        json={"question": "公司有没有股票期权？"},
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert "暂时无法回答" in data["answer"]
    assert data["citations"] == []


def test_sqlite_chat_endpoint_respects_top_k(tmp_path):
    database_path = use_temp_database(tmp_path)

    connection = create_connection(str(database_path))
    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="报销制度",
        file_type="md",
        chunk_count=3,
        is_indexed=True,
    )

    insert_chunk_to_db(connection, document["id"], "报销片段1")
    insert_chunk_to_db(connection, document["id"], "报销片段2")
    insert_chunk_to_db(connection, document["id"], "报销片段3")

    connection.close()

    response = client.post(
        "/api/v1/db/chat?top_k=2",
        json={"question": "报销"},
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data["citations"]) == 2


def test_sqlite_chat_endpoint_rejects_invalid_top_k():
    response = client.post(
        "/api/v1/db/chat?top_k=0",
        json={"question": "报销"},
    )

    assert response.status_code == 422


def test_sqlite_chat_endpoint_rejects_too_large_top_k():
    response = client.post(
        "/api/v1/db/chat?top_k=6",
        json={"question": "报销"},
    )

    assert response.status_code == 422