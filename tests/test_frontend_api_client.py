import requests

from frontend.api_client import (
    chat_with_agent_api,
    chat_with_llm_api,
    create_document_with_content_api,
    submit_feedback_api,
    upload_text_document_api,
)


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


def test_chat_with_agent_api_posts_question_and_query_params(monkeypatch):
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
                "answer": "新员工需要在入职后 30 天内完成安全培训。",
                "citations": [],
                "steps": [
                    {
                        "name": "search_knowledge_base",
                        "status": "completed",
                        "result_count": 1,
                    }
                ],
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_agent_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        top_k=3,
        mode="keyword",
        min_score=0.3,
    )

    assert error_message is None
    assert data["answer"] == "新员工需要在入职后 30 天内完成安全培训。"
    assert len(data["steps"]) == 1

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/agent/chat"
    assert captured["params"] == {
        "top_k": 3,
        "mode": "keyword",
        "min_score": 0.3,
    }
    assert captured["json"] == {"question": "新员工什么时候完成安全培训？"}
    assert captured["timeout"] == 300


def test_chat_with_agent_api_returns_backend_error(monkeypatch):
    def fake_post(url, params, json, timeout):
        return FakeResponse(422, {"detail": "问题不能为空。"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_agent_api(
        base_url="http://127.0.0.1:8000",
        question="",
        top_k=3,
        mode="keyword",
        min_score=0.3,
    )

    assert data is None
    assert error_message == "问题不能为空。"


def test_chat_with_agent_api_handles_network_failure(monkeypatch):
    def fake_post(url, params, json, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_agent_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        top_k=3,
        mode="keyword",
        min_score=0.3,
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


def test_create_document_with_content_api_posts_document(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            201,
            {
                "id": 1,
                "title": "远程办公制度",
                "file_type": "md",
                "chunk_count": 2,
                "is_indexed": True,
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = create_document_with_content_api(
        base_url="http://127.0.0.1:8000",
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。",
    )

    assert error_message is None
    assert data["title"] == "远程办公制度"
    assert data["chunk_count"] == 2

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/db/documents/with-content"
    assert captured["json"] == {
        "title": "远程办公制度",
        "file_type": "md",
        "content": "员工每周可以申请一天远程办公。",
    }
    assert captured["timeout"] == 300


def test_create_document_with_content_api_returns_backend_error(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(409, {"detail": "文档已存在。"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = create_document_with_content_api(
        base_url="http://127.0.0.1:8000",
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。",
    )

    assert data is None
    assert error_message == "文档已存在。"


def test_create_document_with_content_api_handles_network_failure(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = create_document_with_content_api(
        base_url="http://127.0.0.1:8000",
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。",
    )

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"


def test_upload_text_document_api_posts_file(monkeypatch):
    captured = {}

    def fake_post(url, data, files, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["files"] = files
        captured["timeout"] = timeout

        return FakeResponse(
            201,
            {
                "id": 1,
                "title": "访客制度",
                "file_type": "txt",
                "chunk_count": 2,
                "is_indexed": True,
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = upload_text_document_api(
        base_url="http://127.0.0.1:8000",
        file_name="visitor_policy.txt",
        content=b"hello",
        title="访客制度",
    )

    assert error_message is None
    assert data["title"] == "访客制度"
    assert data["file_type"] == "txt"

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/db/documents/upload-text"
    assert captured["data"] == {"title": "访客制度"}
    assert captured["files"] == {
        "file": (
            "visitor_policy.txt",
            b"hello",
            "text/plain",
        )
    }
    assert captured["timeout"] == 300


def test_upload_text_document_api_omits_empty_title(monkeypatch):
    captured = {}

    def fake_post(url, data, files, timeout):
        captured["data"] = data

        return FakeResponse(
            201,
            {
                "id": 1,
                "title": "visitor_policy",
                "file_type": "txt",
                "chunk_count": 1,
                "is_indexed": True,
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = upload_text_document_api(
        base_url="http://127.0.0.1:8000",
        file_name="visitor_policy.txt",
        content=b"hello",
        title="",
    )

    assert error_message is None
    assert data["title"] == "visitor_policy"
    assert captured["data"] == {}


def test_upload_text_document_api_returns_backend_error(monkeypatch):
    def fake_post(url, data, files, timeout):
        return FakeResponse(409, {"detail": "文档已存在。"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = upload_text_document_api(
        base_url="http://127.0.0.1:8000",
        file_name="visitor_policy.txt",
        content=b"hello",
        title="访客制度",
    )

    assert data is None
    assert error_message == "文档已存在。"


def test_upload_text_document_api_handles_network_failure(monkeypatch):
    def fake_post(url, data, files, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = upload_text_document_api(
        base_url="http://127.0.0.1:8000",
        file_name="visitor_policy.txt",
        content=b"hello",
        title="访客制度",
    )

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"
