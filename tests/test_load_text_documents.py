from week03.load_text_documents import load_text_documents


def test_load_text_documents_from_folder():
    documents = load_text_documents("data/company_docs")

    assert len(documents) == 3

    titles = []
    for document in documents:
        titles.append(document["title"])

    assert "employee_handbook" in titles
    assert "leave_policy" in titles
    assert "reimbursement_policy" in titles


def test_load_text_documents_contains_content():
    documents = load_text_documents("data/company_docs")

    first_content = documents[0]["content"]

    assert len(first_content) > 0