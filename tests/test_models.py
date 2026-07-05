import pytest
from pydantic import ValidationError

from week05.models import ChatResponse, Citation


def test_create_citation_model():
    citation = Citation(
        title="reimbursement_policy",
        text="差旅报销需要在出差结束后 7 天内提交。",
        path="data/company_docs/reimbursement_policy.txt",
    )

    assert citation.title == "reimbursement_policy"
    assert citation.text == "差旅报销需要在出差结束后 7 天内提交。"
    assert citation.path == "data/company_docs/reimbursement_policy.txt"


def test_citation_requires_path():
    with pytest.raises(ValidationError):
        Citation(
            title="reimbursement_policy",
            text="差旅报销需要在出差结束后 7 天内提交。",
        )

    
def test_create_chat_response_model():
    response = ChatResponse(
        question="差旅报销多久内提交？",
        keyword="差旅报销",
        answer="差旅报销需要在出差结束后 7 天内提交。",
        citations=[
            Citation(
                title="reimbursement_policy",
                text="差旅报销需要在出差结束后 7 天内提交。",
                path="data/company_docs/reimbursement_policy.txt",
            )
        ],
    )

    assert response.question == "差旅报销多久内提交？"
    assert response.keyword == "差旅报销"
    assert len(response.citations) == 1
    assert response.citations[0].title == "reimbursement_policy"


def test_chat_response_model_validate_from_dict():
    data = {
        "question": "差旅报销多久内提交？",
        "keyword": "差旅报销",
        "answer": "差旅报销需要在出差结束后 7 天内提交。",
        "citations": [
            {
                "title": "reimbursement_policy",
                "text": "差旅报销需要在出差结束后 7 天内提交。",
                "path": "data/company_docs/reimbursement_policy.txt",
            }
        ],
    }

    response = ChatResponse.model_validate(data)

    assert response.question == "差旅报销多久内提交？"
    assert response.citations[0].title == "reimbursement_policy"


def test_chat_response_model_validate_requires_citation_path():
    data = {
        "question": "差旅报销多久内提交？",
        "keyword": "差旅报销",
        "answer": "差旅报销需要在出差结束后 7 天内提交。",
        "citations": [
            {
                "title": "reimbursement_policy",
                "text": "差旅报销需要在出差结束后 7 天内提交。",
            }
        ],
    }

    with pytest.raises(ValidationError):
        ChatResponse.model_validate(data)


def test_chat_response_default_empty_citations():
    response = ChatResponse(
        question="公司有没有股票期权？",
        keyword="公司有没有股票期权？",
        answer="知识库中没有找到相关资料，暂时无法回答。",
    )

    assert response.citations == []


def test_citation_rejects_empty_text():
    with pytest.raises(ValidationError):
        Citation(
            title="reimbursement_policy",
            text="",
            path="data/company_docs/reimbursement_policy.txt",
        )


def test_citation_rejects_empty_title():
    with pytest.raises(ValidationError):
        Citation(
            title="",
            text="差旅报销需要在出差结束后 7 天内提交。",
            path="data/company_docs/reimbursement_policy.txt",
        )


def test_citation_rejects_empty_path():
    with pytest.raises(ValidationError):
        Citation(
            title="reimbursement_policy",
            text="差旅报销需要在出差结束后 7 天内提交。",
            path="",
        )


def test_chat_response_rejects_empty_question():
    with pytest.raises(ValidationError):
        ChatResponse(
            question="",
            keyword="差旅报销",
            answer="差旅报销需要在出差结束后 7 天内提交。",
        )


def test_chat_response_rejects_empty_keyword():
    with pytest.raises(ValidationError):
        ChatResponse(
            question="差旅报销多久内提交？",
            keyword="",
            answer="差旅报销需要在出差结束后 7 天内提交。",
        )


def test_chat_response_rejects_empty_answer():
    with pytest.raises(ValidationError):
        ChatResponse(
            question="差旅报销多久内提交？",
            keyword="差旅报销",
            answer="",
        )