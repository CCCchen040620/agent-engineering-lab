import pytest

from week02.filter_by_type import filter_documents_by_type


def test_filter_documents_by_type():
    documents = [
    {"title": "员工手册", "file_type": "md"},
    {"title": "报销制度", "file_type": "pdf"},
    {"title": "请假制度", "file_type": "md"},
    {"title": "培训资料", "file_type": "pdf"},
    ]

    results = filter_documents_by_type(documents, "md")
    assert len(results) == 2
    assert results[0]["title"] == "员工手册"
    assert results[1]["title"] == "请假制度"
    
    results = filter_documents_by_type(documents, "pdf")
    assert len(results) == 2
    assert results[0]["title"] == "报销制度"
    assert results[1]["title"] == "培训资料"

    results = filter_documents_by_type(documents, "docx")
    assert len(results) == 0
    assert results == []
    