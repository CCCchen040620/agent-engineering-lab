from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path


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