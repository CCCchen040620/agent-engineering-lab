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