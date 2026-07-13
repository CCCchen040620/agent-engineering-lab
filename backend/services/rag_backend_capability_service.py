from copy import deepcopy

from backend.services.rag_backend_service import normalize_rag_retriever_backend


RAG_BACKEND_CAPABILITIES = {
    "sqlite": {
        "backend": "sqlite",
        "label": "SQLite",
        "stage": "default",
        "supported_features": [
            "document_listing",
            "document_indexing",
            "chunk_listing",
            "rag_retrieval",
            "llm_chat",
            "simple_agent_chat",
            "langgraph_agent_chat",
            "conversation_chat",
            "streaming_chat",
            "feedback_storage",
            "embedding_backfill",
        ],
        "unsupported_features": [],
        "notes": [
            "SQLite is the default learning backend.",
            "It supports the full local demo workflow.",
        ],
    },
    "postgresql": {
        "backend": "postgresql",
        "label": "PostgreSQL / pgvector",
        "stage": "experimental",
        "supported_features": [
            "document_listing",
            "document_indexing",
            "chunk_listing",
            "pgvector_retrieval",
            "langgraph_agent_chat",
            "embedding_backfill",
        ],
        "unsupported_features": [
            "conversation_chat",
            "streaming_chat",
            "feedback_storage",
        ],
        "notes": [
            "PostgreSQL is currently used for pgvector retrieval experiments.",
            "Conversation memory and feedback still use SQLite.",
        ],
    },
}


def list_rag_backend_capabilities() -> list[dict]:
    return deepcopy(list(RAG_BACKEND_CAPABILITIES.values()))


def get_rag_backend_capabilities(backend: str) -> dict:
    normalized_backend = normalize_rag_retriever_backend(backend)

    return deepcopy(RAG_BACKEND_CAPABILITIES[normalized_backend])


def rag_backend_supports_feature(backend: str, feature: str) -> bool:
    capabilities = get_rag_backend_capabilities(backend)

    return feature in capabilities["supported_features"]
