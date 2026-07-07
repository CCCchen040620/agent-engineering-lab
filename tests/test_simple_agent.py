from backend.services.simple_agent import run_simple_agent
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
    assert result["steps"][0]["name"] == "search_knowledge_base"
    assert result["steps"][0]["result_count"] == 1
    assert result["steps"][1]["action"] == "answer_with_context"


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
    assert result["steps"][0]["result_count"] == 0
    assert result["steps"][1]["action"] == "refuse"