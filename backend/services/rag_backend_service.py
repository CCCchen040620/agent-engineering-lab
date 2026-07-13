SUPPORTED_RAG_RETRIEVER_BACKENDS = ["sqlite", "postgresql"]


class UnsupportedRagRetrieverBackendError(ValueError):
    pass


def normalize_rag_retriever_backend(backend: str) -> str:
    normalized_backend = backend.strip().lower()

    if normalized_backend not in SUPPORTED_RAG_RETRIEVER_BACKENDS:
        raise UnsupportedRagRetrieverBackendError(
            f"Unsupported retriever backend: {backend}"
        )

    return normalized_backend


def is_postgresql_retriever_backend(backend: str) -> bool:
    return normalize_rag_retriever_backend(backend) == "postgresql"
