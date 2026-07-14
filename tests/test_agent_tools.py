from pathlib import Path
from backend.services.agent_tools import (
    ask_clarification_tool,
    list_documents_tool,
    find_document_by_title_tool,
    read_document_chunks_tool,
    search_knowledge_base_tool,
    answer_with_context_tool,
    refuse_answer_tool,
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


class FakePostgresqlConnection:
    pass


def test_search_knowledge_base_tool_can_use_unified_retriever(monkeypatch):
    captured = {}

    def fake_retrieve_rag_snippets(
        question: str,
        backend: str,
        sqlite_database_path: str,
        postgresql_connection,
        top_k: int,
        mode: str,
        min_score: float,
    ):
        captured["question"] = question
        captured["backend"] = backend
        captured["sqlite_database_path"] = sqlite_database_path
        captured["postgresql_connection"] = postgresql_connection
        captured["top_k"] = top_k
        captured["mode"] = mode
        captured["min_score"] = min_score

        return [
            {
                "title": "员工手册",
                "path": "postgresql://chunk/2",
                "text": "员工每天需要完成 8 小时工作。",
                "score": 0.866,
            }
        ]

    monkeypatch.setattr(
        "backend.services.agent_tools.retrieve_rag_snippets",
        fake_retrieve_rag_snippets,
    )

    connection = FakePostgresqlConnection()

    result = search_knowledge_base_tool(
        question="员工每天需要工作多久？",
        retriever_backend="postgresql",
        postgresql_connection=connection,
        top_k=2,
        mode="precomputed_embedding",
        min_score=0.6,
    )

    assert captured == {
        "question": "员工每天需要工作多久？",
        "backend": "postgresql",
        "sqlite_database_path": "data/app.db",
        "postgresql_connection": connection,
        "top_k": 2,
        "mode": "precomputed_embedding",
        "min_score": 0.6,
    }

    assert result == {
        "question": "员工每天需要工作多久？",
        "keyword": "员工每天需要工作多久？",
        "snippets": [
            {
                "title": "员工手册",
                "path": "postgresql://chunk/2",
                "text": "员工每天需要完成 8 小时工作。",
                "score": 0.866,
            }
        ],
        "count": 1,
    }

    
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
    assert result["generation_error"] == "model timeout"
    assert len(result["citations"]) == 1


def test_refuse_answer_tool():
    result = refuse_answer_tool("公司有没有股票期权？")

    assert result["question"] == "公司有没有股票期权？"
    assert result["answer"] == "知识库中没有找到相关资料，暂时无法回答。"
    assert result["citations"] == []


def test_ask_clarification_tool():
    result = ask_clarification_tool(
        question="帮我查看这份文档的片段",
        missing_field="文档标题",
    )

    assert result["question"] == "帮我查看这份文档的片段"
    assert result["answer"] == "请补充文档标题。"
    assert result["citations"] == []


def test_find_document_by_title_tool(tmp_path):
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

    result = find_document_by_title_tool(
        title="员工手册",
        database_path=str(database_path),
    )

    assert result["found"] == True
    assert result["document"]["title"] == "员工手册"
    assert result["document"]["file_type"] == "md"
    assert result["match_type"] == "exact"


def test_find_document_by_title_tool_returns_not_found(tmp_path):
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

    result = find_document_by_title_tool(
        title="不存在的文档",
        database_path=str(database_path),
    )

    assert result["found"] == False
    assert result["document"] is None
    assert result["match_type"] is None


def test_find_document_by_title_tool_supports_contains_match(tmp_path):
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

    result = find_document_by_title_tool(
        title="手册",
        database_path=str(database_path),
    )

    assert result["found"] == True
    assert result["document"]["title"] == "员工手册"
    assert result["match_type"] == "contains"


def test_agent_tools_use_config_database_path():
    source = Path("backend/services/agent_tools.py").read_text(encoding="utf-8")

    assert "DATABASE_PATH" in source
    assert "SQLITE_DATABASE_PATH" not in source
    assert "week04.settings" not in source
