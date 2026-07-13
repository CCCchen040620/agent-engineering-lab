import pytest

from backend.services.rag_backend_service import (
    UnsupportedRagRetrieverBackendError,
    is_postgresql_retriever_backend,
    normalize_rag_retriever_backend,
)


def test_normalize_rag_retriever_backend_accepts_sqlite():
    assert normalize_rag_retriever_backend("sqlite") == "sqlite"


def test_normalize_rag_retriever_backend_accepts_postgresql():
    assert normalize_rag_retriever_backend("postgresql") == "postgresql"


def test_normalize_rag_retriever_backend_strips_spaces_and_lowercases():
    assert normalize_rag_retriever_backend(" PostgreSQL ") == "postgresql"


def test_normalize_rag_retriever_backend_rejects_unknown_backend():
    with pytest.raises(UnsupportedRagRetrieverBackendError) as error:
        normalize_rag_retriever_backend("mysql")

    assert "Unsupported retriever backend: mysql" in str(error.value)


def test_is_postgresql_retriever_backend():
    assert is_postgresql_retriever_backend("postgresql") is True
    assert is_postgresql_retriever_backend("sqlite") is False
