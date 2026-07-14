from week11.evaluation_cases import load_evaluation_cases
from week11.run_rag_evaluation import (
    build_rag_evaluation_report,
    evaluate_rag_result,
    run_langgraph_evaluation_case,
    run_rag_evaluation,
    write_rag_evaluation_report,
)


def test_evaluate_rag_result_passes_answer_when_expected_document_is_cited():
    case = {
        "id": "answer_case",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "retriever_backend": "sqlite",
        "mode": "precomputed_embedding",
        "top_k": 3,
        "min_score": 0.6,
    }
    result = {
        "answer": "员工每天需要完成 8 小时工作。",
        "has_valid_context": True,
        "is_fallback": False,
        "is_timeout": False,
        "snippets": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "score": 0.9,
            }
        ],
        "citations": [
            {
                "title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "sqlite://1",
            }
        ],
    }

    item = evaluate_rag_result(case, result)

    assert item["passed"] is True
    assert item["expected_document_in_citations"] is True
    assert item["expected_document_in_snippets"] is True


def test_evaluate_rag_result_fails_answer_when_expected_document_is_not_cited():
    case = {
        "id": "wrong_document_case",
        "question": "员工每天需要工作多久？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "retriever_backend": "sqlite",
        "mode": "precomputed_embedding",
        "top_k": 3,
        "min_score": 0.6,
    }
    result = {
        "answer": "员工每天需要完成 8 小时工作。",
        "has_valid_context": True,
        "is_fallback": False,
        "is_timeout": False,
        "snippets": [
            {
                "title": "其他制度",
                "text": "员工每天需要完成 8 小时工作。",
                "score": 0.9,
            }
        ],
        "citations": [
            {
                "title": "其他制度",
                "text": "员工每天需要完成 8 小时工作。",
                "path": "sqlite://9",
            }
        ],
    }

    item = evaluate_rag_result(case, result)

    assert item["passed"] is False
    assert item["expected_document_in_citations"] is False


def test_evaluate_rag_result_passes_refusal_without_context_and_citations():
    case = {
        "id": "refusal_case",
        "question": "公司有没有股票期权？",
        "expected_answer_type": "refusal",
        "expected_document_title": "",
        "retriever_backend": "postgresql",
        "mode": "precomputed_embedding",
        "top_k": 2,
        "min_score": 0.8,
    }
    result = {
        "answer": "知识库中没有找到相关资料，暂时无法回答。",
        "has_valid_context": False,
        "is_timeout": False,
        "citations": [],
        "snippets": [],
    }

    item = evaluate_rag_result(case, result)

    assert item["passed"] is True
    assert item["citation_count"] == 0


def test_run_rag_evaluation_with_fake_runner():
    cases = load_evaluation_cases()
    captured_cases = []

    def fake_runner(case, postgresql_connection, generator):
        captured_cases.append(case)

        if case["expected_answer_type"] == "refusal":
            return {
                "answer": "知识库中没有找到相关资料，暂时无法回答。",
                "has_valid_context": False,
                "citations": [],
                "snippets": [],
            }

        return {
            "answer": "根据知识库资料生成回答。",
            "has_valid_context": True,
            "is_fallback": False,
            "is_timeout": False,
            "citations": [
                {
                    "title": case["expected_document_title"],
                    "text": "命中片段",
                    "path": "fake://1",
                }
            ],
            "snippets": [
                {
                    "title": case["expected_document_title"],
                    "text": "命中片段",
                    "score": 0.9,
                }
            ],
        }

    evaluation = run_rag_evaluation(cases=cases, runner=fake_runner)

    assert evaluation["total"] == len(cases)
    assert evaluation["evaluated"] == len(cases)
    assert evaluation["passed"] == len(cases)
    assert evaluation["failed"] == 0
    assert evaluation["skipped"] == 0
    assert evaluation["pass_rate"] == 1.0
    assert captured_cases == cases


def test_run_rag_evaluation_can_select_cases_before_running():
    cases = load_evaluation_cases()
    captured_cases = []

    def fake_runner(case, postgresql_connection, generator):
        captured_cases.append(case)
        return {
            "answer": "知识库中没有找到相关资料，暂时无法回答。",
            "has_valid_context": False,
            "citations": [],
            "snippets": [],
        }

    evaluation = run_rag_evaluation(
        cases=cases,
        runner=fake_runner,
        retriever_backend="postgresql",
        scenario="unknown_answer",
        tags="unknown",
    )

    assert evaluation["total"] == 1
    assert evaluation["passed"] == 1
    assert captured_cases[0]["id"] == "pg_stock_options_refusal"


def test_run_rag_evaluation_skips_postgresql_without_connection_for_real_runner():
    cases = [
        {
            "id": "pg_case",
            "question": "员工每天需要工作多久？",
            "expected_answer_type": "answer",
            "expected_document_title": "员工手册",
            "retriever_backend": "postgresql",
            "mode": "precomputed_embedding",
            "top_k": 2,
            "min_score": 0.8,
        }
    ]

    evaluation = run_rag_evaluation(cases=cases, postgresql_connection=None)

    assert evaluation["total"] == 1
    assert evaluation["evaluated"] == 0
    assert evaluation["skipped"] == 1
    assert evaluation["items"][0]["skip_reason"] == "postgresql_connection_not_configured"


def test_run_langgraph_evaluation_case_uses_sqlite_admin_database_path(monkeypatch):
    captured_kwargs = {}

    def fake_run_langgraph_agent(**kwargs):
        captured_kwargs.update(kwargs)
        return {
            "answer": "模型回答",
            "has_valid_context": True,
            "citations": [],
            "snippets": [],
        }

    monkeypatch.setattr(
        "week11.run_rag_evaluation.run_langgraph_agent",
        fake_run_langgraph_agent,
    )

    case = {
        "id": "sqlite_case",
        "question": "新员工什么时候完成安全培训？",
        "expected_answer_type": "answer",
        "expected_document_title": "员工手册",
        "retriever_backend": "sqlite",
        "mode": "precomputed_embedding",
        "top_k": 3,
        "min_score": 0.6,
    }

    run_langgraph_evaluation_case(case)

    assert captured_kwargs["database_path"] == "data/app.db"


def test_build_rag_evaluation_report_contains_summary():
    evaluation = {
        "total": 1,
        "evaluated": 1,
        "passed": 1,
        "failed": 0,
        "skipped": 0,
        "pass_rate": 1.0,
        "by_backend": {
            "sqlite": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
            }
        },
        "by_answer_type": {
            "answer": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
            }
        },
        "by_scenario": {
            "known_answer": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
            }
        },
        "by_tag": {
            "policy": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
            }
        },
        "items": [
            {
                "id": "case_1",
                "question": "员工每天需要工作多久？",
                "expected_answer_type": "answer",
                "expected_document_title": "员工手册",
                "scenario": "known_answer",
                "tags": ["sqlite", "answer", "policy"],
                "retriever_backend": "sqlite",
                "mode": "precomputed_embedding",
                "top_k": 3,
                "min_score": 0.6,
                "passed": True,
                "skipped": False,
                "skip_reason": "",
                "answer": "员工每天需要完成 8 小时工作。",
                "has_valid_context": True,
                "is_fallback": False,
                "is_timeout": False,
                "citation_count": 1,
                "citations": [
                    {
                        "title": "员工手册",
                        "path": "sqlite://1",
                    }
                ],
                "snippet_count": 1,
                "snippets": [],
                "expected_document_in_citations": True,
                "expected_document_in_snippets": True,
            }
        ],
    }

    report = build_rag_evaluation_report(evaluation)

    assert "# RAG 统一评测报告" in report
    assert "总用例数：1" in report
    assert "### case_1" in report
    assert "员工手册" in report
    assert "known_answer" in report
    assert "policy" in report


def test_write_rag_evaluation_report(tmp_path):
    evaluation = run_rag_evaluation(
        cases=[
            {
                "id": "refusal_case",
                "question": "公司有没有股票期权？",
                "expected_answer_type": "refusal",
                "expected_document_title": "",
                "retriever_backend": "sqlite",
                "mode": "precomputed_embedding",
                "top_k": 3,
                "min_score": 0.6,
            }
        ],
        runner=lambda case, postgresql_connection, generator: {
            "answer": "知识库中没有找到相关资料，暂时无法回答。",
            "has_valid_context": False,
            "citations": [],
            "snippets": [],
        },
    )
    report_path = tmp_path / "rag-evaluation-run.md"

    written_path = write_rag_evaluation_report(evaluation, report_path)

    assert written_path == report_path
    assert report_path.exists()
    assert "refusal_case" in report_path.read_text(encoding="utf-8")
