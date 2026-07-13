import requests

from frontend.api_client import (
    backfill_postgresql_embeddings_api,
    chat_with_agent_api,
    chat_with_llm_api,
    chat_with_langgraph_agent_api,
    create_document_with_content_api,
    create_postgresql_document_with_content_api,
    find_rag_backend_capabilities,
    get_error_detail,
    get_info_api,
    get_system_status_api,
    list_document_chunks_api,
    list_documents_api,
    list_postgresql_document_source_summary_api,
    list_postgresql_document_embedding_status_api,
    rag_backend_supports_feature,
    submit_feedback_api,
    upload_text_document_api,
    parse_sse_event_line,
    stream_langgraph_agent_api,
)


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


class FakeStreamResponse:
    def __init__(self, status_code, lines):
        self.status_code = status_code
        self.lines = lines

    def iter_lines(self, decode_unicode=True):
        return iter(self.lines)

    def json(self):
        return {"detail": "请求失败。"}

       
class BrokenJsonResponse:
    def json(self):
        raise ValueError("invalid json")


def test_get_error_detail_prefers_unified_error_message():
    response = FakeResponse(
        404,
        {
            "detail": "旧错误信息。",
            "error": {
                "code": "not_found",
                "message": "文档不存在。",
                "status_code": 404,
            },
            "request_id": "request-123",
        },
    )

    message = get_error_detail(response)

    assert message == "文档不存在。（请求编号：request-123）"


def test_get_error_detail_falls_back_to_detail():
    response = FakeResponse(409, {"detail": "文档已存在。"})

    message = get_error_detail(response)

    assert message == "文档已存在。"


def test_get_error_detail_falls_back_when_response_is_not_json():
    message = get_error_detail(BrokenJsonResponse())

    assert message == "请求失败，请稍后再试。"


def test_get_system_status_api_gets_status(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            {
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
            },
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = get_system_status_api("http://127.0.0.1:8000")

    assert error_message is None
    assert data["status"] == "ok"
    assert data["ollama"]["llm_model"]["available"] is True

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/system/status"
    assert captured["timeout"] == 30


def test_get_info_api_gets_backend_capabilities(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            {
                "name": "Enterprise Knowledge Base Agent",
                "rag_backends": [
                    {
                        "backend": "sqlite",
                        "supported_features": ["conversation_chat"],
                    }
                ],
            },
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = get_info_api("http://127.0.0.1:8000")

    assert error_message is None
    assert data["rag_backends"][0]["backend"] == "sqlite"
    assert captured["url"] == "http://127.0.0.1:8000/api/v1/info"
    assert captured["timeout"] == 30


def test_get_info_api_handles_network_failure(monkeypatch):
    def fake_get(url, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = get_info_api("http://127.0.0.1:8000")

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"


def test_find_rag_backend_capabilities():
    info = {
        "rag_backends": [
            {
                "backend": "sqlite",
                "supported_features": ["conversation_chat"],
            },
            {
                "backend": "postgresql",
                "supported_features": ["langgraph_agent_chat"],
            },
        ]
    }

    capabilities = find_rag_backend_capabilities(info, " PostgreSQL ")

    assert capabilities == {
        "backend": "postgresql",
        "supported_features": ["langgraph_agent_chat"],
    }


def test_rag_backend_supports_feature():
    info = {
        "rag_backends": [
            {
                "backend": "sqlite",
                "supported_features": ["conversation_chat"],
            },
            {
                "backend": "postgresql",
                "supported_features": ["langgraph_agent_chat"],
            },
        ]
    }

    assert rag_backend_supports_feature(info, "sqlite", "conversation_chat") is True
    assert rag_backend_supports_feature(info, "postgresql", "conversation_chat") is False


def test_rag_backend_supports_feature_falls_back_to_true_without_capabilities():
    assert rag_backend_supports_feature(None, "postgresql", "conversation_chat") is True


def test_list_documents_api_uses_sqlite_endpoint_by_default(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            [
                {
                    "id": 1,
                    "title": "员工手册",
                    "file_type": "md",
                    "chunk_count": 3,
                    "is_indexed": True,
                }
            ],
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_documents_api("http://127.0.0.1:8000")

    assert error_message is None
    assert data[0]["title"] == "员工手册"
    assert captured["url"] == "http://127.0.0.1:8000/api/v1/db/documents"
    assert captured["timeout"] == 30


def test_list_documents_api_can_use_postgresql_endpoint(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            [
                {
                    "id": 1,
                    "title": "PostgreSQL 文档",
                    "file_type": "md",
                    "chunk_count": 2,
                    "is_indexed": True,
                }
            ],
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_documents_api(
        "http://127.0.0.1:8000",
        backend="postgresql",
    )

    assert error_message is None
    assert data[0]["title"] == "PostgreSQL 文档"
    assert captured["url"] == (
        "http://127.0.0.1:8000/api/v1/postgresql/documents"
    )


def test_list_document_chunks_api_uses_selected_backend(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url

        return FakeResponse(
            200,
            [
                {
                    "id": 1,
                    "document_id": 2,
                    "text": "员工每天需要完成 8 小时工作。",
                }
            ],
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_document_chunks_api(
        "http://127.0.0.1:8000",
        document_id=2,
        backend="postgresql",
    )

    assert error_message is None
    assert data[0]["document_id"] == 2
    assert captured["url"] == (
        "http://127.0.0.1:8000/api/v1/postgresql/documents/2/chunks"
    )


def test_list_postgresql_document_embedding_status_api(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            [
                {
                    "document_id": 1,
                    "title": "PostgreSQL 测试文档",
                    "chunk_count": 2,
                    "embedding_count": 2,
                    "is_embedding_complete": True,
                }
            ],
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_postgresql_document_embedding_status_api(
        "http://127.0.0.1:8000",
    )

    assert error_message is None
    assert data[0]["title"] == "PostgreSQL 测试文档"
    assert captured["url"] == (
        "http://127.0.0.1:8000"
        "/api/v1/postgresql/documents/embedding-status"
    )
    assert captured["timeout"] == 30


def test_list_postgresql_document_embedding_status_api_returns_backend_error(
    monkeypatch,
):
    def fake_get(url, timeout):
        return FakeResponse(400, {"detail": "DATABASE_URL must be a PostgreSQL URL."})

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_postgresql_document_embedding_status_api(
        "http://127.0.0.1:8000",
    )

    assert data is None
    assert error_message == "DATABASE_URL must be a PostgreSQL URL."


def test_list_postgresql_document_source_summary_api(monkeypatch):
    captured = {}

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            [
                {
                    "source": "migration",
                    "document_count": 8,
                },
                {
                    "source": "production",
                    "document_count": 5,
                },
            ],
        )

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_postgresql_document_source_summary_api(
        "http://127.0.0.1:8000",
    )

    assert error_message is None
    assert data == [
        {
            "source": "migration",
            "document_count": 8,
        },
        {
            "source": "production",
            "document_count": 5,
        },
    ]
    assert captured["url"] == (
        "http://127.0.0.1:8000"
        "/api/v1/postgresql/documents/source-summary"
    )
    assert captured["timeout"] == 30


def test_list_postgresql_document_source_summary_api_returns_backend_error(
    monkeypatch,
):
    def fake_get(url, timeout):
        return FakeResponse(400, {"detail": "DATABASE_URL must be a PostgreSQL URL."})

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_postgresql_document_source_summary_api(
        "http://127.0.0.1:8000",
    )

    assert data is None
    assert error_message == "DATABASE_URL must be a PostgreSQL URL."


def test_backfill_postgresql_embeddings_api_posts_request(monkeypatch):
    captured = {}

    def fake_post(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            200,
            {
                "total_chunks": 3,
                "updated": 1,
                "skipped": 2,
                "model": "bge-m3:latest",
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = backfill_postgresql_embeddings_api(
        "http://127.0.0.1:8000",
    )

    assert error_message is None
    assert data == {
        "total_chunks": 3,
        "updated": 1,
        "skipped": 2,
        "model": "bge-m3:latest",
    }
    assert captured["url"] == (
        "http://127.0.0.1:8000/api/v1/postgresql/embeddings/backfill"
    )
    assert captured["timeout"] == 300


def test_backfill_postgresql_embeddings_api_returns_backend_error(monkeypatch):
    def fake_post(url, timeout):
        return FakeResponse(503, {"detail": "PostgreSQL embedding 回填失败"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = backfill_postgresql_embeddings_api(
        "http://127.0.0.1:8000",
    )

    assert data is None
    assert error_message == "PostgreSQL embedding 回填失败"


def test_backfill_postgresql_embeddings_api_handles_network_failure(monkeypatch):
    def fake_post(url, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = backfill_postgresql_embeddings_api(
        "http://127.0.0.1:8000",
    )

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"


def test_list_documents_api_returns_backend_error(monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse(400, {"detail": "DATABASE_URL must be a PostgreSQL URL."})

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = list_documents_api(
        "http://127.0.0.1:8000",
        backend="postgresql",
    )

    assert data is None
    assert error_message == "DATABASE_URL must be a PostgreSQL URL."


def test_get_system_status_api_handles_network_failure(monkeypatch):
    def fake_get(url, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "get", fake_get)

    data, error_message = get_system_status_api("http://127.0.0.1:8000")

    assert data is None
    assert error_message == "后端服务暂时不可用，请确认 FastAPI 已启动。"


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


def test_chat_with_llm_api_returns_unified_backend_error(monkeypatch):
    def fake_post(url, params, json, timeout):
        return FakeResponse(
            429,
            {
                "detail": "请求过于频繁，请稍后再试。",
                "error": {
                    "code": "rate_limited",
                    "message": "请求过于频繁，请稍后再试。",
                    "status_code": 429,
                },
                "request_id": "rate-limit-request",
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

    assert data is None
    assert error_message == "请求过于频繁，请稍后再试。（请求编号：rate-limit-request）"


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


def test_chat_with_langgraph_agent_api_sends_timeout_and_retriever_backend(monkeypatch):
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
                "steps": [],
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = chat_with_langgraph_agent_api(
        base_url="http://127.0.0.1:8000",
        question="新员工什么时候完成安全培训？",
        top_k=3,
        mode="precomputed_embedding",
        min_score=0.8,
        timeout_seconds=30,
        retriever_backend="postgresql",
    )

    assert error_message is None
    assert data["answer"] == "30 天内完成安全培训。"
    assert captured["params"]["timeout_seconds"] == 30
    assert captured["params"]["retriever_backend"] == "postgresql"


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


def test_create_postgresql_document_with_content_api_posts_document(monkeypatch):
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

    data, error_message = create_postgresql_document_with_content_api(
        base_url="http://127.0.0.1:8000",
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。",
    )

    assert error_message is None
    assert data["title"] == "远程办公制度"
    assert data["chunk_count"] == 2

    assert captured["url"] == (
        "http://127.0.0.1:8000"
        "/api/v1/postgresql/documents/with-content"
    )
    assert captured["json"] == {
        "title": "远程办公制度",
        "file_type": "md",
        "content": "员工每周可以申请一天远程办公。",
    }
    assert captured["timeout"] == 300


def test_create_postgresql_document_with_content_api_returns_backend_error(
    monkeypatch,
):
    def fake_post(url, json, timeout):
        return FakeResponse(409, {"detail": "文档创建失败。"})

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = create_postgresql_document_with_content_api(
        base_url="http://127.0.0.1:8000",
        title="远程办公制度",
        file_type="md",
        content="员工每周可以申请一天远程办公。",
    )

    assert data is None
    assert error_message == "文档创建失败。"


def test_create_postgresql_document_with_content_api_handles_network_failure(
    monkeypatch,
):
    def fake_post(url, json, timeout):
        raise requests.RequestException

    monkeypatch.setattr(requests, "post", fake_post)

    data, error_message = create_postgresql_document_with_content_api(
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


def test_parse_sse_event_line_returns_event():
    event = parse_sse_event_line(
        'data: {"type": "delta", "content": "你好"}'
    )

    assert event == {
        "type": "delta",
        "content": "你好",
    }


def test_parse_sse_event_line_ignores_non_data_line():
    event = parse_sse_event_line("event: message")

    assert event is None


def test_stream_langgraph_agent_api_yields_sse_events(monkeypatch):
    captured = {}

    def fake_post(url, params, json, timeout, stream):
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        captured["timeout"] = timeout
        captured["stream"] = stream

        return FakeStreamResponse(
            200,
            [
                'data: {"type": "delta", "content": "你好"}',
                "",
                'data: {"type": "metadata", "keyword": "测试"}',
                'data: {"type": "done"}',
            ],
        )

    monkeypatch.setattr(requests, "post", fake_post)

    events = list(
        stream_langgraph_agent_api(
            base_url="http://127.0.0.1:8000",
            question="测试问题",
            top_k=3,
            mode="precomputed_embedding",
            min_score=0.8,
            timeout_seconds=30,
        )
    )

    assert events == [
        {"type": "delta", "content": "你好"},
        {"type": "metadata", "keyword": "测试"},
        {"type": "done"},
    ]

    assert captured["url"] == "http://127.0.0.1:8000/api/v1/langgraph-agent/chat/stream"
    assert captured["params"]["timeout_seconds"] == 30
    assert captured["stream"] is True


def test_stream_langgraph_agent_api_yields_error_when_backend_returns_error(monkeypatch):
    def fake_post(url, params, json, timeout, stream):
        return FakeStreamResponse(
            429,
            [],
        )

    monkeypatch.setattr(requests, "post", fake_post)

    events = list(
        stream_langgraph_agent_api(
            base_url="http://127.0.0.1:8000",
            question="测试问题",
            top_k=3,
            mode="precomputed_embedding",
            min_score=0.8,
            timeout_seconds=30,
        )
    )

    assert events == [
        {
            "type": "error",
            "message": "请求失败。",
        }
    ]
