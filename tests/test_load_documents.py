from backend.services.document_service import save_documents
from week02.load_documents import load_documents


def test_load_documents_from_json_file(tmp_path):
    file_path = tmp_path / "documents.json"
    documents = [
        {
            "title": "员工手册",
            "file_type": "md",
            "chunk_count": 12,
            "is_indexed": True,
        },
        {
            "title": "报销制度",
            "file_type": "pdf",
            "chunk_count": 8,
            "is_indexed": False,
        },
        {
            "title": "请假制度",
            "file_type": "md",
            "chunk_count": 5,
            "is_indexed": True,
        },
    ]

    save_documents(str(file_path), documents)

    loaded_documents = load_documents(str(file_path))

    assert loaded_documents == documents