from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_memory_demo_remembers_name_in_same_thread():
    first_response = client.post(
        "/api/v1/memory-demo/chat",
        params={"thread_id": "chen"},
        json={"question": "我叫陈晨"},
    )

    second_response = client.post(
        "/api/v1/memory-demo/chat",
        params={"thread_id": "chen"},
        json={"question": "我叫什么？"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["remembered_name"] == "陈晨"
    assert "我记住了" in first_data["answer"]

    assert second_data["remembered_name"] == "陈晨"
    assert second_data["answer"] == "你叫陈晨。"
    assert second_data["messages"] == ["我叫陈晨", "我叫什么？"]


def test_memory_demo_does_not_share_memory_between_threads():
    first_response = client.post(
        "/api/v1/memory-demo/chat",
        params={"thread_id": "chen"},
        json={"question": "我叫陈晨"},
    )

    second_response = client.post(
        "/api/v1/memory-demo/chat",
        params={"thread_id": "another"},
        json={"question": "我叫什么？"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    data = second_response.json()

    assert data["remembered_name"] is None
    assert data["answer"] == "我还不知道你的名字。"
    assert data["messages"] == ["我叫什么？"]


def test_memory_demo_requires_thread_id():
    response = client.post(
        "/api/v1/memory-demo/chat",
        json={"question": "我叫陈晨"},
    )

    assert response.status_code == 422