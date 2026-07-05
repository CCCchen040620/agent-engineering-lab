from backend.services.document_service import filter_documents


def test_filter_documents_by_indexed_only():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
        {"title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    results = filter_documents(documents, indexed_only=True)

    assert len(results) == 1
    assert results[0]["title"] == "员工手册"


def test_filter_documents_by_file_type():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
        {"title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    results = filter_documents(documents, file_type="pdf")

    assert len(results) == 1
    assert results[0]["title"] == "报销制度"


def test_filter_documents_by_indexed_and_file_type():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
        {"title": "报销制度", "file_type": "pdf", "is_indexed": False},
        {"title": "请假制度", "file_type": "md", "is_indexed": True},
    ]

    results = filter_documents(documents, indexed_only=True, file_type="md")

    assert len(results) == 2
    assert results[0]["title"] == "员工手册"
    assert results[1]["title"] == "请假制度"