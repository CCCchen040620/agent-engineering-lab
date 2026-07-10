from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
    list_chunks_by_document_id,
)
from backend.services.sqlite_embedding_repository import find_chunk_embedding_by_chunk_id


client = TestClient(app)


def use_fake_embedder(monkeypatch):
    def fake_embed_with_ollama(text: str) -> list[float]:
        return [float(len(text)), 1.0]

    monkeypatch.setattr(
        "backend.services.document_indexing_service.embed_with_ollama",
        fake_embed_with_ollama,
    )


def test_list_db_documents_endpoint(tmp_path):
    use_temp_database(tmp_path)

    client.post(
        "/api/v1/db/documents",
        json={
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
    )

    response = client.get("/api/v1/db/documents")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "员工手册"


def test_list_db_documents_endpoint_with_indexed_only(tmp_path):
    use_temp_database(tmp_path)

    client.post(
        "/api/v1/db/documents",
        json={
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
    )

    client.post(
        "/api/v1/db/documents",
        json={
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
            "is_indexed": False,
        },
    )

    response = client.get("/api/v1/db/documents?indexed_only=true")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "员工手册"
    assert data[0]["is_indexed"] == True


def test_list_db_documents_endpoint_with_file_type(tmp_path):
    use_temp_database(tmp_path)

    client.post(
        "/api/v1/db/documents",
        json={
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
    )

    client.post(
        "/api/v1/db/documents",
        json={
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
            "is_indexed": False,
        },
    )

    response = client.get("/api/v1/db/documents?file_type=pdf")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "培训资料"
    assert data[0]["file_type"] == "pdf"


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


def test_sqlite_chat_endpoint_vector_mode(tmp_path):
    database_path = use_temp_database(tmp_path)

    connection = create_connection(str(database_path))
    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="报销制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工报销需要提交发票。",
    )

    connection.close()

    response = client.post(
        "/api/v1/db/chat?mode=vector",
        json={"question": "报销发票怎么提交？"},
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data["citations"]) == 1
    assert data["citations"][0]["title"] == "报销制度"


def test_sqlite_llm_chat_endpoint_refuses_unknown_question(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/chat/llm",
        json={"question": "公司有没有股票期权？"},
    )

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert "暂时无法回答" in data["answer"]
    assert data["citations"] == []


def test_create_db_document_with_content_endpoint(monkeypatch, tmp_path):
    use_fake_embedder(monkeypatch)

    database_path = use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "员工每周可以申请一天远程办公。远程办公需要提前提交申请。",
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 201

    data = response.json()

    connection = create_connection(str(database_path))
    chunks = list_chunks_by_document_id(connection, data["id"])
    first_embedding = find_chunk_embedding_by_chunk_id(connection, chunks[0]["id"])
    connection.close()

    assert data["title"] == "远程办公制度"
    assert data["chunk_count"] == 2
    assert data["is_indexed"] == True
    assert len(chunks) == 2
    assert first_embedding["embedding"] == [float(len(chunks[0]["text"])), 1.0]


def test_create_db_document_with_content_rejects_no_valid_chunks(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/documents/with-content",
        json={
            "title": "空内容制度",
            "file_type": "md",
            "content": "。。。\n   ！！！？？？",
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 422
    assert response.json()["detail"] == "文档正文没有有效内容。"


def test_create_db_document_with_content_returns_409_for_duplicate_title(
    monkeypatch,
    tmp_path,
):
    use_fake_embedder(monkeypatch)

    use_temp_database(tmp_path)

    first_response = client.post(
        "/api/v1/db/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "员工每周可以申请一天远程办公。",
        },
    )

    second_response = client.post(
        "/api/v1/db/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "远程办公需要提前提交申请。",
        },
    )

    clear_dependency_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "文档已存在。"


def test_create_db_document_with_content_returns_503_when_embedding_fails(
    monkeypatch,
    tmp_path,
):
    use_temp_database(tmp_path)

    def failing_embedder(text: str) -> list[float]:
        raise RuntimeError("embedding failed")

    monkeypatch.setattr(
        "backend.services.document_indexing_service.embed_with_ollama",
        failing_embedder,
    )

    response = client.post(
        "/api/v1/db/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "员工可以远程办公。远程办公需要提前申请。",
        },
    )

    list_response = client.get("/api/v1/db/documents")

    clear_dependency_overrides()

    assert response.status_code == 503
    assert "文档索引失败" in response.json()["detail"]
    assert list_response.json() == []


def test_list_db_document_chunks_endpoint(monkeypatch, tmp_path):
    use_fake_embedder(monkeypatch)

    database_path = use_temp_database(tmp_path)

    create_response = client.post(
        "/api/v1/db/documents/with-content",
        json={
            "title": "远程办公制度",
            "file_type": "md",
            "content": "员工每周可以申请一天远程办公。远程办公需要提前提交申请。",
        },
    )

    document_id = create_response.json()["id"]

    response = client.get(f"/api/v1/db/documents/{document_id}/chunks")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["document_id"] == document_id
    assert data[0]["text"] == "员工每周可以申请一天远程办公。"


def test_list_db_document_chunks_endpoint_returns_404_when_document_not_found(tmp_path):
    use_temp_database(tmp_path)

    response = client.get("/api/v1/db/documents/999/chunks")

    clear_dependency_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "文档不存在。"
def test_upload_text_document_endpoint(monkeypatch, tmp_path):
    database_path = use_temp_database(tmp_path)

    use_fake_embedder(monkeypatch)

    response = client.post(
        "/api/v1/db/documents/upload-text",
        data={"title": "访客制度"},
        files={
            "file": (
                "visitor_policy.txt",
                "访客进入办公区需要提前登记。访客需要由员工陪同进入办公区。".encode(
                    "utf-8"
                ),
                "text/plain",
            )
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 201

    data = response.json()

    connection = create_connection(str(database_path))
    chunks = list_chunks_by_document_id(connection, data["id"])
    first_embedding = find_chunk_embedding_by_chunk_id(connection, chunks[0]["id"])
    connection.close()

    assert data["title"] == "访客制度"
    assert data["file_type"] == "txt"
    assert data["chunk_count"] == 2
    assert len(chunks) == 2
    assert first_embedding["embedding"] == [float(len(chunks[0]["text"])), 1.0]


def test_upload_text_document_endpoint_uses_filename_as_title(monkeypatch, tmp_path):
    use_temp_database(tmp_path)

    use_fake_embedder(monkeypatch)

    response = client.post(
        "/api/v1/db/documents/upload-text",
        files={
            "file": (
                "visitor_policy.txt",
                "访客进入办公区需要提前登记。".encode("utf-8"),
                "text/plain",
            )
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 201
    assert response.json()["title"] == "visitor_policy"


def test_upload_text_document_endpoint_rejects_non_txt_file(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/documents/upload-text",
        files={
            "file": (
                "visitor_policy.pdf",
                "访客进入办公区需要提前登记。".encode("utf-8"),
                "application/pdf",
            )
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 422
    assert response.json()["detail"] == "仅支持 txt 文件。"


def test_upload_text_document_endpoint_rejects_invalid_encoding(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/documents/upload-text",
        files={
            "file": (
                "visitor_policy.txt",
                b"\xff\xfe\xfd",
                "text/plain",
            )
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 422
    assert response.json()["detail"] == "文件读取失败，请上传 UTF-8 编码的 txt 文件。"


def test_upload_text_document_endpoint_rejects_no_valid_chunks(tmp_path):
    use_temp_database(tmp_path)

    response = client.post(
        "/api/v1/db/documents/upload-text",
        files={
            "file": (
                "empty_policy.txt",
                "。。。\n   ！！！？？？".encode("utf-8"),
                "text/plain",
            )
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 422
    assert response.json()["detail"] == "文档正文没有有效内容。"


def test_upload_text_document_endpoint_returns_503_when_embedding_fails(
    monkeypatch,
    tmp_path,
):
    use_temp_database(tmp_path)

    def failing_embedder(text: str) -> list[float]:
        raise RuntimeError("embedding failed")

    monkeypatch.setattr(
        "backend.services.document_indexing_service.embed_with_ollama",
        failing_embedder,
    )

    response = client.post(
        "/api/v1/db/documents/upload-text",
        data={"title": "访客制度"},
        files={
            "file": (
                "visitor_policy.txt",
                "访客进入办公区需要提前登记。".encode("utf-8"),
                "text/plain",
            )
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 503
    assert "文档索引失败" in response.json()["detail"]
