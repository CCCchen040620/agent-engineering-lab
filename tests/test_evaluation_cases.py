import pytest

from week11.evaluation_cases import (
    filter_evaluation_cases,
    load_agent_evaluation_cases,
    load_evaluation_cases,
    select_evaluation_cases,
    summarize_evaluation_cases,
    validate_evaluation_case,
)


def test_load_evaluation_cases_from_default_file():
    cases = load_evaluation_cases()
    case_ids = {case["id"] for case in cases}

    assert len(cases) >= 5
    assert "pg_work_hours_answer" in case_ids
    assert "pg_stock_options_refusal" in case_ids
    assert "sqlite_safety_training_answer" in case_ids
    assert "pg_prompt_injection_stock_options_refusal" in case_ids
    assert "sqlite_conversation_work_hours_answer" in case_ids

    for case in cases:
        assert case["question"] != ""
        assert case["expected_answer_type"] in {"answer", "refusal"}
        assert case["retriever_backend"] in {"sqlite", "postgresql"}
        assert case["scenario"] != ""
        assert case["tags"] != []
        assert isinstance(case["messages"], list)
        assert case["top_k"] >= 1
        assert 0 <= case["min_score"] <= 1


def test_filter_evaluation_cases_by_backend():
    cases = load_evaluation_cases()

    postgresql_cases = filter_evaluation_cases(
        cases,
        retriever_backend="postgresql",
    )

    assert len(postgresql_cases) >= 3
    assert all(case["retriever_backend"] == "postgresql" for case in postgresql_cases)


def test_filter_evaluation_cases_by_scenario_and_tag():
    cases = load_evaluation_cases()

    known_answer_cases = filter_evaluation_cases(cases, scenario="known_answer")
    policy_cases = filter_evaluation_cases(cases, tag="policy")

    assert len(known_answer_cases) >= 2
    assert all(case["scenario"] == "known_answer" for case in known_answer_cases)
    assert len(policy_cases) >= 2
    assert all("policy" in case["tags"] for case in policy_cases)


def test_select_evaluation_cases_combines_generic_filters():
    cases = load_evaluation_cases()

    selected_cases = select_evaluation_cases(
        cases,
        retriever_backend="postgresql",
        expected_answer_type="answer",
        scenario="known_answer",
        tags=["postgresql", "policy"],
        mode="precomputed_embedding",
    )

    assert len(selected_cases) >= 1

    for case in selected_cases:
        assert case["retriever_backend"] == "postgresql"
        assert case["expected_answer_type"] == "answer"
        assert case["scenario"] == "known_answer"
        assert "postgresql" in case["tags"]
        assert "policy" in case["tags"]
        assert case["mode"] == "precomputed_embedding"


def test_select_evaluation_cases_matches_any_tag_when_requested():
    cases = load_evaluation_cases()

    selected_cases = select_evaluation_cases(
        cases,
        tags=["sqlite", "unknown"],
        tag_match="any",
    )

    assert len(selected_cases) >= 2

    for case in selected_cases:
        assert "sqlite" in case["tags"] or "unknown" in case["tags"]


def test_select_evaluation_cases_can_select_prompt_injection_security_cases():
    cases = load_evaluation_cases()

    selected_cases = select_evaluation_cases(
        cases,
        retriever_backend="postgresql",
        expected_answer_type="refusal",
        scenario="prompt_injection",
        tags=["security", "prompt_injection"],
    )

    assert len(selected_cases) == 1
    assert selected_cases[0]["id"] == "pg_prompt_injection_stock_options_refusal"


def test_select_evaluation_cases_can_select_conversation_context_cases():
    cases = load_evaluation_cases()

    selected_cases = select_evaluation_cases(
        cases,
        retriever_backend="sqlite",
        scenario="conversation_context",
        tags=["conversation_context", "multi_turn"],
    )

    assert len(selected_cases) == 1
    assert selected_cases[0]["id"] == "sqlite_conversation_work_hours_answer"
    assert len(selected_cases[0]["messages"]) == 2


def test_select_evaluation_cases_rejects_invalid_tag_match():
    cases = load_evaluation_cases()

    with pytest.raises(ValueError, match="tag_match"):
        select_evaluation_cases(cases, tags=["policy"], tag_match="unsupported")


def test_load_agent_evaluation_cases_maps_expected_answer_type():
    cases = load_agent_evaluation_cases(retriever_backend="postgresql")
    case_types = {case["case_type"] for case in cases}

    assert len(cases) >= 2
    assert "answer" in case_types
    assert "refusal" in case_types
    assert all("expected_document_title" in case for case in cases)
    assert all("scenario" in case for case in cases)
    assert all("tags" in case for case in cases)
    assert all("messages" in case for case in cases)


def test_load_agent_evaluation_cases_can_use_generic_filters():
    cases = load_agent_evaluation_cases(
        retriever_backend="postgresql",
        scenario="unknown_answer",
        tags="unknown",
    )

    assert len(cases) == 1
    assert cases[0]["case_type"] == "refusal"
    assert cases[0]["scenario"] == "unknown_answer"
    assert "unknown" in cases[0]["tags"]


def test_validate_evaluation_case_requires_expected_document_for_answer():
    case = {
        "id": "answer_without_document",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "",
        "scenario": "known_answer",
        "tags": ["postgresql", "answer"],
        "retriever_backend": "postgresql",
        "mode": "precomputed_embedding",
        "top_k": 2,
        "min_score": 0.8,
    }

    with pytest.raises(ValueError, match="expected_document_title"):
        validate_evaluation_case(case)


def test_validate_evaluation_case_requires_tags():
    case = {
        "id": "case_without_tags",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "scenario": "known_answer",
        "tags": [],
        "retriever_backend": "postgresql",
        "mode": "precomputed_embedding",
        "top_k": 2,
        "min_score": 0.8,
    }

    with pytest.raises(ValueError, match="tags"):
        validate_evaluation_case(case)


def test_validate_evaluation_case_defaults_messages_to_empty_list():
    case = {
        "id": "case_without_messages",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "scenario": "known_answer",
        "tags": ["sqlite", "answer"],
        "retriever_backend": "sqlite",
        "mode": "precomputed_embedding",
        "top_k": 3,
        "min_score": 0.6,
    }

    validated_case = validate_evaluation_case(case)

    assert validated_case["messages"] == []


def test_validate_evaluation_case_rejects_invalid_messages():
    case = {
        "id": "case_with_invalid_messages",
        "question": "每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "scenario": "conversation_context",
        "tags": ["sqlite", "answer", "conversation_context"],
        "retriever_backend": "sqlite",
        "mode": "precomputed_embedding",
        "top_k": 3,
        "min_score": 0.6,
        "messages": [
            {
                "role": "user",
            }
        ],
    }

    with pytest.raises(ValueError, match="content"):
        validate_evaluation_case(case)


def test_validate_evaluation_case_allows_custom_scenario():
    case = {
        "id": "case_with_custom_scenario",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "scenario": "contract_review",
        "tags": ["contract", "answer"],
        "retriever_backend": "postgresql",
        "mode": "precomputed_embedding",
        "top_k": 2,
        "min_score": 0.8,
    }

    validated_case = validate_evaluation_case(case)

    assert validated_case["scenario"] == "contract_review"
    assert validated_case["tags"] == ["contract", "answer"]
    assert validated_case["messages"] == []


def test_summarize_evaluation_cases():
    cases = load_evaluation_cases()

    summary = summarize_evaluation_cases(cases)

    assert summary["total"] == len(cases)
    assert summary["by_backend"]["postgresql"] >= 2
    assert summary["by_backend"]["sqlite"] >= 1
    assert summary["by_answer_type"]["answer"] >= 2
    assert summary["by_answer_type"]["refusal"] >= 2
    assert summary["by_scenario"]["known_answer"] >= 2
    assert summary["by_scenario"]["unknown_answer"] >= 1
    assert summary["by_scenario"]["prompt_injection"] >= 1
    assert summary["by_scenario"]["conversation_context"] >= 1
    assert summary["by_tag"]["policy"] >= 2
    assert summary["by_tag"]["security"] >= 1
    assert summary["by_tag"]["prompt_injection"] >= 1
    assert summary["by_tag"]["multi_turn"] >= 1
