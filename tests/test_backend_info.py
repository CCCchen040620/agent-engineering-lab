from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_info_endpoint():
    response = client.get("/api/v1/info")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Enterprise Knowledge Base Agent"
    assert data["version"] == "0.1.0"
    assert "chat_with_citations" in data["features"]
    assert "refusal_for_unknown_questions" in data["features"]
    assert "list_documents" in data["features"]
    assert "create_document" in data["features"]
    assert "delete_document_by_id" in data["features"]
    assert "sqlite_list_documents" in data["features"]
    assert "sqlite_create_document" in data["features"]
    assert "sqlite_delete_document_by_id" in data["features"]
    assert "sqlite_chat_with_citations" in data["features"]