from week10.evaluate_postgresql_migrated_documents_batch import (
    DEFAULT_BATCH_MIGRATION_AGENT_CASES,
    evaluate_batch_migrated_document_case,
    evaluate_postgresql_migrated_documents_batch,
)


def test_evaluate_batch_migrated_document_case_passes_when_expected_document_is_top1():
    case = {
        "question": "新员工什么时候完成安全培训？",
        "expected_title": "员工手册",
    }
    result = {
        "answer": "新员工入职后需要在 30 天内完成安全培训。",
        "has_valid_context": True,
        "is_fallback": False,
        "snippets": [
            {
                "title": "员工手册",
                "text": "新员工入职后需要在 30 天内完成安全培训。",
                "path": "postgresql://chunk/1",
            }
        ],
        "citations": [
            {
                "title": "员工手册",
                "text": "新员工入职后需要在 30 天内完成安全培训。",
                "path": "postgresql://chunk/1",
            }
        ],
    }

    evaluation = evaluate_batch_migrated_document_case(case, result)

    assert evaluation["passed"] is True
    assert evaluation["question"] == "新员工什么时候完成安全培训？"
    assert evaluation["expected_title"] == "员工手册"
    assert evaluation["has_valid_context"] is True
    assert evaluation["top_snippet_matched"] is True
    assert evaluation["top_citation_matched"] is True


def test_evaluate_batch_migrated_document_case_fails_when_expected_document_is_not_top1():
    case = {
        "question": "新员工什么时候完成安全培训？",
        "expected_title": "员工手册",
    }
    result = {
        "answer": "模型回答",
        "has_valid_context": True,
        "is_fallback": False,
        "snippets": [
            {
                "title": "其他文档",
                "text": "其他内容。",
                "path": "postgresql://chunk/99",
            },
            {
                "title": "员工手册",
                "text": "新员工入职后需要在 30 天内完成安全培训。",
                "path": "postgresql://chunk/1",
            },
        ],
        "citations": [],
    }

    evaluation = evaluate_batch_migrated_document_case(case, result)

    assert evaluation["passed"] is False
    assert evaluation["retrieved_expected_document"] is True
    assert evaluation["top_snippet_matched"] is False


class FakeConnection:
    pass


def test_evaluate_postgresql_migrated_documents_batch(monkeypatch):
    captured_calls = []

    def fake_run_langgraph_agent(**kwargs):
        captured_calls.append(kwargs)
        question = kwargs["question"]

        if question == "新员工什么时候完成安全培训？":
            title = "员工手册"
        else:
            title = "请假制度"

        return {
            "answer": "模型回答",
            "has_valid_context": True,
            "is_fallback": False,
            "snippets": [
                {
                    "title": title,
                    "text": "命中的片段",
                    "path": "postgresql://chunk/1",
                }
            ],
            "citations": [
                {
                    "title": title,
                    "text": "命中的片段",
                    "path": "postgresql://chunk/1",
                }
            ],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_migrated_documents_batch.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    cases = [
        {
            "question": "新员工什么时候完成安全培训？",
            "expected_title": "员工手册",
        },
        {
            "question": "请假需要怎么申请？",
            "expected_title": "请假制度",
        },
    ]

    result = evaluate_postgresql_migrated_documents_batch(
        connection=FakeConnection(),
        cases=cases,
        top_k=3,
        min_score=0.6,
        generator=lambda prompt: "模型回答",
    )

    assert result["total"] == 2
    assert result["passed"] == 2
    assert result["pass_rate"] == 1.0
    assert result["retriever_backend"] == "postgresql"
    assert result["mode"] == "precomputed_embedding"
    assert result["top_k"] == 3
    assert result["min_score"] == 0.6

    assert captured_calls[0]["question"] == "新员工什么时候完成安全培训？"
    assert captured_calls[0]["retriever_backend"] == "postgresql"
    assert captured_calls[0]["postgresql_connection"].__class__ is FakeConnection