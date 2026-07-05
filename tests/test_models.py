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