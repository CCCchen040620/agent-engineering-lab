def score_text(text: str, keyword: str) -> int:
    return text.count(keyword)


def rank_chunks(chunks: list[dict], keyword: str) -> list[dict]:
    ranked_chunks = []

    for chunk in chunks:
        score = score_text(chunk["text"], keyword)

        ranked_chunk = chunk.copy()
        ranked_chunk["score"] = score

        ranked_chunks.append(ranked_chunk)

    ranked_chunks.sort(key=lambda chunk: chunk["score"], reverse=True)

    return ranked_chunks