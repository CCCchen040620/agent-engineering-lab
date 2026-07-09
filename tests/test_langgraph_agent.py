from backend.services.conversation_context_service import (
    calculate_question_similarity,
    is_contextual_context_valid,
)
from backend.services.langgraph_agent import run_langgraph_agent
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)


def test_calculate_question_similarity():
    score = calculate_question_similarity(
        question="每天需要工作多久？",
        text="员工每天需要完成 8 小时工作。",
    )

    assert score >= 0.3


def test_is_contextual_context_valid_returns_true_for_related_context():
    snippets = [
        {
            "title": "员工手册",
            "text": "员工每天需要完成 8 小时工作。",
            "score": 0.8,
        }
    ]

    result = is_contextual_context_valid(
        question="每天需要工作多久？",
        context_document_title="员工手册",
        snippets=snippets,
    )

    assert result is True


def test_is_contextual_context_valid_returns_false_for_unrelated_context():
    snippets = [
        {
            "title": "员工手册",
            "text": "员工每天需要完成 8 小时工作。",
            "score": 0.8,
        }
    ]

    result = is_contextual_context_valid(
        question="报销需要什么材料？",
        context_document_title="员工手册",
        snippets=snippets,
    )

    assert result is False


def test_run_langgraph_agent_lists_documents(tmp_path):
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

    result = run_langgraph_agent(
        question="知识库里有哪些文档？",
        database_path=str(database_path),
    )

    assert result["intent"] == "list_documents"
    assert result["keyword"] == "文档列表"
    assert "员工手册" in result["answer"]
    assert "请假制度" in result["answer"]
    assert result["citations"] == []

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][0]["observation"]["intent"] == "list_documents"
    assert result["steps"][1]["tool"] == "list_documents_tool"
    assert result["steps"][1]["observation"]["document_count"] == 2


def test_run_langgraph_agent_answers_with_context(tmp_path):
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

    result = run_langgraph_agent(
        question="新员工什么时候完成安全培训？",
        database_path=str(database_path),
        mode="keyword",
        generator=fake_generator,
    )

    assert result["intent"] == "answer_question"
    assert result["keyword"] == "安全培训"
    assert result["answer"] == "新员工需要在入职后 30 天内完成安全培训。"
    assert len(result["citations"]) == 1

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert result["steps"][1]["observation"]["result_count"] == 1
    assert result["steps"][1]["next_action"] == "validate_context"
    assert result["steps"][3]["tool"] == "answer_with_context_tool"
    assert result["has_valid_context"] is True
    assert result["steps"][2]["tool"] == "validate_context_node"
    assert result["steps"][2]["observation"]["has_valid_context"] is True
    assert result["steps"][3]["tool"] == "answer_with_context_tool"


def test_run_langgraph_agent_refuses_without_context(tmp_path):
    database_path = tmp_path / "test.db"

    result = run_langgraph_agent(
        question="公司有没有股票期权？",
        database_path=str(database_path),
        mode="keyword",
    )

    assert result["intent"] == "answer_question"
    assert result["keyword"] == "股票期权"
    assert result["citations"] == []

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][1]["tool"] == "search_knowledge_base_tool"
    assert result["steps"][1]["observation"]["result_count"] == 0
    assert result["steps"][1]["next_action"] == "validate_context"
    assert result["has_valid_context"] is False
    assert result["steps"][2]["tool"] == "validate_context_node"
    assert result["steps"][2]["observation"]["has_valid_context"] is False
    assert result["steps"][3]["tool"] == "refuse_answer_tool"


def test_run_langgraph_agent_refuses_when_snippets_do_not_contain_keyword(tmp_path):
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

    result = run_langgraph_agent(
        question="公司有没有股票期权？",
        database_path=str(database_path),
        mode="vector",
        min_score=0.0,
    )

    assert result["keyword"] == "股票期权"
    assert len(result["snippets"]) > 0
    assert result["has_valid_context"] is False
    assert result["citations"] == []
    assert result["steps"][2]["tool"] == "validate_context_node"
    assert result["steps"][2]["observation"]["has_valid_context"] is False
    assert result["steps"][3]["tool"] == "refuse_answer_tool"


def test_run_langgraph_agent_reads_document_chunks(tmp_path):
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

    result = run_langgraph_agent(
        question="查看员工手册的片段",
        database_path=str(database_path),
    )

    assert result["intent"] == "read_document"
    assert result["keyword"] == "员工手册"
    assert result["document_title"] == "员工手册"
    assert "员工每天需要完成 8 小时工作。" in result["answer"]
    assert "新员工需要完成安全培训。" in result["answer"]
    assert len(result["citations"]) == 2

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][0]["observation"]["intent"] == "read_document"
    assert result["steps"][1]["tool"] == "extract_document_title"
    assert result["steps"][1]["observation"]["source"] == "question"
    assert result["steps"][2]["tool"] == "find_document_by_title_tool"
    assert result["steps"][2]["observation"]["found"] is True
    assert result["steps"][3]["tool"] == "read_document_chunks_tool"


def test_run_langgraph_agent_asks_clarification_when_document_title_is_missing(tmp_path):
    database_path = tmp_path / "test.db"

    result = run_langgraph_agent(
        question="查看这份文档的片段",
        database_path=str(database_path),
    )

    assert result["intent"] == "read_document"
    assert result["keyword"] == "文档标题"
    assert result["document_title"] == ""
    assert result["citations"] == []
    assert "文档标题" in result["answer"]

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][1]["tool"] == "extract_document_title"
    assert result["steps"][1]["observation"]["source"] == "none"
    assert result["steps"][1]["next_action"] == "ask_clarification_node"
    assert result["steps"][2]["tool"] == "ask_clarification_tool"


def test_run_langgraph_agent_asks_clarification_when_document_is_not_found(tmp_path):
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

    result = run_langgraph_agent(
        question="查看不存在文档的片段",
        database_path=str(database_path),
    )

    assert result["intent"] == "read_document"
    assert result["keyword"] == "不存在文档"
    assert result["citations"] == []
    assert "正确的文档标题" in result["answer"]

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][1]["tool"] == "extract_document_title"
    assert result["steps"][2]["tool"] == "find_document_by_title_tool"
    assert result["steps"][2]["observation"]["found"] is False
    assert result["steps"][3]["tool"] == "ask_clarification_tool"


def test_run_langgraph_agent_uses_messages_to_infer_document_title(tmp_path):
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

    messages = [
        {
            "role": "user",
            "content": "查看员工手册的片段",
        },
        {
            "role": "assistant",
            "content": "员工手册 的片段如下：\n[1] 新员工入职后需要在 30 天内完成安全培训。",
        },
    ]

    result = run_langgraph_agent(
        question="查看这份文档的片段",
        database_path=str(database_path),
        messages=messages,
    )

    assert result["intent"] == "read_document"
    assert result["document_title"] == "员工手册"
    assert "新员工入职后需要在 30 天内完成安全培训。" in result["answer"]
    assert len(result["citations"]) == 1

    assert result["steps"][0]["tool"] == "decide_agent_intent"
    assert result["steps"][1]["tool"] == "extract_document_title"
    assert result["steps"][1]["observation"]["source"] == "messages"
    assert result["steps"][1]["observation"]["document_title"] == "员工手册"
    assert result["steps"][2]["tool"] == "find_document_by_title_tool"
    assert result["steps"][3]["tool"] == "read_document_chunks_tool"


def test_run_langgraph_agent_uses_contextual_question_for_search(tmp_path):
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

    messages = [
        {
            "role": "assistant",
            "content": "新员工需要在入职后 30 天内完成安全培训。",
            "metadata": {
                "citations": [
                    {
                        "title": "员工手册",
                        "text": "新员工入职后需要在 30 天内完成安全培训。",
                        "path": "sqlite://1",
                    }
                ]
            },
        }
    ]

    def fake_generator(prompt: str) -> str:
        assert "员工每天需要完成 8 小时工作。" in prompt
        return "员工每天需要完成 8 小时工作。"

    result = run_langgraph_agent(
        question="每天需要工作多久？",
        database_path=str(database_path),
        mode="vector",
        min_score=0.0,
        generator=fake_generator,
        messages=messages,
    )

    assert result["intent"] == "answer_question"
    assert result["answer"] == "员工每天需要完成 8 小时工作。"
    assert len(result["citations"]) == 1
    assert result["citations"][0]["title"] == "员工手册"
    assert result["steps"][1]["input"]["contextual_question"] == "员工手册 每天需要工作多久？"
    assert result["steps"][1]["input"]["context_document_title"] == "员工手册"
    assert result["has_valid_context"] is True


def test_run_langgraph_agent_does_not_use_context_when_similarity_is_zero(tmp_path):
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

    messages = [
        {
            "role": "assistant",
            "content": "新员工需要在入职后 30 天内完成安全培训。",
            "metadata": {
                "citations": [
                    {
                        "title": "员工手册",
                        "text": "新员工入职后需要在 30 天内完成安全培训。",
                        "path": "sqlite://1",
                    }
                ]
            },
        }
    ]

    result = run_langgraph_agent(
        question="报销需要什么材料？",
        database_path=str(database_path),
        mode="vector",
        min_score=0.0,
        messages=messages,
    )

    assert result["intent"] == "answer_question"
    assert result["context_document_title"] == "员工手册"
    assert result["has_valid_context"] is False
    assert result["citations"] == []
    assert "暂时无法回答" in result["answer"]