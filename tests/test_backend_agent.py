from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.db_documents import get_database_path
from backend.routers.agent import get_agent_generator
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)


client = TestClient(app)


def test_agent_chat_endpoint_answers_with_context(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_database_path] = lambda: str(database_path)

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

    app.dependency_overrides[get_agent_generator] = lambda: fake_generator

    response = client.post(
        "/api/v1/agent/chat",
        json={"question": "新员工什么时候完成安全培训？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["keyword"] == "安全培训"
    assert len(data["citations"]) == 1
    assert data["answer"] == "新员工需要在入职后 30 天内完成安全培训。"
    assert data["steps"][0]["step"] == 1
    assert data["steps"][0]["tool"] == "decide_agent_intent"
    assert data["steps"][0]["input"]["question"] == "新员工什么时候完成安全培训？"
    assert data["steps"][0]["observation"]["intent"] == "answer_question"
    assert data["steps"][0]["next_action"] == "search_knowledge_base"

    assert data["steps"][1]["step"] == 2
    assert data["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert data["steps"][1]["input"]["question"] == "新员工什么时候完成安全培训？"
    assert data["steps"][1]["input"]["mode"] == "keyword"
    assert data["steps"][1]["observation"]["keyword"] == "安全培训"
    assert data["steps"][1]["observation"]["result_count"] == 1
    assert data["steps"][1]["next_action"] == "answer_with_context"

    assert data["steps"][2]["step"] == 3
    assert data["steps"][2]["tool"] == "answer_with_context_tool"
    assert data["steps"][2]["input"]["snippet_count"] == 1
    assert data["steps"][2]["observation"]["citation_count"] == 1
    assert data["steps"][2]["next_action"] == "finish"



def test_agent_chat_endpoint_refuses_without_context(tmp_path):
    database_path = tmp_path / "test.db"
    app.dependency_overrides[get_database_path] = lambda: str(database_path)

    response = client.post(
        "/api/v1/agent/chat",
        json={"question": "公司有没有股票期权？"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "知识库中没有找到相关资料，暂时无法回答。"
    assert data["citations"] == []
    assert data["steps"][0]["step"] == 1
    assert data["steps"][0]["tool"] == "decide_agent_intent"
    assert data["steps"][0]["observation"]["intent"] == "answer_question"
    assert data["steps"][0]["next_action"] == "search_knowledge_base"

    assert data["steps"][1]["step"] == 2
    assert data["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert data["steps"][1]["observation"]["result_count"] == 0
    assert data["steps"][1]["next_action"] == "refuse"

    assert data["steps"][2]["step"] == 3
    assert data["steps"][2]["tool"] == "refuse_answer_tool"
    assert data["steps"][2]["input"]["snippet_count"] == 0
    assert data["steps"][2]["observation"]["citation_count"] == 0
    assert data["steps"][2]["next_action"] == "finish"