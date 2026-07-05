from week02.load_documents import load_documents
from week05.models import DocumentCreateRequest
from backend.services.document_service import (
    get_next_document_id,
    add_document,
    delete_document_by_title,
    filter_documents,
    find_document_by_title,
    save_documents,
    find_document_by_id,
)


def test_filter_documents_by_indexed_only():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
        {"id": 2, "title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    results = filter_documents(documents, indexed_only=True)

    assert len(results) == 1
    assert results[0]["title"] == "员工手册"


def test_filter_documents_by_file_type():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
        {"id": 2, "title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    results = filter_documents(documents, file_type="pdf")

    assert len(results) == 1
    assert results[0]["title"] == "报销制度"


def test_filter_documents_by_indexed_and_file_type():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
        {"id": 2, "title": "报销制度", "file_type": "pdf", "is_indexed": False},
        {"id": 3, "title": "请假制度", "file_type": "md", "is_indexed": True},
    ]

    results = filter_documents(documents, indexed_only=True, file_type="md")

    assert len(results) == 2
    assert results[0]["title"] == "员工手册"
    assert results[1]["title"] == "请假制度"


def test_find_document_by_title():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
        {"id": 2, "title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    result = find_document_by_title(documents, "员工手册")

    assert result["title"] == "员工手册"


def test_find_document_by_title_returns_none_when_not_found():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
    ]

    result = find_document_by_title(documents, "不存在的文档")

    assert result is None


def test_delete_document_by_title():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
        {"id": 2, "title": "报销制度", "file_type": "pdf", "is_indexed": False},
    ]

    results, deleted = delete_document_by_title(documents, "报销制度")

    assert deleted == True
    assert len(results) == 1
    assert results[0]["title"] == "员工手册"


def test_delete_document_by_title_returns_false_when_not_found():
    documents = [
        {"id": 1, "title": "员工手册", "file_type": "md", "is_indexed": True},
    ]

    results, deleted = delete_document_by_title(documents, "不存在的文档")

    assert deleted == False
    assert results == documents


def test_save_documents(tmp_path):
    file_path = tmp_path / "documents.json"
    documents = [
        {
            "id": 1,
            "title": "测试文档",
            "file_type": "md",
            "chunk_count": 1,
            "is_indexed": True,
        }
    ]

    save_documents(str(file_path), documents)

    loaded_documents = load_documents(str(file_path))

    assert loaded_documents == documents


def test_get_next_document_id_returns_1_for_empty_list():
    assert get_next_document_id([]) == 1


def test_get_next_document_id_returns_max_id_plus_1():
    documents = [
        {"id": 1, "title": "员工手册"},
        {"id": 3, "title": "请假制度"},
    ]

    assert get_next_document_id(documents) == 4


def test_add_document():
    documents = []
    request = DocumentCreateRequest(
        id=4,
        title="培训资料",
        file_type="pdf",
        chunk_count=3,
    )

    results, document = add_document(documents, request)

    assert document.id == 1
    assert results[0]["id"] == 1
    assert document is not None
    assert document.title == "培训资料"
    assert len(results) == 1
    assert results[0]["title"] == "培训资料"
    assert results[0]["is_indexed"] == False


def test_add_document_returns_none_when_title_exists():
    documents = [
        {
            "id": 4,
            "title": "培训资料",
            "file_type": "pdf",
            "chunk_count": 3,
            "is_indexed": False,
        }
    ]
    request = DocumentCreateRequest(
        id=1,
        title="培训资料",
        file_type="pdf",
        chunk_count=3,
    )

    results, document = add_document(documents, request)

    assert document is None
    assert results == documents


def test_find_document_by_id():
    documents = [
        {"id": 1, "title": "员工手册"},
        {"id": 2, "title": "报销制度"},
    ]

    result = find_document_by_id(documents, 1)

    assert result["title"] == "员工手册"


def test_find_document_by_id_returns_none_when_not_found():
    documents = [
        {"id": 1, "title": "员工手册"},
    ]

    result = find_document_by_id(documents, 999)

    assert result is None