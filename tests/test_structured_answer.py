from week04.structured_answer import build_structured_answer


def test_build_structured_answer():
    result = build_structured_answer("差旅报销多久内提交？")

    assert result["question"] == "差旅报销多久内提交？"
    assert result["keyword"] == "差旅报销"
    assert "差旅报销需要在出差结束后 7 天内提交。" in result["answer"]


def test_build_structured_answer_includes_citations():
    result = build_structured_answer("差旅报销多久内提交？")

    assert len(result["citations"]) == 1
    assert result["citations"][0]["title"] == "reimbursement_policy"
    assert result["citations"][0]["text"] == "差旅报销需要在出差结束后 7 天内提交。"