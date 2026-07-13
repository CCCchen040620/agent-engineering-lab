from week10.evaluate_postgresql_migrated_document_agent import (
    MIGRATED_DOCUMENT_QUESTION,
    contains_expected_document,
    evaluate_migrated_document_agent_result,
    evaluate_postgresql_migrated_document_agent,
    is_expected_document_item,
    is_postgresql_snippet,
    top_item_matches_expected_document,
)
from week10.seed_sqlite_migration_sample import SQLITE_MIGRATION_SAMPLE_TITLE


class FakeConnection:
    pass


def test_is_postgresql_snippet():
    assert is_postgresql_snippet({"path": "postgresql://chunk/10"}) is True
    assert is_postgresql_snippet({"path": "sqlite://1"}) is False
    assert is_postgresql_snippet({}) is False


def test_is_expected_document_item():
    item = {
        "title": SQLITE_MIGRATION_SAMPLE_TITLE,
        "path": "postgresql://chunk/10",
    }

    assert is_expected_document_item(item, SQLITE_MIGRATION_SAMPLE_TITLE) is True
    assert is_expected_document_item(item, "其他文档") is False
    assert (
        is_expected_document_item(
            {
                "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                "path": "sqlite://1",
            },
            SQLITE_MIGRATION_SAMPLE_TITLE,
        )
        is False
    )


def test_contains_expected_document():
    items = [
        {
            "title": "其他文档",
            "path": "postgresql://chunk/1",
        },
        {
            "title": SQLITE_MIGRATION_SAMPLE_TITLE,
            "path": "postgresql://chunk/10",
        },
    ]

    assert contains_expected_document(items, SQLITE_MIGRATION_SAMPLE_TITLE) is True
    assert contains_expected_document(items, "不存在的文档") is False


def test_top_item_matches_expected_document():
    items = [
        {
            "title": SQLITE_MIGRATION_SAMPLE_TITLE,
            "path": "postgresql://chunk/10",
        },
        {
            "title": "其他文档",
            "path": "postgresql://chunk/1",
        },
    ]

    assert top_item_matches_expected_document(items, SQLITE_MIGRATION_SAMPLE_TITLE) is True
    assert top_item_matches_expected_document([], SQLITE_MIGRATION_SAMPLE_TITLE) is False


def test_top_item_does_not_match_when_expected_document_is_second():
    items = [
        {
            "title": "其他文档",
            "path": "postgresql://chunk/1",
        },
        {
            "title": SQLITE_MIGRATION_SAMPLE_TITLE,
            "path": "postgresql://chunk/10",
        },
    ]

    assert top_item_matches_expected_document(items, SQLITE_MIGRATION_SAMPLE_TITLE) is False


def test_evaluate_migrated_document_agent_result_passes_with_top_snippet():
    result = {
        "answer": "已检索到相关资料，但模型生成回答失败。请查看引用内容：",
        "has_valid_context": True,
        "is_fallback": True,
        "snippets": [
            {
                "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                "text": "SQLite 迁移测试片段一。",
                "path": "postgresql://chunk/10",
            }
        ],
        "citations": [
            {
                "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                "text": "SQLite 迁移测试片段一。",
                "path": "postgresql://chunk/10",
            }
        ],
    }

    evaluation = evaluate_migrated_document_agent_result(
        result,
        expected_title=SQLITE_MIGRATION_SAMPLE_TITLE,
    )

    assert evaluation["passed"] is True
    assert evaluation["has_valid_context"] is True
    assert evaluation["is_fallback"] is True
    assert evaluation["retrieved_expected_document"] is True
    assert evaluation["cited_expected_document"] is True
    assert evaluation["top_snippet_matched"] is True
    assert evaluation["top_citation_matched"] is True
    assert evaluation["snippet_count"] == 1
    assert evaluation["citation_count"] == 1


def test_evaluate_migrated_document_agent_result_fails_without_valid_context():
    result = {
        "answer": "知识库中没有找到相关资料，暂时无法回答。",
        "has_valid_context": False,
        "is_fallback": False,
        "snippets": [
            {
                "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                "text": "SQLite 迁移测试片段一。",
                "path": "postgresql://chunk/10",
            }
        ],
        "citations": [],
    }

    evaluation = evaluate_migrated_document_agent_result(
        result,
        expected_title=SQLITE_MIGRATION_SAMPLE_TITLE,
    )

    assert evaluation["passed"] is False
    assert evaluation["retrieved_expected_document"] is True
    assert evaluation["cited_expected_document"] is False


def test_evaluate_migrated_document_agent_result_fails_when_expected_document_is_not_top1():
    result = {
        "answer": "模型回答",
        "has_valid_context": True,
        "is_fallback": False,
        "snippets": [
            {
                "title": "其他文档",
                "text": "其他片段。",
                "path": "postgresql://chunk/1",
            },
            {
                "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                "text": "SQLite 迁移测试片段一。",
                "path": "postgresql://chunk/10",
            },
        ],
        "citations": [],
    }

    evaluation = evaluate_migrated_document_agent_result(
        result,
        expected_title=SQLITE_MIGRATION_SAMPLE_TITLE,
    )

    assert evaluation["passed"] is False
    assert evaluation["retrieved_expected_document"] is True
    assert evaluation["top_snippet_matched"] is False


def test_evaluate_postgresql_migrated_document_agent(monkeypatch):
    connection = FakeConnection()
    captured_call = {}

    def fake_run_langgraph_agent(**kwargs):
        captured_call.update(kwargs)

        return {
            "answer": "已检索到相关资料，但模型生成回答失败。请查看引用内容：",
            "has_valid_context": True,
            "is_fallback": True,
            "snippets": [
                {
                    "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                    "text": "SQLite 迁移测试片段一。",
                    "path": "postgresql://chunk/10",
                }
            ],
            "citations": [
                {
                    "title": SQLITE_MIGRATION_SAMPLE_TITLE,
                    "text": "SQLite 迁移测试片段一。",
                    "path": "postgresql://chunk/10",
                }
            ],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_migrated_document_agent.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    result = evaluate_postgresql_migrated_document_agent(
        connection,
        top_k=3,
        min_score=0.6,
        generator=lambda prompt: "模型回答",
    )

    assert result["passed"] is True
    assert result["question"] == MIGRATED_DOCUMENT_QUESTION
    assert result["expected_title"] == SQLITE_MIGRATION_SAMPLE_TITLE
    assert result["retriever_backend"] == "postgresql"
    assert result["mode"] == "precomputed_embedding"
    assert result["top_k"] == 3
    assert result["min_score"] == 0.6
    assert result["is_fallback"] is True
    assert result["top_snippet_matched"] is True
    assert result["top_citation_matched"] is True

    assert captured_call["question"] == MIGRATED_DOCUMENT_QUESTION
    assert captured_call["top_k"] == 3
    assert captured_call["min_score"] == 0.6
    assert captured_call["mode"] == "precomputed_embedding"
    assert captured_call["retriever_backend"] == "postgresql"
    assert captured_call["postgresql_connection"] is connection
