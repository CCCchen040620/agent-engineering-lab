from backend.services.rag_backend_capability_service import (
    get_rag_backend_capabilities,
    list_rag_backend_capabilities,
    rag_backend_supports_feature,
)


def test_get_sqlite_backend_capabilities():
    capabilities = get_rag_backend_capabilities("sqlite")

    assert capabilities["backend"] == "sqlite"
    assert capabilities["stage"] == "default"
    assert "conversation_chat" in capabilities["supported_features"]
    assert "document_content_indexing" in capabilities["supported_features"]
    assert "txt_file_upload" in capabilities["supported_features"]
    assert capabilities["unsupported_features"] == []


def test_get_postgresql_backend_capabilities():
    capabilities = get_rag_backend_capabilities("postgresql")

    assert capabilities["backend"] == "postgresql"
    assert capabilities["stage"] == "experimental"
    assert "pgvector_retrieval" in capabilities["supported_features"]
    assert "document_content_indexing" in capabilities["supported_features"]
    assert "conversation_chat" in capabilities["supported_features"]
    assert "streaming_chat" in capabilities["unsupported_features"]
    assert "txt_file_upload" in capabilities["unsupported_features"]


def test_get_backend_capabilities_normalizes_backend_name():
    capabilities = get_rag_backend_capabilities(" PostgreSQL ")

    assert capabilities["backend"] == "postgresql"


def test_list_rag_backend_capabilities_contains_sqlite_and_postgresql():
    capabilities = list_rag_backend_capabilities()
    backend_names = []

    for item in capabilities:
        backend_names.append(item["backend"])

    assert backend_names == ["sqlite", "postgresql"]


def test_rag_backend_supports_feature():
    assert rag_backend_supports_feature("sqlite", "conversation_chat") is True
    assert rag_backend_supports_feature("postgresql", "conversation_chat") is True
    assert rag_backend_supports_feature("sqlite", "txt_file_upload") is True
    assert rag_backend_supports_feature("postgresql", "txt_file_upload") is False
