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