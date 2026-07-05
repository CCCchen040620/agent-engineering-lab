from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_chat_endpoint_returns_answer():
    response = client.post(
        "/api/v1/chat",
        json={"question": "差旅报销多久内提交？"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "差旅报销多久内提交？"
    assert data["keyword"] == "差旅报销"
    assert "差旅报销需要在出差结束后 7 天内提交。" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["title"] == "reimbursement_policy"


def test_chat_endpoint_rejects_empty_question():
    response = client.post(
        "/api/v1/chat",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_chat_endpoint_refuses_unknown_question():
    response = client.post(
        "/api/v1/chat",
        json={"question": "公司有没有股票期权？"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "公司有没有股票期权？"
    assert data["keyword"] == "公司有没有股票期权？"
    assert "暂时无法回答" in data["answer"]
    assert data["citations"] == []