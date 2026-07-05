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