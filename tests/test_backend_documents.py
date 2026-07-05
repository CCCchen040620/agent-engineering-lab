from fastapi.testclient import TestClient
from backend.routers.documents import get_documents_file_path
from backend.services.document_service import save_documents
from week02.load_documents import load_documents
from backend.main import app


client = TestClient(app)


def test_list_documents_endpoint():
    response = client.get("/api/v1/documents")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 4
    assert data[0]["title"] == "员工手册"
    assert data[1]["title"] == "报销制度"
    assert data[2]["title"] == "请假制度"
    assert data[3]["title"] == "培训资料"


def test_list_documents_endpoint_with_indexed_only():
    response = client.get("/api/v1/documents?indexed_only=true")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "员工手册"
    assert data[1]["title"] == "请假制度"


def test_list_documents_endpoint_with_file_type():
    response = client.get("/api/v1/documents?file_type=pdf")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "报销制度"
    assert data[1]["title"] == "培训资料"


def test_list_documents_endpoint_with_indexed_only_and_file_type():
    response = client.get("/api/v1/documents?indexed_only=true&file_type=md")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["title"] == "员工手册"
    assert data[1]["title"] == "请假制度"


def test_get_document_by_title():
    response = client.get("/api/v1/documents/员工手册")

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "员工手册"
    assert data["file_type"] == "md"


def test_get_document_by_title_returns_404_when_not_found():
    response = client.get("/api/v1/documents/不存在的文档")

    assert response.status_code == 404
    assert response.json()["detail"] == "文档不存在。"


def test_delete_document_endpoint(tmp_path):
    file_path = tmp_path / "documents.json"
    documents = [
        {
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