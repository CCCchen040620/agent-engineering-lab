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
    assert data["steps"][0]["tool"] == "decide_agent_intent"
    assert data["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert data["steps"][2]["tool"] == "validate_context_node"
    assert data["steps"][2]["observation"]["has_valid_context"] is True
    assert data["steps"][3]["tool"] == "answer_with_context_tool"


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
    assert data["steps"][0]["tool"] == "decide_agent_intent"
    assert data["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert data["steps"][2]["tool"] == "validate_context_node"
    assert data["steps"][2]["observation"]["has_valid_context"] is False
    assert data["steps"][3]["tool"] == "refuse_answer_tool"