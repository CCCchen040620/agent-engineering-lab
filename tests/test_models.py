from week05.models import Citation


def test_create_citation_model():
    citation = Citation(
        title="reimbursement_policy",
        text="差旅报销需要在出差结束后 7 天内提交。",
    )

    assert citation.title == "reimbursement_policy"
    assert citation.text == "差旅报销需要在出差结束后 7 天内提交。"