from backend.config import (
    DATABASE_PATH,
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    RAG_RETRIEVER_BACKEND,
)
from backend.services.postgresql_rag_retriever import (
    retrieve_postgresql_snippets,
)
from backend.services.sqlite_llm_qa_service import search_sqlite_snippets


def retrieve_rag_snippets(
    question: str,
    backend: str = RAG_RETRIEVER_BACKEND,
    sqlite_database_path: str = DATABASE_PATH,
    postgresql_connection=None,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "precomputed_embedding",
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[dict]:
    if backend == "sqlite":
        keyword, snippets = search_sqlite_snippets(
            question=question,
            database_path=sqlite_database_path,
            top_k=top_k,
            mode=mode,
            min_score=min_score,
        )

        return snippets

    if backend == "postgresql":
        if postgresql_connection is None:
            raise ValueError("postgresql_connection is required")

        return retrieve_postgresql_snippets(
            postgresql_connection,
            question=question,
            top_k=top_k,
            min_score=min_score,
        )

    raise ValueError(f"Unsupported retriever backend: {backend}")