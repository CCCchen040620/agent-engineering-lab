from week02.load_documents import load_documents
from backend.services.document_service import (
    delete_document_by_title,
    filter_documents,
    find_document_by_title,
    save_documents,
)


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


def test_find_document_by_title():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
        {"title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    result = find_document_by_title(documents, "员工手册")

    assert result["title"] == "员工手册"


def test_find_document_by_title_returns_none_when_not_found():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
    ]

    result = find_document_by_title(documents, "不存在的文档")

    assert result is None


def test_delete_document_by_title():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
        {"title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    results, deleted = delete_document_by_title(documents, "报销制度")

    assert deleted == True
    assert len(results) == 1
    assert results[0]["title"] == "员工手册"


def test_delete_document_by_title_returns_false_when_not_found():
    documents = [
        {"title": "员工手册", "file_type": "md", "is_indexed": True},
    ]

    results, deleted = delete_document_by_title(documents, "不存在的文档")

    assert deleted == False
    assert results == documents


def test_save_documents(tmp_path):
    file_path = tmp_path / "documents.json"
    documents = [
        {
            "title": "测试文档",
            "file_type": "md",
            "chunk_count": 1,
            "is_indexed": True,
        }
    ]

    save_documents(str(file_path), documents)

    loaded_documents = load_documents(str(file_path))

    assert loaded_documents == documents