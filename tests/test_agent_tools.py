from backend.services.agent_tools import (
    list_documents_tool,
    read_document_chunks_tool,
    search_knowledge_base_tool,
    answer_with_context_tool,
)
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)


def test_list_documents_tool(tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)

    insert_document_to_db(
        connection,
        title="员工手册",
        file_type="md",
        chunk_count=12,
        is_indexed=True,
    )

    connection.close()

    result = list_documents_tool(str(database_path))

    assert result["count"] == 1
    assert result["documents"][0]["title"] == "员工手册"
    assert result["documents"][0]["is_indexed"] == True


def test_read_document_chunks_tool(tmp_path):
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

    result = read_document_chunks_tool(
        document_id=document["id"],
        database_path=str(database_path),
    )

    assert result["found"] == True
    assert result["document"]["title"] == "员工手册"
    assert len(result["chunks"]) == 2
    assert result["chunks"][0]["text"] == "员工每天需要完成 8 小时工作。"


def test_read_document_chunks_tool_returns_not_found(tmp_path):
    database_path = tmp_path / "test.db"

    result = read_document_chunks_tool(
        document_id=999,
        database_path=str(database_path),
    )

    assert result["found"] == False
    assert result["document"] is None
    assert result["chunks"] == []


def test_search_knowledge_base_tool(tmp_path):
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

    result = search_knowledge_base_tool(
        question="新员工什么时候完成安全培训？",
        database_path=str(database_path),
        mode="keyword",
    )

    assert result["question"] == "新员工什么时候完成安全培训？"
    assert result["keyword"] == "安全培训"
    assert result["count"] == 1
    assert result["snippets"][0]["title"] == "员工手册"
    assert result["snippets"][0]["text"] == "新员工入职后需要在 30 天内完成安全培训。"


def test_search_knowledge_base_tool_returns_empty_result(tmp_path):
    database_path = tmp_path / "test.db"

    result = search_knowledge_base_tool(
        question="公司有没有股票期权？",
        database_path=str(database_path),
        mode="keyword",
    )

    assert result["question"] == "公司有没有股票期权？"
    assert result["keyword"] == "股票期权"
    assert result["count"] == 0
    assert result["snippets"] == []


def test_answer_with_context_tool():
    snippets = [
        {
            "title": "员工手册",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
            "path": "sqlite://1",
        }
    ]

    def fake_generator(prompt: str) -> str:
        assert "新员工入职后需要在 30 天内完成安全培训。" in prompt
        assert "新员工什么时候完成安全培训？" in prompt

        return "新员工需要在入职后 30 天内完成安全培训。"

    result = answer_with_context_tool(
        question="新员工什么时候完成安全培训？",
        snippets=snippets,
        generator=fake_generator,
    )

    assert result["question"] == "新员工什么时候完成安全培训？"
    assert result["answer"] == "新员工需要在入职后 30 天内完成安全培训。"
    assert len(result["citations"]) == 1
    assert result["citations"][0]["title"] == "员工手册"


def test_answer_with_context_tool_refuses_without_snippets():
    result = answer_with_context_tool(
        question="公司有没有股票期权？",
        snippets=[],
    )

    assert result["answer"] == "知识库中没有找到相关资料，暂时无法回答。"
    assert result["citations"] == []


def test_answer_with_context_tool_handles_generator_error():
    snippets = [
        {
            "title": "员工手册",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
            "path": "sqlite://1",
        }
    ]

    def broken_generator(prompt: str) -> str:
        raise RuntimeError("model timeout")

    result = answer_with_context_tool(
        question="新员工什么时候完成安全培训？",
        snippets=snippets,
        generator=broken_generator,
    )

    assert result["answer"] == "本地模型暂时不可用，请稍后再试。"
    assert len(result["citations"]) == 1