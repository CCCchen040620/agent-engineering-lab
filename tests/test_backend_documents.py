from fastapi.testclient import TestClient
from backend.routers.documents import get_documents_file_path
from backend.services.document_service import save_documents
from week02.load_documents import load_documents
from backend.main import app


client = TestClient(app)


def use_temp_documents_file(tmp_path, documents):
    file_path = tmp_path / "documents.json"
    save_documents(str(file_path), documents)

    app.dependency_overrides[get_documents_file_path] = lambda: str(file_path)

    return file_path


def clear_dependency_overrides():
    app.dependency_overrides.clear()


def test_list_documents_endpoint(tmp_path):
    documents = [
        {
            "id": 1,
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
        {
            "id": 2,
            "title": "报销制度",
            "file_type": "pdf",
            "chunk_count": 8,
            "is_indexed": False,
        },
        {
            "id": 3,
            "title": "请假制度",
            "file_type": "md",
            "chunk_count": 5,
            "is_indexed": True,
        },
    ]
    use_temp_documents_file(tmp_path, documents)

    response = client.get("/api/v1/documents")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert data[0]["title"] == "员工手册"
    assert data[1]["title"] == "报销制度"
    assert data[2]["title"] == "请假制度"


def test_list_documents_endpoint_with_indexed_only(tmp_path):
    documents = [
        {
            "id": 1,
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
        {
            "id": 2,
            "title": "报销制度",
            "file_type": "pdf",
            "chunk_count": 8,
            "is_indexed": False,
        },
        {
            "id": 3,
            "title": "请假制度",
            "file_type": "md",
            "chunk_count": 5,
            "is_indexed": True,
        },
    ]
    use_temp_documents_file(tmp_path, documents)

    response = client.get("/api/v1/documents?indexed_only=true")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "员工手册"
    assert data[1]["title"] == "请假制度"


def test_list_documents_endpoint_with_file_type(tmp_path):
    documents = [
        {
            "id": 1,
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
        {
            "id": 2,
            "title": "报销制度",
            "file_type": "pdf",
            "chunk_count": 8,
            "is_indexed": False,
        },
        {
            "id": 4,
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
            "is_indexed": False,
        },
    ]
    use_temp_documents_file(tmp_path, documents)

    response = client.get("/api/v1/documents?file_type=pdf")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "报销制度"
    assert data[1]["title"] == "培训资料"


def test_list_documents_endpoint_with_indexed_only_and_file_type(tmp_path):
    documents = [
        {
            "id": 1,
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
        {
            "id": 2,
            "title": "报销制度",
            "file_type": "pdf",
            "chunk_count": 8,
            "is_indexed": False,
        },
        {
            "id": 3,
            "title": "请假制度",
            "file_type": "md",
            "chunk_count": 5,
            "is_indexed": True,
        },
    ]
    use_temp_documents_file(tmp_path, documents)

    response = client.get("/api/v1/documents?indexed_only=true&file_type=md")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "员工手册"
    assert data[1]["title"] == "请假制度"


def test_get_document_by_title(tmp_path):
    documents = [
        {
            "id": 1,
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        }
    ]
    use_temp_documents_file(tmp_path, documents)

    response = client.get("/api/v1/documents/员工手册")

    clear_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "员工手册"
    assert data["file_type"] == "md"


def test_get_document_by_title_returns_404_when_not_found(tmp_path):
    use_temp_documents_file(tmp_path, [])

    response = client.get("/api/v1/documents/不存在的文档")

    clear_dependency_overrides()

    assert response.status_code == 404
    assert response.json()["detail"] == "文档不存在。"


def test_delete_document_endpoint(tmp_path):
    file_path = tmp_path / "documents.json"
    documents = [
        {
            "id": 1,
            "title": "测试文档",
            "file_type": "md",
            "chunk_count": 1,
            "is_indexed": True,
        }
    ]
    save_documents(str(file_path), documents)

    app.dependency_overrides[get_documents_file_path] = lambda: str(file_path)

    response = client.delete("/api/v1/documents/测试文档")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"message": "文档已删除。", "title": "测试文档"}

    loaded_documents = load_documents(str(file_path))
    assert loaded_documents == []


def test_delete_document_endpoint_returns_404_when_not_found(tmp_path):
    file_path = tmp_path / "documents.json"
    save_documents(str(file_path), [])

    app.dependency_overrides[get_documents_file_path] = lambda: str(file_path)

    response = client.delete("/api/v1/documents/不存在的文档")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "文档不存在。"


def test_create_document_endpoint(tmp_path):
    use_temp_documents_file(tmp_path, [])

    response = client.post(
        "/api/v1/documents",
        json={
            "id": 4,
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "培训资料"
    assert data["file_type"] == "pdf"
    assert data["chunk_count"] == 3
    assert data["is_indexed"] == False


def test_create_document_endpoint_returns_409_when_title_exists(tmp_path):
    documents = [
        {
            "id": 4,
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
            "is_indexed": False,
        }
    ]
    use_temp_documents_file(tmp_path, documents)

    response = client.post(
        "/api/v1/documents",
        json={
            "id": 4,
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
        },
    )

    clear_dependency_overrides()

    assert response.status_code == 409
    assert response.json()["detail"] == "文档已存在。"


def test_create_document_endpoint_rejects_empty_title():
    response = client.post(
        "/api/v1/documents",
        json={
            "id": 4,
            "title": "",
            "file_type": "pdf",
            "chunk_count": 3,
        },
    )

    assert response.status_code == 422