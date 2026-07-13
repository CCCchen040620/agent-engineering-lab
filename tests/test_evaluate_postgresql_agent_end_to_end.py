from week10.evaluate_postgresql_agent_end_to_end import (
    END_TO_END_DOCUMENT_CONTENT,
    END_TO_END_DOCUMENT_TITLE,
    END_TO_END_QUESTION,
    cites_expected_document,
    ensure_end_to_end_document,
    evaluate_end_to_end_agent_result,
    evaluate_postgresql_agent_end_to_end,
    top_citation_matches_expected_document,
)


class FakeConnection:
    pass


def test_ensure_end_to_end_document_reuses_existing_document(monkeypatch):
    connection = FakeConnection()

    existing_document = {
        "id": 1,
        "title": END_TO_END_DOCUMENT_TITLE,
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
    }

    def fake_find_document(connection, title):
        return existing_document

    def fake_create_document(*args, **kwargs):
        raise AssertionError("不应该重复创建已存在的验收文档")

    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent_end_to_end."
        "find_document_by_title_from_postgresql",
        fake_find_document,
    )
    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent_end_to_end."
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_document,
    )

    result = ensure_end_to_end_document(connection)

    assert result == {
        "created": False,
        "document": existing_document,
    }


def test_ensure_end_to_end_document_creates_missing_document(monkeypatch):
    connection = FakeConnection()
    captured = {}

    def fake_find_document(connection, title):
        return None

    def fake_create_document(
        connection,
        title,
        file_type,
        content,
        embedder,
        embedding_model,
        source,
    ):
        captured["title"] = title
        captured["file_type"] = file_type
        captured["content"] = content
        captured["embedding_model"] = embedding_model
        captured["source"] = source

        return {
            "document": {
                "id": 2,
                "title": title,
                "file_type": file_type,
                "chunk_count": 2,
                "is_indexed": True,
                "source": source,
            },
            "chunks": [],
            "embeddings": [],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent_end_to_end."
        "find_document_by_title_from_postgresql",
        fake_find_document,
    )
    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent_end_to_end."
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_document,
    )

    result = ensure_end_to_end_document(
        connection,
        embedder=lambda text: [1.0, 0.0],
        embedding_model="fake-model",
    )

    assert result["created"] is True
    assert result["document"]["title"] == END_TO_END_DOCUMENT_TITLE
    assert result["document"]["is_indexed"] is True
    assert result["document"]["source"] == "evaluation"
    assert captured == {
        "title": END_TO_END_DOCUMENT_TITLE,
        "file_type": "md",
        "content": END_TO_END_DOCUMENT_CONTENT,
        "embedding_model": "fake-model",
        "source": "evaluation",
    }


def test_cites_expected_document():
    citations = [
        {
            "title": "其他文档",
            "path": "postgresql://chunk/1",
        },
        {
            "title": END_TO_END_DOCUMENT_TITLE,
            "path": "postgresql://chunk/2",
        },
    ]

    assert cites_expected_document(citations, END_TO_END_DOCUMENT_TITLE) is True
    assert cites_expected_document(citations, "不存在的文档") is False


def test_top_citation_matches_expected_document():
    citations = [
        {
            "title": END_TO_END_DOCUMENT_TITLE,
            "path": "postgresql://chunk/2",
        },
        {
            "title": "其他文档",
            "path": "postgresql://chunk/1",
        },
    ]

    assert (
        top_citation_matches_expected_document(
            citations,
            END_TO_END_DOCUMENT_TITLE,
        )
        is True
    )
    assert top_citation_matches_expected_document([], END_TO_END_DOCUMENT_TITLE) is False


def test_top_citation_does_not_match_when_expected_document_is_second():
    citations = [
        {
            "title": "其他文档",
            "path": "postgresql://chunk/1",
        },
        {
            "title": END_TO_END_DOCUMENT_TITLE,
            "path": "postgresql://chunk/2",
        },
    ]

    assert (
        top_citation_matches_expected_document(
            citations,
            END_TO_END_DOCUMENT_TITLE,
        )
        is False
    )


def test_evaluate_end_to_end_agent_result_passes_when_expected_document_is_cited():
    result = {
        "answer": "员工参加外部培训需要提前提交申请。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": END_TO_END_DOCUMENT_TITLE,
                "text": "员工参加外部培训需要提前提交申请。",
                "path": "postgresql://chunk/10",
            }
        ],
    }

    evaluation = evaluate_end_to_end_agent_result(
        result,
        expected_title=END_TO_END_DOCUMENT_TITLE,
    )

    assert evaluation["passed"] is True
    assert evaluation["cited_expected_document"] is True
    assert evaluation["top_citation_matched"] is True
    assert evaluation["citation_count"] == 1


def test_evaluate_end_to_end_agent_result_fails_when_expected_document_is_not_top1():
    result = {
        "answer": "员工参加外部培训需要提前提交申请。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "其他文档",
                "text": "员工参加外部培训需要提前提交申请。",
                "path": "postgresql://chunk/9",
            },
            {
                "title": END_TO_END_DOCUMENT_TITLE,
                "text": "员工参加外部培训需要提前提交申请。",
                "path": "postgresql://chunk/10",
            },
        ],
    }

    evaluation = evaluate_end_to_end_agent_result(
        result,
        expected_title=END_TO_END_DOCUMENT_TITLE,
    )

    assert evaluation["passed"] is False
    assert evaluation["cited_expected_document"] is True
    assert evaluation["top_citation_matched"] is False


def test_evaluate_end_to_end_agent_result_fails_when_wrong_document_is_cited():
    result = {
        "answer": "员工参加外部培训需要提前提交申请。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "其他文档",
                "text": "员工参加外部培训需要提前提交申请。",
                "path": "postgresql://chunk/10",
            }
        ],
    }

    evaluation = evaluate_end_to_end_agent_result(
        result,
        expected_title=END_TO_END_DOCUMENT_TITLE,
    )

    assert evaluation["passed"] is False
    assert evaluation["cited_expected_document"] is False


def test_evaluate_postgresql_agent_end_to_end(monkeypatch):
    connection = FakeConnection()
    captured_call = {}

    def fake_ensure_document(
        connection,
        title,
        content,
        embedder,
        source,
    ):
        return {
            "created": True,
            "document": {
                "id": 3,
                "title": title,
                "file_type": "md",
                "chunk_count": 2,
                "is_indexed": True,
            },
        }

    def fake_run_langgraph_agent(**kwargs):
        captured_call.update(kwargs)

        return {
            "answer": "员工参加外部培训需要提前提交申请。",
            "has_valid_context": True,
            "is_fallback": False,
            "citations": [
                {
                    "title": END_TO_END_DOCUMENT_TITLE,
                    "text": "员工参加外部培训需要提前提交申请。",
                    "path": "postgresql://chunk/3",
                }
            ],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent_end_to_end.ensure_end_to_end_document",
        fake_ensure_document,
    )
    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent_end_to_end.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    result = evaluate_postgresql_agent_end_to_end(
        connection,
        top_k=3,
        min_score=0.6,
        generator=lambda prompt: "模型回答",
    )

    assert result["passed"] is True
    assert result["document_created"] is True
    assert result["document"]["title"] == END_TO_END_DOCUMENT_TITLE
    assert result["question"] == END_TO_END_QUESTION
    assert result["retriever_backend"] == "postgresql"
    assert result["cited_expected_document"] is True
    assert result["top_citation_matched"] is True

    assert captured_call["question"] == END_TO_END_QUESTION
    assert captured_call["top_k"] == 3
    assert captured_call["min_score"] == 0.6
    assert captured_call["mode"] == "precomputed_embedding"
    assert captured_call["retriever_backend"] == "postgresql"
    assert captured_call["postgresql_connection"] is connection
