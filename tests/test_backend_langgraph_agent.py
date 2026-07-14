from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path
from backend.routers import langgraph_agent as langgraph_agent_router
from backend.routers.langgraph_agent import (
    get_langgraph_agent_generator,
    get_langgraph_postgresql_database_url,
    resolve_retriever_backend,
)
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_conversation_repository import (
    add_message,
    create_conversations_table,
    create_messages_table,
    find_conversation_by_id,
)


client = TestClient(app)


def test_resolve_retriever_backend_marks_default_from_config(monkeypatch):
    monkeypatch.setattr(
        langgraph_agent_router,
        "RAG_RETRIEVER_BACKEND",
        "postgresql",
    )

    assert resolve_retriever_backend(None) == ("postgresql", "default")
    assert resolve_retriever_backend("") == ("postgresql", "default")


def test_resolve_retriever_backend_marks_override(monkeypatch):
    monkeypatch.setattr(
        langgraph_agent_router,
        "RAG_RETRIEVER_BACKEND",
        "postgresql",
    )

    assert resolve_retriever_backend("sqlite") == ("sqlite", "override")


def test_langgraph_agent_chat_endpoint_accepts_timeout_seconds(monkeypatch, tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/langgraph-agent/chat?timeout_seconds=1",
        json={"question": "知识库里有哪些文档？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["timeout_seconds"] == 1


def test_langgraph_agent_chat_endpoint_rejects_invalid_timeout_seconds():
    response = client.post(
        "/api/v1/langgraph-agent/chat?timeout_seconds=0",
        json={"question": "知识库里有哪些文档？"},
    )

    assert response.status_code == 422


def test_langgraph_agent_chat_endpoint_rejects_postgresql_retriever_when_database_url_is_not_postgresql():
    app.dependency_overrides[get_langgraph_postgresql_database_url] = lambda: (
        "sqlite:///data/app.db"
    )

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        params={"retriever_backend": "postgresql"},
        json={"question": "员工每天需要工作多久？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "DATABASE_URL must be a PostgreSQL URL to use PostgreSQL retriever."
    )


def test_langgraph_agent_chat_endpoint_answers_with_context(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    connection.close()

    def fake_generator(prompt: str) -> str:
        assert "新员工入职后需要在 30 天内完成安全培训。" in prompt
        return "新员工需要在入职后 30 天内完成安全培训。"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = lambda: fake_generator

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        json={"question": "新员工什么时候完成安全培训？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "answer_question"
    assert data["keyword"] == "安全培训"
    assert data["answer"] == "新员工需要在入职后 30 天内完成安全培训。"
    assert len(data["citations"]) == 1
    assert data["steps"][0]["tool"] == "load_conversation_summary"
    assert data["steps"][1]["tool"] == "decide_agent_intent"
    assert data["steps"][2]["tool"] == "search_knowledge_base_tool"
    assert data["steps"][3]["tool"] == "validate_context_node"
    assert data["steps"][3]["observation"]["has_valid_context"] is True
    assert data["steps"][4]["tool"] == "answer_with_context_tool"


def test_langgraph_agent_chat_endpoint_refuses_without_context(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        json={"question": "公司有没有股票期权？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "answer_question"
    assert data["keyword"] == "股票期权"
    assert data["citations"] == []
    assert data["steps"][0]["tool"] == "load_conversation_summary"
    assert data["steps"][1]["tool"] == "decide_agent_intent"
    assert data["steps"][2]["tool"] == "search_knowledge_base_tool"
    assert data["steps"][3]["tool"] == "validate_context_node"
    assert data["steps"][3]["observation"]["has_valid_context"] is False
    assert data["steps"][4]["tool"] == "refuse_answer_tool"


def test_langgraph_agent_chat_endpoint_reads_document_chunks(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=2,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工每天需要完成 8 小时工作。",
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工需要完成安全培训。",
    )

    connection.close()

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        json={"question": "查看员工手册的片段"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "read_document"
    assert data["keyword"] == "员工手册"
    assert data["document_title"] == "员工手册"
    assert "员工每天需要完成 8 小时工作。" in data["answer"]
    assert "新员工需要完成安全培训。" in data["answer"]
    assert len(data["citations"]) == 2

    assert data["steps"][0]["tool"] == "load_conversation_summary"
    assert data["steps"][1]["tool"] == "decide_agent_intent"
    assert data["steps"][2]["tool"] == "extract_document_title"
    assert data["steps"][3]["tool"] == "find_document_by_title_tool"
    assert data["steps"][3]["observation"]["found"] is True
    assert data["steps"][4]["tool"] == "read_document_chunks_tool"


def test_langgraph_agent_chat_endpoint_asks_clarification_when_title_missing(
    tmp_path,
):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        json={"question": "查看这份文档的片段"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "read_document"
    assert data["keyword"] == "文档标题"
    assert data["document_title"] == ""
    assert data["citations"] == []
    assert "文档标题" in data["answer"]

    assert data["steps"][0]["tool"] == "load_conversation_summary"
    assert data["steps"][1]["tool"] == "decide_agent_intent"
    assert data["steps"][2]["tool"] == "extract_document_title"
    assert data["steps"][2]["next_action"] == "ask_clarification_node"
    assert data["steps"][3]["tool"] == "ask_clarification_tool"


def test_langgraph_agent_chat_endpoint_accepts_retriever_backend(monkeypatch):
    captured = {}

    def fake_run_langgraph_agent(**kwargs):
        captured.update(kwargs)

        return {
            "question": kwargs["question"],
            "intent": "answer_question",
            "keyword": "安全培训",
            "contextual_question": kwargs["question"],
            "context_document_title": "",
            "snippets": [
                {
                    "title": "员工手册",
                    "path": "sqlite://1",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "score": 0.9,
                }
            ],
            "has_valid_context": True,
            "document_title": "",
            "document": None,
            "document_match_type": None,
            "missing_field": "",
            "answer": "新员工需要在入职后 30 天内完成安全培训。",
            "citations": [
                {
                    "title": "员工手册",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "path": "sqlite://1",
                }
            ],
            "steps": [],
            "database_path": kwargs["database_path"],
            "top_k": kwargs["top_k"],
            "mode": kwargs["mode"],
            "min_score": kwargs["min_score"],
            "retriever_backend": kwargs["retriever_backend"],
            "retriever_backend_source": kwargs["retriever_backend_source"],
            "generator": {},
            "timeout_seconds": kwargs["timeout_seconds"],
            "is_timeout": False,
            "is_fallback": False,
        }

    monkeypatch.setattr(
        "backend.routers.langgraph_agent.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        params={
            "retriever_backend": "sqlite",
            "top_k": 2,
            "mode": "precomputed_embedding",
            "min_score": 0.6,
        },
        json={"question": "新员工什么时候完成安全培训？"},
    )

    assert response.status_code == 200

    data = response.json()

    assert captured["retriever_backend"] == "sqlite"
    assert captured["retriever_backend_source"] == "override"
    assert captured["top_k"] == 2
    assert captured["mode"] == "precomputed_embedding"
    assert captured["min_score"] == 0.6
    assert data["retriever_backend"] == "sqlite"
    assert data["retriever_backend_source"] == "override"


def test_langgraph_agent_chat_endpoint_marks_default_retriever_backend(monkeypatch):
    captured = {}

    def fake_run_langgraph_agent(**kwargs):
        captured.update(kwargs)

        return {
            "question": kwargs["question"],
            "intent": "answer_question",
            "keyword": "安全培训",
            "contextual_question": kwargs["question"],
            "context_document_title": "",
            "snippets": [],
            "has_valid_context": False,
            "document_title": "",
            "document": None,
            "document_match_type": None,
            "missing_field": "",
            "answer": "知识库中没有找到相关资料，暂时无法回答。",
            "citations": [],
            "steps": [],
            "database_path": kwargs["database_path"],
            "top_k": kwargs["top_k"],
            "mode": kwargs["mode"],
            "min_score": kwargs["min_score"],
            "retriever_backend": kwargs["retriever_backend"],
            "retriever_backend_source": kwargs["retriever_backend_source"],
            "timeout_seconds": kwargs["timeout_seconds"],
            "is_timeout": False,
            "is_fallback": False,
        }

    monkeypatch.setattr(
        "backend.routers.langgraph_agent.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        json={"question": "新员工什么时候完成安全培训？"},
    )

    assert response.status_code == 200

    data = response.json()

    assert captured["retriever_backend"] == "sqlite"
    assert captured["retriever_backend_source"] == "default"
    assert data["retriever_backend"] == "sqlite"
    assert data["retriever_backend_source"] == "default"


def test_langgraph_agent_conversation_chat_saves_messages(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = (
        lambda: lambda prompt: "新员工需要在入职后 30 天内完成安全培训。"
    )

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "第一次对话"},
    )

    conversation_id = conversation_response.json()["id"]

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "公司有没有股票期权？"},
    )

    messages_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert messages_response.status_code == 200

    data = response.json()
    messages = messages_response.json()

    assert data["conversation_id"] == conversation_id
    assert len(data["saved_messages"]) == 2

    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "公司有没有股票期权？"
    assert messages[0]["metadata"]["question"] == "公司有没有股票期权？"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == data["answer"]
    assert messages[1]["metadata"]["intent"] == data["intent"]
    assert messages[1]["metadata"]["keyword"] == data["keyword"]
    assert messages[1]["metadata"]["retriever_backend"] == data["retriever_backend"]
    assert (
        messages[1]["metadata"]["retriever_backend_source"]
        == data["retriever_backend_source"]
    )
    assert messages[1]["metadata"]["citations"] == data["citations"]
    assert messages[1]["metadata"]["steps"] == data["steps"]

    connection = create_connection(str(database_path))

    conversation = find_conversation_by_id(
        connection,
        conversation_id,
    )

    connection.close()

    assert data["conversation_summary"] == "最近问题：公司有没有股票期权？。"
    assert conversation["summary"] == "最近问题：公司有没有股票期权？。"


def test_langgraph_agent_conversation_chat_returns_404_when_conversation_not_found(
    tmp_path,
):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/langgraph-agent/conversations/999/chat",
        json={"question": "公司有没有股票期权？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "会话不存在。"


def test_langgraph_agent_conversation_chat_uses_saved_messages(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    connection.close()

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = (
        lambda: lambda prompt: "这是模型回答"
    )

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "员工手册阅读会话"},
    )

    conversation_id = conversation_response.json()["id"]

    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    add_message(
        connection,
        conversation_id=conversation_id,
        role="user",
        content="查看员工手册的片段",
    )

    add_message(
        connection,
        conversation_id=conversation_id,
        role="assistant",
        content="员工手册 的片段如下：\n[1] 新员工入职后需要在 30 天内完成安全培训。",
    )

    connection.close()

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "查看这份文档的片段"},
    )

    messages_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert messages_response.status_code == 200

    data = response.json()
    messages = messages_response.json()

    assert data["intent"] == "read_document"
    assert data["document_title"] == "员工手册"
    assert data["steps"][2]["tool"] == "extract_document_title"
    assert data["steps"][2]["observation"]["source"] == "messages"
    assert "新员工入职后需要在 30 天内完成安全培训。" in data["answer"]
    assert len(data["citations"]) == 1

    assert len(messages) == 4
    assert messages[0]["content"] == "查看员工手册的片段"
    assert messages[1]["content"] == "员工手册 的片段如下：\n[1] 新员工入职后需要在 30 天内完成安全培训。"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "查看这份文档的片段"
    assert messages[3]["role"] == "assistant"
    assert messages[3]["content"] == data["answer"]


def test_langgraph_agent_conversation_chat_uses_citation_metadata(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="新员工入职后需要在 30 天内完成安全培训。",
    )

    connection.close()

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = (
        lambda: lambda prompt: "这是模型回答"
    )

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "metadata 引用测试"},
    )

    conversation_id = conversation_response.json()["id"]

    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    add_message(
        connection,
        conversation_id=conversation_id,
        role="assistant",
        content="这是一段没有固定片段格式的回答。",
        metadata={
            "citations": [
                {
                    "title": "员工手册",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "path": "sqlite://1",
                }
            ]
        },
    )

    connection.close()

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "查看这份文档的片段"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "read_document"
    assert data["document_title"] == "员工手册"
    assert data["steps"][2]["observation"]["source"] == "messages"
    assert "新员工入职后需要在 30 天内完成安全培训。" in data["answer"]


def test_langgraph_agent_conversation_chat_uses_context_for_search(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工每天需要完成 8 小时工作。",
    )

    overtime_document = insert_document_to_db(
        connection,
        title="加班制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=overtime_document["id"],
        text="员工加班需要提前提交申请。",
    )

    device_document = insert_document_to_db(
        connection,
        title="设备借用制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=device_document["id"],
        text="员工借用公司设备需要提交申请。",
    )

    connection.close()

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = (
        lambda: lambda prompt: "员工每天需要完成 8 小时工作。"
    )

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "上下文检索测试"},
    )

    conversation_id = conversation_response.json()["id"]

    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    add_message(
        connection,
        conversation_id=conversation_id,
        role="assistant",
        content="新员工需要在入职后 30 天内完成安全培训。",
        metadata={
            "citations": [
                {
                    "title": "员工手册",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "path": "sqlite://1",
                }
            ]
        },
    )

    connection.close()

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "每天需要工作多久？"},
        params={"mode": "vector", "min_score": 0.0},
    )

    messages_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert messages_response.status_code == 200

    data = response.json()
    messages = messages_response.json()

    assert data["intent"] == "answer_question"
    assert data["answer"] == "员工每天需要完成 8 小时工作。"
    assert len(data["citations"]) == 1
    assert data["citations"][0]["title"] == "员工手册"
    assert data["steps"][2]["input"]["contextual_question"] == "员工手册 每天需要工作多久？"
    assert data["steps"][2]["input"]["context_document_title"] == "员工手册"

    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == data["answer"]
    assert messages[-1]["metadata"]["citations"] == data["citations"]


def test_langgraph_agent_conversation_chat_avoids_unrelated_context(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工每天需要完成 8 小时工作。",
    )

    connection.close()

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "防止上下文污染测试"},
    )

    conversation_id = conversation_response.json()["id"]

    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    add_message(
        connection,
        conversation_id=conversation_id,
        role="assistant",
        content="新员工需要在入职后 30 天内完成安全培训。",
        metadata={
            "citations": [
                {
                    "title": "员工手册",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "path": "sqlite://1",
                }
            ]
        },
    )

    connection.close()

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "报销需要什么材料？"},
        params={"mode": "vector", "min_score": 0.0},
    )

    messages_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert messages_response.status_code == 200

    data = response.json()
    messages = messages_response.json()

    assert data["intent"] == "answer_question"
    assert data["context_document_title"] == "员工手册"
    assert data["has_valid_context"] is False
    assert data["citations"] == []
    assert "暂时无法回答" in data["answer"]

    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["metadata"]["citations"] == []


def test_conversation_list_shows_updated_summary_after_agent_chat(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = (
        lambda: lambda prompt: "知识库中没有找到相关资料，暂时无法回答。"
    )

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "长期记忆测试"},
    )

    conversation_id = conversation_response.json()["id"]

    chat_response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "公司有没有股票期权？"},
    )

    conversations_response = client.get("/api/v1/conversations")

    app.dependency_overrides.clear()

    assert chat_response.status_code == 200
    assert conversations_response.status_code == 200

    chat_data = chat_response.json()
    conversations = conversations_response.json()

    assert chat_data["conversation_summary"] == "最近问题：公司有没有股票期权？。"
    assert conversations == [
        {
            "id": conversation_id,
            "title": "长期记忆测试",
            "summary": "最近问题：公司有没有股票期权？。",
        }
    ]


def test_langgraph_agent_conversation_chat_receives_existing_summary(tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "已有摘要会话"},
    )

    conversation_id = conversation_response.json()["id"]

    connection = create_connection(str(database_path))

    create_conversations_table(connection)
    create_messages_table(connection)

    from backend.services.sqlite_conversation_repository import (
        update_conversation_summary,
    )

    update_conversation_summary(
        connection,
        conversation_id=conversation_id,
        summary="最近问题：员工每天需要工作多久？；最近引用文档：员工手册。",
    )

    connection.close()

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "公司有没有股票期权？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["conversation_summary"] == "最近问题：公司有没有股票期权？。"


def test_langgraph_agent_conversation_chat_does_not_use_summary_for_unrelated_question(
    tmp_path,
):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)
    create_conversations_table(connection)
    create_messages_table(connection)

    document = insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工每天需要完成 8 小时工作。",
    )

    connection.close()

    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "summary 防污染测试"},
    )

    conversation_id = conversation_response.json()["id"]

    connection = create_connection(str(database_path))

    from backend.services.sqlite_conversation_repository import (
        update_conversation_summary,
    )

    update_conversation_summary(
        connection,
        conversation_id=conversation_id,
        summary="最近问题：每天需要工作多久？；最近引用文档：员工手册。",
    )

    connection.close()

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        json={"question": "报销需要什么材料？"},
        params={"mode": "vector", "min_score": 0.0},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "answer_question"
    assert data["contextual_question"] == "员工手册 报销需要什么材料？"
    assert data["context_document_title"] == "员工手册"
    assert data["has_valid_context"] is False
    assert data["citations"] == []
    assert "暂时无法回答" in data["answer"]
    assert data["steps"][0]["tool"] == "load_conversation_summary"
    assert data["steps"][0]["input"]["has_summary"] is True
    assert data["steps"][2]["input"]["contextual_question"] == "员工手册 报销需要什么材料？"
    assert data["steps"][3]["tool"] == "validate_context_node"
    assert data["steps"][3]["observation"]["has_valid_context"] is False
    assert data["steps"][4]["tool"] == "refuse_answer_tool"


def test_langgraph_agent_stream_endpoint_returns_sse(monkeypatch, tmp_path):
    database_path = tmp_path / "test.db"

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_agent_generator] = (
        lambda: lambda prompt: "这是流式回答"
    )

    response = client.post(
        "/api/v1/langgraph-agent/chat/stream",
        json={"question": "知识库里有哪些文档？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    text = response.text

    assert 'data: {"type": "delta"' in text
    assert "这是流式回答" in text or "当前知识库文档" in text
    assert 'data: {"type": "metadata"' in text
    assert '"retriever_backend_source": "default"' in text
    assert 'data: {"type": "done"}' in text


class FakePostgresqlConnection:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_langgraph_agent_chat_endpoint_passes_postgresql_connection(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "test.db"
    fake_connection = FakePostgresqlConnection()
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return fake_connection

    def fake_run_langgraph_agent(**kwargs):
        captured["question"] = kwargs["question"]
        captured["database_path"] = kwargs["database_path"]
        captured["retriever_backend"] = kwargs["retriever_backend"]
        captured["retriever_backend_source"] = kwargs["retriever_backend_source"]
        captured["postgresql_connection"] = kwargs["postgresql_connection"]

        return {
            "question": kwargs["question"],
            "intent": "answer_question",
            "keyword": "安全培训",
            "contextual_question": kwargs["question"],
            "context_document_title": "",
            "snippets": [
                {
                    "title": "员工手册",
                    "path": "postgresql://chunk/2",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "score": 0.9,
                }
            ],
            "has_valid_context": True,
            "document_title": "",
            "document": None,
            "document_match_type": None,
            "missing_field": "",
            "answer": "新员工需要在入职后 30 天内完成安全培训。",
            "citations": [
                {
                    "title": "员工手册",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "path": "postgresql://chunk/2",
                }
            ],
            "steps": [],
            "database_path": kwargs["database_path"],
            "top_k": kwargs["top_k"],
            "mode": kwargs["mode"],
            "min_score": kwargs["min_score"],
            "retriever_backend": kwargs["retriever_backend"],
            "retriever_backend_source": kwargs["retriever_backend_source"],
            "timeout_seconds": kwargs["timeout_seconds"],
            "is_timeout": False,
            "is_fallback": False,
        }

    monkeypatch.setattr(
        "backend.routers.langgraph_agent.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.langgraph_agent.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    response = client.post(
        "/api/v1/langgraph-agent/chat",
        params={"retriever_backend": "postgresql"},
        json={"question": "新员工什么时候完成安全培训？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["question"] == "新员工什么时候完成安全培训？"
    assert captured["database_path"] == str(database_path)
    assert captured["retriever_backend"] == "postgresql"
    assert captured["retriever_backend_source"] == "override"
    assert captured["postgresql_connection"] == fake_connection
    assert fake_connection.closed is True

    assert data["retriever_backend"] == "postgresql"
    assert data["retriever_backend_source"] == "override"
    assert data["snippets"][0]["path"] == "postgresql://chunk/2"


def test_langgraph_agent_conversation_chat_accepts_postgresql_retriever(
    monkeypatch,
    tmp_path,
):
    database_path = tmp_path / "test.db"
    fake_connection = FakePostgresqlConnection()
    captured = {}

    def fake_connect(database_url: str):
        captured["database_url"] = database_url
        return fake_connection

    def fake_run_langgraph_agent(**kwargs):
        captured["question"] = kwargs["question"]
        captured["database_path"] = kwargs["database_path"]
        captured["retriever_backend"] = kwargs["retriever_backend"]
        captured["retriever_backend_source"] = kwargs["retriever_backend_source"]
        captured["postgresql_connection"] = kwargs["postgresql_connection"]
        captured["messages"] = kwargs["messages"]
        captured["conversation_summary"] = kwargs["conversation_summary"]

        return {
            "question": kwargs["question"],
            "intent": "answer_question",
            "keyword": "每天工作多久",
            "contextual_question": kwargs["question"],
            "context_document_title": "",
            "snippets": [
                {
                    "title": "员工手册",
                    "path": "postgresql://chunk/2",
                    "text": "员工每天需要完成 8 小时工作。",
                    "score": 0.9,
                }
            ],
            "has_valid_context": True,
            "document_title": "",
            "document": None,
            "document_match_type": None,
            "missing_field": "",
            "answer": "员工每天需要完成 8 小时工作。",
            "citations": [
                {
                    "title": "员工手册",
                    "text": "员工每天需要完成 8 小时工作。",
                    "path": "postgresql://chunk/2",
                }
            ],
            "steps": [],
            "database_path": kwargs["database_path"],
            "top_k": kwargs["top_k"],
            "mode": kwargs["mode"],
            "min_score": kwargs["min_score"],
            "retriever_backend": kwargs["retriever_backend"],
            "retriever_backend_source": kwargs["retriever_backend_source"],
            "timeout_seconds": kwargs["timeout_seconds"],
            "is_timeout": False,
            "is_fallback": False,
        }

    monkeypatch.setattr(
        "backend.routers.langgraph_agent.psycopg.connect",
        fake_connect,
    )
    monkeypatch.setattr(
        "backend.routers.langgraph_agent.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    app.dependency_overrides[get_database_path] = lambda: str(database_path)
    app.dependency_overrides[get_langgraph_postgresql_database_url] = lambda: (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    conversation_response = client.post(
        "/api/v1/conversations",
        json={"title": "PostgreSQL 会话检索"},
    )

    conversation_id = conversation_response.json()["id"]

    response = client.post(
        f"/api/v1/langgraph-agent/conversations/{conversation_id}/chat",
        params={
            "retriever_backend": "postgresql",
            "top_k": 2,
            "mode": "precomputed_embedding",
            "min_score": 0.6,
        },
        json={"question": "员工每天需要工作多久？"},
    )

    messages_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages"
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert messages_response.status_code == 200

    data = response.json()
    messages = messages_response.json()

    assert captured["database_url"] == (
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )
    assert captured["question"] == "员工每天需要工作多久？"
    assert captured["database_path"] == str(database_path)
    assert captured["retriever_backend"] == "postgresql"
    assert captured["retriever_backend_source"] == "override"
    assert captured["postgresql_connection"] == fake_connection
    assert captured["messages"] == []
    assert captured["conversation_summary"] == ""
    assert fake_connection.closed is True

    assert data["conversation_id"] == conversation_id
    assert data["retriever_backend"] == "postgresql"
    assert data["retriever_backend_source"] == "override"
    assert data["snippets"][0]["path"] == "postgresql://chunk/2"
    assert len(data["saved_messages"]) == 2

    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "员工每天需要工作多久？"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "员工每天需要完成 8 小时工作。"
    assert messages[1]["metadata"]["citations"][0]["path"] == "postgresql://chunk/2"
