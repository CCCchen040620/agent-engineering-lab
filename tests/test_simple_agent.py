from pathlib import Path
from backend.services.simple_agent import (
    decide_agent_intent,
    extract_document_title,
    run_simple_agent,
)
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


def test_decide_agent_intent_returns_read_document():
    assert decide_agent_intent("查看员工手册的片段") == "read_document"
    assert decide_agent_intent("读取请假制度的内容") == "read_document"
    assert decide_agent_intent("员工手册有哪些内容") == "read_document"


def test_extract_document_title():
    assert extract_document_title("查看员工手册的片段") == "员工手册"
    assert extract_document_title("读取请假制度的内容") == "请假制度"
    assert extract_document_title("员工手册有哪些内容") == "员工手册"


def test_extract_document_title_returns_empty_when_missing_title():
    assert extract_document_title("查看这份文档的片段") == ""


def test_run_simple_agent_reads_document_chunks(tmp_path):
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

    result = run_simple_agent(
        question="查看员工手册的片段",
        database_path=str(database_path),
    )

    assert result["keyword"] == "员工手册"
    assert "员工每天需要完成 8 小时工作。" in result["answer"]
    assert "新员工需要完成安全培训。" in result["answer"]
    assert len(result["citations"]) == 2

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][0]["observation"]["intent"] == "read_document"

    assert result["steps"][1]["tool"] == "extract_document_title"
    assert result["steps"][1]["observation"]["document_title"] == "员工手册"

    assert result["steps"][2]["tool"] == "find_document_by_title_tool"
    assert result["steps"][2]["observation"]["found"] == True
    assert result["steps"][2]["observation"]["match_type"] == "exact"

    assert result["steps"][3]["tool"] == "read_document_chunks_tool"
    assert result["steps"][3]["observation"]["chunk_count"] == 2


def test_run_simple_agent_asks_clarification_when_document_title_is_missing(tmp_path):
    database_path = tmp_path / "test.db"

    result = run_simple_agent(
        question="查看这份文档的片段",
        database_path=str(database_path),
    )

    assert result["keyword"] == "文档标题"
    assert result["answer"] == "请补充文档标题。"
    assert result["citations"] == []
    assert result["steps"][0]["observation"]["intent"] == "read_document"
    assert result["steps"][2]["tool"] == "ask_clarification_tool"


def test_run_simple_agent_reads_document_chunks_with_partial_title(tmp_path):
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

    result = run_simple_agent(
        question="查看手册的片段",
        database_path=str(database_path),
    )

    assert result["keyword"] == "手册"
    assert "员工每天需要完成 8 小时工作。" in result["answer"]
    assert result["steps"][2]["tool"] == "find_document_by_title_tool"
    assert result["steps"][2]["observation"]["found"] == True
    assert result["steps"][2]["observation"]["match_type"] == "contains"


def test_run_simple_agent_asks_clarification_when_document_is_not_found(tmp_path):
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

    connection.close()

    result = run_simple_agent(
        question="查看不存在文档的片段",
        database_path=str(database_path),
    )

    assert result["keyword"] == "不存在文档"
    assert result["answer"] == "请补充正确的文档标题。"
    assert result["steps"][2]["tool"] == "find_document_by_title_tool"
    assert result["steps"][2]["observation"]["found"] == False
    assert result["steps"][2]["observation"]["match_type"] is None
    assert result["steps"][3]["tool"] == "ask_clarification_tool"


def test_simple_agent_uses_config_database_path():
    source = Path("backend/services/simple_agent.py").read_text(encoding="utf-8")

    assert "DATABASE_PATH" in source
    assert "SQLITE_DATABASE_PATH" not in source
    assert "week04.settings" not in source