import math


def tokenize(text: str) -> list[str]:
    return text.split()


def build_term_frequency(text: str) -> dict[str, int]:
    tokens = tokenize(text)
    frequencies = {}

    for token in tokens:
        if token not in frequencies:
            frequencies[token] = 0

        frequencies[token] = frequencies[token] + 1

    return frequencies


def count_shared_terms(first_vector: dict[str, int], second_vector: dict[str, int]) -> int:
    shared_count = 0

    for term in first_vector:
        if term in second_vector:
            shared_count = shared_count + 1

    return shared_count


def dot_product(first_vector: dict[str, int], second_vector: dict[str, int]) -> int:
    score = 0

    for term in first_vector:
        if term in second_vector:
            score = score + first_vector[term] * second_vector[term]

    return score


def vector_length(vector: dict[str, int]) -> float:
    total = 0

    for value in vector.values():
        total = total + value * value

    return math.sqrt(total)


def cosine_similarity(first_vector: dict[str, int], second_vector: dict[str, int]) -> float:
    first_length = vector_length(first_vector)
    second_length = vector_length(second_vector)

    if first_length == 0 or second_length == 0:
        return 0

    return dot_product(first_vector, second_vector) / (first_length * second_length)


def search_chunks_by_similarity(
    query: str,
    chunks: list[dict],
    top_k: int = 3,
) -> list[dict]:
    query_vector = build_term_frequency(query)
    results = []

    for chunk in chunks:
        chunk_vector = build_term_frequency(chunk["text"])
        score = cosine_similarity(query_vector, chunk_vector)

        result = chunk.copy()
        result["score"] = score

        results.append(result)

    results.sort(key=lambda chunk: chunk["score"], reverse=True)

    return results[:top_k]


def main():
    chunks = [
        {"text": "员工报销需要提交发票。"},
        {"text": "新员工需要完成安全培训。"},
        {"text": "年假需要提前申请。"},
    ]

    results = search_chunks_by_similarity("报销 发票", chunks, top_k=2)

    for result in results:
        print(result)


if __name__ == "__main__":
    main()