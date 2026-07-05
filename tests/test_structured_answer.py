from week04.structured_answer import build_structured_answer
from week05.models import Citation, ChatResponse


def test_build_structured_answer():
    result = build_structured_answer("差旅报销多久内提交？")

    assert result.question == "差旅报销多久内提交？"
    assert result.keyword == "差旅报销"
    assert "差旅报销需要在出差结束后 7 天内提交。" in result.answer


def test_build_structured_answer_includes_citations():
    result = build_structured_answer("差旅报销多久内提交？")

    assert len(result.citations) == 1
    assert result.citations[0].title == "reimbursement_policy"
    assert result.citations[0].text == "差旅报销需要在出差结束后 7 天内提交。"


def test_build_structured_answer_returns_chat_response_model():
    result = build_structured_answer("差旅报销多久内提交？")

    assert isinstance(result, ChatResponse)


def test_build_structured_answer_citations_are_citation_models():
    result = build_structured_answer("差旅报销多久内提交？")

    assert isinstance(result.citations[0], Citation)


def test_build_structured_answer_no_answer_has_empty_citations():
    result = build_structured_answer("公司有没有股票期权？")

    assert result.citations == []
    assert "暂时无法回答" in result.answer