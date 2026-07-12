from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_vector_search_repository import (
    search_chunks_by_vector_from_postgresql,
)


def search_postgresql_chunks_by_question(
    connection,
    question: str,
    top_k: int = 3,
) -> dict:
    query_embedding = embed_with_ollama(question)

    results = search_chunks_by_vector_from_postgresql(
        connection,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    return {
        "question": question,
        "embedding_size": len(query_embedding),
        "results": results,
    }