from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.system import get_system_status_builder


client = TestClient(app)


def test_system_status_endpoint():
    def fake_status_builder():
        return {
            "status": "ok",
            "api": "ok",
            "database": {"status": "ok"},
            "ollama": {
                "status": "ok",
                "llm_model": {
                    "name": "qwen3.6:latest",
                    "available": True,
                },
                "embedding_model": {
                    "name": "bge-m3:latest",
                    "available": True,
                },
            },
        }

    app.dependency_overrides[get_system_status_builder] = lambda: fake_status_builder

    response = client.get("/api/v1/system/status")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["api"] == "ok"
    assert data["database"]["status"] == "ok"
    assert data["ollama"]["llm_model"]["name"] == "qwen3.6:latest"
