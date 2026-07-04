from week03.content_search import search_by_content
from week03.load_text_documents import load_text_documents


def test_search_by_content_finds_employee_handbook():
    documents = load_text_documents("data/company_docs")

    results = search_by_content(documents, "安全培训")

    assert len(results) == 1
    assert results[0]["title"] == "employee_handbook"


def test_search_by_content_finds_reimbursement_policy():
    documents = load_text_documents("data/company_docs")

    results = search_by_content(documents, "发票")

    assert len(results) == 1
    assert results[0]["title"] == "reimbursement_policy"


def test_search_by_content_returns_empty_list_when_not_found():
    documents = load_text_documents("data/company_docs")

    results = search_by_content(documents, "股票期权")

    assert results == []