from week03.rag_cli import (
    answer_question,
    run_refusal_evaluation,
    run_retrieval_evaluation,
)


def test_answer_question_with_known_answer():
    answer = answer_question("差旅报销多久内提交？")

    assert "检索关键词：差旅报销" in answer
    assert "差旅报销需要在出差结束后 7 天内提交。" in answer
    assert "来源：reimbursement_policy" in answer


def test_run_refusal_evaluation():
    result = run_refusal_evaluation()

    assert result["total"] == 5
    assert result["passed"] == 5


def test_run_retrieval_evaluation():
    result = run_retrieval_evaluation()

    assert result["total"] == 3
    assert result["passed"] == 3