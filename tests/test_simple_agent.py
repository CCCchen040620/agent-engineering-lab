from backend.services.simple_agent import decide_agent_intent, run_simple_agent
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)


def test_run_simple_agent_answers_with_context(tmp_path):
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

    result = run_simple_agent(
        question="新员工什么时候完成安全培训？",
        database_path=str(database_path),
        mode="keyword",
        generator=fake_generator,
    )

    assert result["keyword"] == "安全培训"
    assert result["answer"] == "新员工需要在入职后 30 天内完成安全培训。"
    assert len(result["citations"]) == 1
    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][0]["observation"]["intent"] == "answer_question"
    assert result["steps"][0]["next_action"] == "search_knowledge_base"

    assert result["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert result["steps"][1]["observation"]["result_count"] == 1
    assert result["steps"][1]["next_action"] == "answer_with_context"

    assert result["steps"][2]["tool"] == "answer_with_context_tool"
    assert result["steps"][2]["input"]["snippet_count"] == 1
    assert result["steps"][2]["observation"]["citation_count"] == 1
    assert result["steps"][2]["next_action"] == "finish"


def test_run_simple_agent_refuses_without_context(tmp_path):
    database_path = tmp_path / "test.db"

    result = run_simple_agent(
        question="公司有没有股票期权？",
        database_path=str(database_path),
        mode="keyword",
    )

    assert result["keyword"] == "股票期权"
    assert result["answer"] == "知识库中没有找到相关资料，暂时无法回答。"
    assert result["citations"] == []
    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][0]["observation"]["intent"] == "answer_question"
    assert result["steps"][0]["next_action"] == "search_knowledge_base"

    assert result["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert result["steps"][1]["observation"]["result_count"] == 0
    assert result["steps"][1]["next_action"] == "refuse"

    assert result["steps"][2]["tool"] == "refuse_answer_tool"
    assert result["steps"][2]["input"]["snippet_count"] == 0
    assert result["steps"][2]["observation"]["citation_count"] == 0
    assert result["steps"][2]["next_action"] == "finish"


def test_decide_agent_intent_returns_list_documents():
    assert decide_agent_intent("知识库里有哪些文档？") == "list_documents"
    assert decide_agent_intent("请列出文档") == "list_documents"
    assert decide_agent_intent("查看文档列表") == "list_documents"


def test_decide_agent_intent_returns_answer_question():
    assert decide_agent_intent("新员工什么时候完成安全培训？") == "answer_question"


def test_run_simple_agent_lists_documents(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    insert_document_to_db(
        connection,
        title="请假制度",
        file_type="md",
        chunk_count=1,
        is_indexed=True,
    )

    connection.close()

    result = run_simple_agent(
        question="知识库里有哪些文档？",
        database_path=str(database_path),
    )

    assert result["keyword"] == "文档列表"
    assert "员工手册" in result["answer"]
    assert "请假制度" in result["answer"]
    assert result["citations"] == []
    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][0]["observation"]["intent"] == "list_documents"
    assert result["steps"][1]["tool"] == "list_documents_tool"
    assert result["steps"][1]["observation"]["document_count"] == 2
    assert result["steps"][1]["next_action"] == "finish"