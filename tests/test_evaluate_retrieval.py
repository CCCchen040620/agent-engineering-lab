from week03.evaluate_retrieval import evaluate_retrieval_questions


def test_evaluate_retrieval_questions():
    questions = [
        {
            "question": "新员工什么时候完成安全培训？",
            "expected_title": "employee_handbook",
        },
        {
            "question": "差旅报销多久内提交？",
            "expected_title": "reimbursement_policy",
        },
    ]

    result = evaluate_retrieval_questions(questions)

    assert result["total"] == 2
    assert result["passed"] == 2