from week02.search_service import search_documents


def test_search_documents_by_keyword():
    documents = [
        {"title": "员工手册"},
        {"title": "报销制度"},
        {"title": "请假制度"},
    ]

    results = search_documents(documents, "制度")

    assert len(results) == 2
    assert results[0]["title"] == "报销制度"
    assert results[1]["title"] == "请假制度"


def test_search_documents_returns_empty_list_when_not_found():
    documents = [
        {"title": "员工手册"},
        {"title": "报销制度"},
    ]

    results = search_documents(documents, "工资")

    assert results == []