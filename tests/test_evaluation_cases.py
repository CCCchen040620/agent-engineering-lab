import pytest

from week11.evaluation_cases import (
    filter_evaluation_cases,
    load_agent_evaluation_cases,
    load_evaluation_cases,
    summarize_evaluation_cases,
    validate_evaluation_case,
)


def test_load_evaluation_cases_from_default_file():
    cases = load_evaluation_cases()
    case_ids = {case["id"] for case in cases}

    assert len(cases) >= 3
    assert "pg_work_hours_answer" in case_ids
    assert "pg_stock_options_refusal" in case_ids
    assert "sqlite_safety_training_answer" in case_ids

    for case in cases:
        assert case["question"] != ""
        assert case["expected_answer_type"] in {"answer", "refusal"}
        assert case["retriever_backend"] in {"sqlite", "postgresql"}
        assert case["top_k"] >= 1
        assert 0 <= case["min_score"] <= 1


def test_filter_evaluation_cases_by_backend():
    cases = load_evaluation_cases()

    postgresql_cases = filter_evaluation_cases(
        cases,
        retriever_backend="postgresql",
    )

    assert len(postgresql_cases) >= 2
    assert all(case["retriever_backend"] == "postgresql" for case in postgresql_cases)


def test_load_agent_evaluation_cases_maps_expected_answer_type():
    cases = load_agent_evaluation_cases(retriever_backend="postgresql")
    case_types = {case["case_type"] for case in cases}

    assert len(cases) >= 2
    assert "answer" in case_types
    assert "refusal" in case_types
    assert all("expected_document_title" in case for case in cases)


def test_validate_evaluation_case_requires_expected_document_for_answer():
    case = {
        "id": "answer_without_document",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "",
        "retriever_backend": "postgresql",
        "mode": "precomputed_embedding",
        "top_k": 2,
        "min_score": 0.8,
    }

    with pytest.raises(ValueError, match="expected_document_title"):
        validate_evaluation_case(case)


def test_summarize_evaluation_cases():
    cases = load_evaluation_cases()

    summary = summarize_evaluation_cases(cases)

    assert summary["total"] == len(cases)
    assert summary["by_backend"]["postgresql"] >= 2
    assert summary["by_backend"]["sqlite"] >= 1
    assert summary["by_answer_type"]["answer"] >= 2
    assert summary["by_answer_type"]["refusal"] >= 1
