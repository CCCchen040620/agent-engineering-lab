from fastapi.testclient import TestClient

from backend.main import app


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