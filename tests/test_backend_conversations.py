from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import db_documents
from backend.routers.db_documents import get_database_path


client = TestClient(app)


def test_conversation_endpoint_uses_config_database_path(tmp_path, monkeypatch):
    app.dependency_overrides.clear()
    database_path = tmp_path / "configured.db"
    monkeypatch.setattr(db_documents, "DATABASE_PATH", str(database_path))

    response = client.post(
        "/api/v1/conversations",
        json={"title": "配置路径会话"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert database_path.exists()


def test_create_conversation_endpoint(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/conversations",
        json={"title": "第一次对话"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "第一次对话"
    assert data["summary"] == ""


def test_list_conversations_endpoint(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    client.post(
        "/api/v1/conversations",
        json={"title": "第一次对话"},
    )

    client.post(
        "/api/v1/conversations",
        json={"title": "第二次对话"},
    )

    response = client.get("/api/v1/conversations")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data == [
        {
            "id": 1,
            "title": "第一次对话",
            "summary": "",
        },
        {
            "id": 2,
            "title": "第二次对话",
            "summary": "",
        },
    ]


def test_get_conversation_by_id_endpoint(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "长期记忆测试"},
    )

    conversation_id = create_response.json()["id"]

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "id": conversation_id,
        "title": "长期记忆测试",
        "summary": "",
    }


def test_get_conversation_by_id_endpoint_returns_404_when_not_found(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.get("/api/v1/conversations/999")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "会话不存在。"

    
def test_add_conversation_message_endpoint(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "第一次对话"},
    )

    conversation_id = conversation_response.json()["id"]

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "role": "user",
            "content": "我叫陈晨",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["conversation_id"] == conversation_id
    assert data["role"] == "user"
    assert data["content"] == "我叫陈晨"


def test_list_conversation_messages_endpoint(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "第一次对话"},
    )

    conversation_id = conversation_response.json()["id"]

    client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "role": "user",
            "content": "我叫陈晨",
        },
    )

    client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "role": "assistant",
            "content": "我记住了，你叫陈晨。",
        },
    )

    response = client.get(f"/api/v1/conversations/{conversation_id}/messages")

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["role"] == "user"
    assert data[0]["content"] == "我叫陈晨"
    assert data[1]["role"] == "assistant"
    assert data[1]["content"] == "我记住了，你叫陈晨。"


def test_list_conversation_messages_endpoint_returns_404_when_not_found(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.get("/api/v1/conversations/999/messages")

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "会话不存在。"


def test_add_conversation_message_endpoint_returns_404_when_not_found(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/conversations/999/messages",
        json={
            "role": "user",
            "content": "我叫陈晨",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "会话不存在。"
