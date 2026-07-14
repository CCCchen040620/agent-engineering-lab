from week10.evaluate_postgresql_agent import (
    evaluate_agent_case,
    evaluate_postgresql_agent,
    get_default_agent_cases,
    is_postgresql_citation,
)


class FakeConnection:
    pass


def test_is_postgresql_citation():
    assert is_postgresql_citation({"path": "postgresql://chunk/1"}) is True
    assert is_postgresql_citation({"path": "sqlite://1"}) is False
    assert is_postgresql_citation({}) is False


def test_evaluate_agent_case_passes_answer_with_postgresql_citation():
    result = {
        "answer": "员工每天需要完成 8 小时工作。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "postgresql://chunk/2",
            }
        ],
    }

    item = evaluate_agent_case(
        {
            "question": "员工每天需要工作多久？",
            "case_type": "answer",
        },
        result,
    )

    assert item["passed"] is True
    assert item["citation_count"] == 1
    assert item["has_valid_context"] is True
    assert item["is_fallback"] is False


def test_evaluate_agent_case_fails_answer_with_sqlite_citation():
    result = {
        "answer": "员工每天需要完成 8 小时工作。",
        "has_valid_context": True,
        "is_fallback": False,
        "citations": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "sqlite://1",
            }
        ],
    }

    item = evaluate_agent_case(
        {
            "question": "员工每天需要工作多久？",
            "case_type": "answer",
        },
        result,
    )

    assert item["passed"] is False


def test_evaluate_agent_case_passes_refusal_without_citations():
    result = {
        "answer": "知识库中没有找到相关资料，暂时无法回答。",
        "has_valid_context": False,
        "is_fallback": False,
        "citations": [],
    }

    item = evaluate_agent_case(
        {
            "question": "公司有没有股票期权？",
            "case_type": "refusal",
        },
        result,
    )

    assert item["passed"] is True
    assert item["citation_count"] == 0
    assert item["has_valid_context"] is False


def test_evaluate_postgresql_agent(monkeypatch):
    captured_calls = []

    def fake_run_langgraph_agent(**kwargs):
        captured_calls.append(kwargs)

        if kwargs["question"] == "员工每天需要工作多久？":
            return {
                "answer": "员工每天需要完成 8 小时工作。",
                "has_valid_context": True,
                "is_fallback": False,
                "citations": [
                    {
                        "title": "员工手册",
                        "text": "员工每天需要完成 8 小时工作。",
                        "path": "postgresql://chunk/2",
                    }
                ],
            }

        return {
            "answer": "知识库中没有找到相关资料，暂时无法回答。",
            "has_valid_context": False,
            "is_fallback": False,
            "citations": [],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_agent.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    connection = FakeConnection()

    result = evaluate_postgresql_agent(
        connection,
        cases=[
            {
                "question": "员工每天需要工作多久？",
                "case_type": "answer",
            },
            {
                "question": "公司有没有股票期权？",
                "case_type": "refusal",
            },
        ],
        top_k=2,
        min_score=0.8,
        generator=lambda prompt: "模型回答",
    )

    assert result["total"] == 2
    assert result["passed"] == 2
    assert result["pass_rate"] == 1.0
    assert result["top_k"] == 2
    assert result["min_score"] == 0.8
    assert result["mode"] == "precomputed_embedding"
    assert result["retriever_backend"] == "postgresql"
    assert result["items"][0]["passed"] is True
    assert result["items"][1]["passed"] is True

    assert captured_calls[0]["question"] == "员工每天需要工作多久？"
    assert captured_calls[0]["top_k"] == 2
    assert captured_calls[0]["min_score"] == 0.8
    assert captured_calls[0]["mode"] == "precomputed_embedding"
    assert captured_calls[0]["retriever_backend"] == "postgresql"
    assert captured_calls[0]["postgresql_connection"] is connection

    assert captured_calls[1]["question"] == "公司有没有股票期权？"
    assert captured_calls[1]["retriever_backend"] == "postgresql"


def test_get_default_agent_cases_loads_shared_postgresql_cases():
    cases = get_default_agent_cases()
    case_types = {case["case_type"] for case in cases}

    assert len(cases) >= 2
    assert "answer" in case_types
    assert "refusal" in case_types
