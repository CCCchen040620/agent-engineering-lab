from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path
from backend.routers.langgraph_agent import get_langgraph_agent_generator
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