from fastapi.testclient import TestClient

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