import json

import pytest

from week11.evaluate_batch_document_ingestion_agent_flow import (
    build_batch_document_ingestion_agent_report,
    evaluate_batch_document_ingestion_agent_case,
    evaluate_batch_document_ingestion_agent_flow,
    load_batch_document_ingestion_agent_cases,
    validate_batch_document_ingestion_agent_case,
    write_batch_document_ingestion_agent_report,
)


class FakeConnection:
    pass


def build_case(**overrides) -> dict:
    case = {
        "id": "case_1",
        "title": "Target Policy",
        "question": "What is the target rule?",
        "source": "migration",
        "mode": "precomputed_embedding",
        "top_k": 3,
        "min_score": 0.6,
    }
    case.update(overrides)
    return case


def build_single_result(**overrides) -> dict:
    result = {
        "passed": True,
        "failure_reason": "fallback_answer",
        "retrieval_passed": True,
        "retrieval_failure_reason": "",
        "generation_passed": False,
        "generation_failure_reason": "fallback_answer",
        "title": "Target Policy",
        "question": "What is the target rule?",
        "document": {
            "id": 1,
            "title": "Target Policy",
            "file_type": "md",
            "chunk_count": 1,
            "is_indexed": True,
            "source": "migration",
        },
        "top_k": 3,
        "min_score": 0.6,
        "mode": "precomputed_embedding",
        "retriever_backend": "postgresql",
        "answer": "fallback answer",
        "has_valid_context": True,
        "is_fallback": True,
        "citation_count": 1,
        "cited_expected_document": True,
        "top_citation_matched": True,
        "citations": [
            {
                "title": "Target Policy",
                "text": "Target evidence.",
                "path": "postgresql://chunk/1",
            }
        ],
        "snippets": [],
    }
    result.update(overrides)
    return result


def test_validate_batch_document_ingestion_agent_case_adds_defaults():
    case = validate_batch_document_ingestion_agent_case(
        {
            "id": "case_1",
            "title": "Target Policy",
            "question": "What is the target rule?",
        }
    )

    assert case["source"] == "migration"
    assert case["mode"] == "precomputed_embedding"
    assert case["top_k"] == 3
    assert case["min_score"] == 0.6


def test_validate_batch_document_ingestion_agent_case_rejects_missing_title():
    with pytest.raises(ValueError, match="title"):
        validate_batch_document_ingestion_agent_case(
            {
                "id": "case_1",
                "question": "What is the target rule?",
            }
        )


def test_load_batch_document_ingestion_agent_cases(tmp_path):
    case_file = tmp_path / "cases.json"
    case_file.write_text(json.dumps([build_case()]), encoding="utf-8")

    cases = load_batch_document_ingestion_agent_cases(case_file)

    assert len(cases) == 1
    assert cases[0]["id"] == "case_1"


def test_default_batch_document_ingestion_agent_cases_load():
    cases = load_batch_document_ingestion_agent_cases()

    assert len(cases) > 0
    assert all(case["source"] == "migration" for case in cases)


def test_evaluate_batch_document_ingestion_agent_case_passes_with_generation_fallback():
    connection = FakeConnection()
    captured = {}

    def fake_evaluator(connection, **kwargs):
        captured.update(kwargs)
        return build_single_result()

    result = evaluate_batch_document_ingestion_agent_case(
        connection,
        build_case(),
        timeout_seconds=12,
        generator=lambda prompt: "model answer",
        evaluator=fake_evaluator,
    )

    assert result["passed"] is True
    assert result["failure_reason"] == "fallback_answer"
    assert result["case_id"] == "case_1"
    assert result["expected_source"] == "migration"
    assert result["document_source"] == "migration"
    assert result["source_matched"] is True

    assert captured["title"] == "Target Policy"
    assert captured["question"] == "What is the target rule?"
    assert captured["top_k"] == 3
    assert captured["min_score"] == 0.6
    assert captured["mode"] == "precomputed_embedding"
    assert captured["timeout_seconds"] == 12


def test_evaluate_batch_document_ingestion_agent_case_fails_on_source_mismatch():
    connection = FakeConnection()

    def fake_evaluator(connection, **kwargs):
        return build_single_result(
            failure_reason="",
            document={
                "id": 1,
                "title": "Target Policy",
                "file_type": "md",
                "chunk_count": 1,
                "is_indexed": True,
                "source": "production",
            },
        )

    result = evaluate_batch_document_ingestion_agent_case(
        connection,
        build_case(source="migration"),
        evaluator=fake_evaluator,
    )

    assert result["passed"] is False
    assert result["failure_reason"] == "source_mismatch"
    assert result["source_matched"] is False


def test_evaluate_batch_document_ingestion_agent_flow_summarizes_items():
    connection = FakeConnection()

    def fake_evaluator(connection, **kwargs):
        if kwargs["title"] == "Failed Policy":
            return build_single_result(
                passed=False,
                failure_reason="document_not_found",
                retrieval_passed=False,
                retrieval_failure_reason="document_not_found",
                generation_passed=False,
                generation_failure_reason="not_evaluated",
                title="Failed Policy",
                document=None,
                citation_count=0,
                cited_expected_document=False,
                top_citation_matched=False,
                citations=[],
            )

        return build_single_result()

    evaluation = evaluate_batch_document_ingestion_agent_flow(
        connection,
        cases=[
            build_case(id="case_1", title="Target Policy"),
            build_case(id="case_2", title="Failed Policy"),
        ],
        evaluator=fake_evaluator,
    )

    assert evaluation["total"] == 2
    assert evaluation["passed"] == 1
    assert evaluation["failed"] == 1
    assert evaluation["pass_rate"] == 0.5
    assert evaluation["retrieval_passed"] == 1
    assert evaluation["generation_passed"] == 0
    assert evaluation["source_matched"] == 1
    assert evaluation["retriever_backend"] == "postgresql"


def test_build_batch_document_ingestion_agent_report():
    evaluation = {
        "total": 1,
        "passed": 1,
        "failed": 0,
        "pass_rate": 1.0,
        "retrieval_passed": 1,
        "generation_passed": 0,
        "source_matched": 1,
        "retriever_backend": "postgresql",
        "items": [
            {
                "case_id": "case_1",
                "expected_source": "migration",
                "document_source": "migration",
                "source_matched": True,
                **build_single_result(),
            }
        ],
    }

    report = build_batch_document_ingestion_agent_report(evaluation)

    assert "# PostgreSQL 批量文档入库 Agent 验收报告" in report
    assert "case_1" in report
    assert "Target Policy" in report
    assert "fallback_answer" in report


def test_write_batch_document_ingestion_agent_report(tmp_path):
    report_path = tmp_path / "batch-report.md"
    evaluation = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "pass_rate": 0,
        "retrieval_passed": 0,
        "generation_passed": 0,
        "source_matched": 0,
        "retriever_backend": "postgresql",
        "items": [],
    }

    written_path = write_batch_document_ingestion_agent_report(evaluation, report_path)

    assert written_path == report_path
    assert report_path.exists()
    assert "无用例" in report_path.read_text(encoding="utf-8")
