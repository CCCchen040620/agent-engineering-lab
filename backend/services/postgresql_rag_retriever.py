from backend.services.postgresql_natural_language_search_service import (
    search_postgresql_chunks_by_question,
)


def result_to_snippet(result: dict) -> dict:
    return {
        "title": result["document_title"],
        "path": f"postgresql://chunk/{result['chunk_id']}",
        "text": result["text"],
        "score": result["score"],
    }


def retrieve_postgresql_snippets(
    connection,
    question: str,
    top_k: int = 3,
    min_score: float = 0.0,
) -> list[dict]:
    search_result = search_postgresql_chunks_by_question(
        connection,
        question=question,
        top_k=top_k,
    )

    snippets = []

    for result in search_result["results"]:
        if result["score"] >= min_score:
            snippets.append(result_to_snippet(result))

    return snippets


