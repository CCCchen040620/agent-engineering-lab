from typing import Callable

from backend.services.embedding_similarity_service import cosine_similarity
from backend.services.ollama_embedding_service import embed_with_ollama


def search_chunks_by_embedding(
    query: str,
    chunks: list[dict],
    top_k: int = 3,
    embedder: Callable[[str], list[float]] = embed_with_ollama,
) -> list[dict]:
    query_embedding = embedder(query)

    results = []

    for chunk in chunks:
        chunk_embedding = embedder(chunk["text"])
        score = cosine_similarity(query_embedding, chunk_embedding)

        result = chunk.copy()
        result["score"] = score

        results.append(result)

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:top_k]