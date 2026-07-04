from week02.search_service import format_document, search_documents


def test_search_documents_by_keyword():
    documents = [
        {"title": "员工手册","is_indexed":True},
        {"title": "报销制度","is_indexed":False},
        {"title": "请假制度","is_indexed":True},
    ]

    results = search_documents(documents, "制度")

    assert len(results) == 1
    assert results[0]["title"] == "请假制度"


def test_search_documents_returns_empty_list_when_not_found():
    documents = [
        {"title": "员工手册", "is_indexed": True},
        {"title": "报销制度", "is_indexed": False},
    ]

    results = search_documents(documents, "工资")

    assert results == []


def test_format_document():
    document = {
        "title": "请假制度",
        "file_type": "md",
        "chunk_count": 5,
        "is_indexed": True,
    }

    result = format_document(document)

    assert result == "- 请假制度 | 类型: md | 切分块: 5"