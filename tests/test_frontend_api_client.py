import requests

from frontend.api_client import chat_with_llm_api, submit_feedback_api


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


def test_chat_with_llm_api_posts_question_and_query_params(monkeypatch):
    captured = {}

    def fake_post(url, params, json, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            {
                "question": "新员工什么时候完成安全培训？",
                "keyword": "安全培训",
                "answer": "30 天内完成安全培训。",
                "citations": [],
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_llm_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        top_k=3,
        mode="precomputed_embedding",
        min_score=0.8,
    )

    assert error_message is None
    assert data["answer"] == "30 天内完成安全培训。"

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/db/chat/llm"
    assert captured["params"] == {
        "top_k": 3,
        "mode": "precomputed_embedding",
        "min_score": 0.8,
    }
    assert captured["json"] == {"question": "新员工什么时候完成安全培训？"}
    assert captured["timeout"] == 300


def test_chat_with_llm_api_returns_backend_error(monkeypatch):
    def fake_post(url, params, json, timeout):
        return FakeResponse(422, {"detail": "问题不能为空。"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_llm_api(
        base_url="http://127.0.0.1:8000",
        question="",
        top_k=3,
        mode="precomputed_embedding",
        min_score=0.8,
    )

    assert data is None
    assert error_message == "问题不能为空。"


def test_chat_with_llm_api_handles_network_failure(monkeypatch):
    def fake_post(url, params, json, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_llm_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        top_k=3,
        mode="precomputed_embedding",
        min_score=0.8,
    )

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"


def test_submit_feedback_api_posts_feedback(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            201,
            {
                "id": 1,
                "question": "新员工什么时候完成安全培训？",
                "answer": "30 天内完成安全培训。",
                "rating": "helpful",
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = submit_feedback_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        answer="30 天内完成安全培训。",
        rating="helpful",
    )

    assert error_message is None
    assert data["id"] == 1
    assert data["rating"] == "helpful"

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/feedback"
    assert captured["json"] == {
        "question": "新员工什么时候完成安全培训？",
        "answer": "30 天内完成安全培训。",
        "rating": "helpful",
    }
    assert captured["timeout"] == 30


def test_submit_feedback_api_returns_backend_error(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(422, {"detail": "rating 不合法。"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = submit_feedback_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        answer="30 天内完成安全培训。",
        rating="bad",
    )

    assert data is None
    assert error_message == "rating 不合法。"


def test_submit_feedback_api_handles_network_failure(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = submit_feedback_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        answer="30 天内完成安全培训。",
        rating="helpful",
    )

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"
