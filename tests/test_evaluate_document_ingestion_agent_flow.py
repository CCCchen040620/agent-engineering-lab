from week11.evaluate_document_ingestion_agent_flow import (
    answer_is_refusal,
    citation_matches_document,
    citations_include_document,
    evaluate_agent_result_for_document,
    evaluate_document_ingestion_agent_flow,
    get_agent_flow_failure_reason,
    top_citation_matches_document,
)


class FakeConnection:
    pass


def test_answer_is_refusal():
    assert answer_is_refusal("知识库中没有找到相关资料，暂时无法回答。") is True
    assert answer_is_refusal("根据知识库资料，员工每天需要工作 8 小时。") is False


def test_citation_matches_document():
    citation = {
        "title": "员工手册",
        "text": "员工每天需要完成 8 小时工作。",
        "path": "postgresql://chunk/1",
    }

    assert citation_matches_document(citation, "员工手册") is True
    assert citation_matches_document(citation, "请假制度") is False
    assert (
        citation_matches_document(
            {
                **citation,
                "path": "sqlite://1",
            },
            "员工手册",
        )
        is False
    )


def test_citations_include_document():
    citations = [
        {
            "title": "请假制度",
            "path": "postgresql://chunk/2",
        },
        {
            "title": "员工手册",
            "path": "postgresql://chunk/1",
        },
    ]

    assert citations_include_document(citations, "员工手册") is True
    assert citations_include_document(citations, "设备借用制度") is False


def test_top_citation_matches_document():
    citations = [
        {
            "title": "员工手册",
            "path": "postgresql://chunk/1",
        },
        {
            "title": "请假制度",
            "path": "postgresql://chunk/2",
        },
    ]

    assert top_citation_matches_document(citations, "员工手册") is True
    assert top_citation_matches_document(citations, "请假制度") is False
    assert top_citation_matches_document([], "员工手册") is False


def test_get_agent_flow_failure_reason_passes():
    result = {
        "answer": "根据知识库资料，员工每天需要工作 8 小时。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "员工手册",
                "path": "postgresql://chunk/1",
            }
        ],
    }

    assert get_agent_flow_failure_reason(result, "员工手册") == ""


def test_get_agent_flow_failure_reason_fails_when_context_is_invalid():
    result = {
        "answer": "知识库中没有找到相关资料，暂时无法回答。",
        "has_valid_context": False,
        "is_fallback": False,
        "citations": [],
    }

    assert get_agent_flow_failure_reason(result, "员工手册") == "invalid_context"


def test_get_agent_flow_failure_reason_fails_when_answer_is_fallback():
    result = {
        "answer": "已检索到相关资料，但模型生成回答失败。",
        "has_valid_context": True,
        "is_fallback": True,
        "citations": [
            {
                "title": "员工手册",
                "path": "postgresql://chunk/1",
            }
        ],
    }

    assert get_agent_flow_failure_reason(result, "员工手册") == "fallback_answer"


def test_get_agent_flow_failure_reason_fails_when_answer_is_refusal():
    result = {
        "answer": "知识库中没有找到相关资料，暂时无法回答。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "员工手册",
                "path": "postgresql://chunk/1",
            }
        ],
    }

    assert get_agent_flow_failure_reason(result, "员工手册") == "refusal_answer"


def test_get_agent_flow_failure_reason_fails_when_document_is_not_cited():
    result = {
        "answer": "根据知识库资料，员工每天需要工作 8 小时。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "请假制度",
                "path": "postgresql://chunk/2",
            }
        ],
    }

    assert (
        get_agent_flow_failure_reason(result, "员工手册")
        == "expected_document_not_cited"
    )


def test_get_agent_flow_failure_reason_fails_when_top_citation_is_wrong():
    result = {
        "answer": "根据知识库资料，员工每天需要工作 8 小时。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "请假制度",
                "path": "postgresql://chunk/2",
            },
            {
                "title": "员工手册",
                "path": "postgresql://chunk/1",
            },
        ],
    }

    assert get_agent_flow_failure_reason(result, "员工手册") == "top_citation_mismatch"


def test_evaluate_agent_result_for_document_passes():
    result = {
        "answer": "根据知识库资料，员工每天需要工作 8 小时。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "postgresql://chunk/1",
            }
        ],
        "snippets": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "postgresql://chunk/1",
                "score": 0.91,
            }
        ],
    }

    evaluation = evaluate_agent_result_for_document(result, "员工手册")

    assert evaluation["passed"] is True
    assert evaluation["failure_reason"] == ""
    assert evaluation["has_valid_context"] is True
    assert evaluation["is_fallback"] is False
    assert evaluation["citation_count"] == 1
    assert evaluation["cited_expected_document"] is True
    assert evaluation["top_citation_matched"] is True
    assert evaluation["snippets"] == result["snippets"]


def test_evaluate_document_ingestion_agent_flow_returns_document_not_found(
    monkeypatch,
):
    connection = FakeConnection()

    monkeypatch.setattr(
        "week11.evaluate_document_ingestion_agent_flow."
        "find_document_by_title_from_postgresql",
        lambda connection, title: None,
    )

    def fake_agent_runner(**kwargs):
        raise AssertionError("文档不存在时不应该调用 Agent")

    result = evaluate_document_ingestion_agent_flow(
        connection,
        title="不存在的文档",
        question="测试问题",
        agent_runner=fake_agent_runner,
    )

    assert result["passed"] is False
    assert result["failure_reason"] == "document_not_found"
    assert result["document"] is None
    assert result["citation_count"] == 0


def test_evaluate_document_ingestion_agent_flow_runs_agent_with_postgresql_backend(
    monkeypatch,
):
    connection = FakeConnection()
    captured = {}
    document = {
        "id": 1,
        "title": "员工手册",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "migration",
    }

    monkeypatch.setattr(
        "week11.evaluate_document_ingestion_agent_flow."
        "find_document_by_title_from_postgresql",
        lambda connection, title: document,
    )

    def fake_agent_runner(**kwargs):
        captured.update(kwargs)

        return {
            "answer": "根据知识库资料，员工每天需要工作 8 小时。",
            "has_valid_context": True,
            "is_fallback": False,
            "citations": [
                {
                    "title": "员工手册",
                    "text": "员工每天需要完成 8 小时工作。",
                    "path": "postgresql://chunk/1",
                }
            ],
        }

    generator = lambda prompt: "模型回答"

    result = evaluate_document_ingestion_agent_flow(
        connection,
        title="员工手册",
        question="员工每天需要工作多久？",
        top_k=2,
        min_score=0.8,
        timeout_seconds=15,
        generator=generator,
        agent_runner=fake_agent_runner,
    )

    assert result["passed"] is True
    assert result["failure_reason"] == ""
    assert result["document"] == document
    assert result["retriever_backend"] == "postgresql"
    assert result["top_k"] == 2
    assert result["min_score"] == 0.8

    assert captured["question"] == "员工每天需要工作多久？"
    assert captured["top_k"] == 2
    assert captured["min_score"] == 0.8
    assert captured["mode"] == "precomputed_embedding"
    assert captured["timeout_seconds"] == 15
    assert captured["retriever_backend"] == "postgresql"
    assert captured["postgresql_connection"] is connection
    assert captured["generator"] is generator
