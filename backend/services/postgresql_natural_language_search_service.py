from backend.services.ollama_embedding_service import embed_with_ollama
from backend.services.postgresql_vector_search_repository import (
    search_chunks_by_vector_from_postgresql,
)


def search_postgresql_chunks_by_question(
    connection,
    question: str,
    top_k: int = 3,
    min_score: float = 0.0,
) -> dict:
    query_embedding = embed_with_ollama(question)

    results = search_chunks_by_vector_from_postgresql(
        connection,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    filtered_results = []

    for result in results:
        if result["score"] >= min_score:
            filtered_results.append(result)

    return {
        "question": question,
        "embedding_size": len(query_embedding),
        "results": filtered_results,
    }
