from pathlib import Path
from backend.services.sqlite_document_repository import (
    create_chunks_table,
    create_connection,
    create_documents_table,
    insert_chunk_to_db,
    insert_document_to_db,
)
from backend.services.sqlite_llm_qa_service import build_sqlite_llm_chat_response


def test_build_sqlite_llm_chat_response_uses_generator(tmp_path):
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
        assert "新员工什么时候完成安全培训？" in prompt
        assert "新员工入职后需要在 30 天内完成安全培训。" in prompt

        return "新员工需要在 30 天内完成安全培训。"

    response = build_sqlite_llm_chat_response(
        "新员工什么时候完成安全培训？",
        database_path=str(database_path),
        mode="keyword",
        generator=fake_generator,
    )

    assert response.answer == "新员工需要在 30 天内完成安全培训。"
    assert len(response.citations) == 1
    assert response.citations[0].title == "员工手册"


def test_build_sqlite_llm_chat_response_refuses_when_no_snippets(tmp_path):
    database_path = tmp_path / "test.db"

    def fake_generator(prompt: str) -> str:
        raise AssertionError("没有检索到资料时，不应该调用大模型。")

    response = build_sqlite_llm_chat_response(
        "公司有没有股票期权？",
        database_path=str(database_path),
        mode="keyword",
        generator=fake_generator,
    )

    assert "暂时无法回答" in response.answer
    assert response.citations == []


def test_build_sqlite_llm_chat_response_handles_generator_error(tmp_path):
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

    def broken_generator(prompt: str) -> str:
        raise RuntimeError("ollama is down")

    response = build_sqlite_llm_chat_response(
        "新员工什么时候完成安全培训？",
        database_path=str(database_path),
        mode="keyword",
        generator=broken_generator,
    )

    assert "本地模型暂时不可用" in response.answer
    assert len(response.citations) == 1


def test_build_sqlite_chat_response_embedding_mode(monkeypatch, tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    create_documents_table(connection)
    create_chunks_table(connection)

    document = insert_document_to_db(
        connection,
        title="远程办公制度",
        file_type="md",
        chunk_count=2,
        is_indexed=True,
    )

    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工可以远程办公。",
    )
    insert_chunk_to_db(
        connection,
        document_id=document["id"],
        text="员工报销需要提交发票。",
    )

    connection.close()

    embeddings = {
        "远程办公怎么申请？": [1.0, 0.0],
        "员工可以远程办公。": [0.9, 0.1],
        "员工报销需要提交发票。": [0.0, 1.0],
    }

    def fake_embedder(text: str) -> list[float]:
        return embeddings[text]

    monkeypatch.setattr(
        "backend.services.sqlite_embedding_search_service.embed_with_ollama",
        fake_embedder,
    )

    def fake_generator(prompt: str) -> str:
        return "员工可以远程办公。"

    response = build_sqlite_llm_chat_response(
        "远程办公怎么申请？",
        database_path=str(database_path),
        mode="embedding",
        min_score=0.3,
        generator=fake_generator,
    )

    assert response.answer == "员工可以远程办公。"
    assert len(response.citations) == 1
    assert response.citations[0].title == "远程办公制度"
    assert response.citations[0].text == "员工可以远程办公。"


def test_build_sqlite_chat_response_precomputed_embedding_mode(monkeypatch, tmp_path):
    database_path = tmp_path / "test.db"
    connection = create_connection(str(database_path))

    def chunk_embedder(text: str) -> list[float]:
        embeddings = {
            "员工可以远程办公。": [0.9, 0.1],
            "员工报销需要提交发票。": [0.0, 1.0],
        }

        return embeddings[text]

    from backend.services.document_indexing_service import (
        create_document_with_chunks_and_embeddings,
    )

    create_document_with_chunks_and_embeddings(
        connection,
        title="远程办公制度",
        file_type="md",
        content="员工可以远程办公。员工报销需要提交发票。",
        embedder=chunk_embedder,
    )

    connection.close()

    def query_embedder(text: str) -> list[float]:
        return [1.0, 0.0]

    monkeypatch.setattr(
        "backend.services.sqlite_precomputed_embedding_search_service.embed_with_ollama",
        query_embedder,
    )

    def fake_generator(prompt: str) -> str:
        return "员工可以远程办公。"

    response = build_sqlite_llm_chat_response(
        "远程办公怎么申请？",
        database_path=str(database_path),
        mode="precomputed_embedding",
        min_score=0.3,
        generator=fake_generator,
    )

    assert response.answer == "员工可以远程办公。"
    assert len(response.citations) == 1
    assert response.citations[0].title == "远程办公制度"
    assert response.citations[0].text == "员工可以远程办公。"


def test_sqlite_llm_qa_service_uses_config_database_path():
    source = Path("backend/services/sqlite_llm_qa_service.py").read_text(
        encoding="utf-8"
    )

    assert "DATABASE_PATH" in source
    assert "SQLITE_DATABASE_PATH" not in source
    assert "week04.settings" not in source