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


def main():
    first = build_term_frequency("报销 发票")
    second = build_term_frequency("报销 发票 审批")

    score = cosine_similarity(first, second)

    print("余弦相似度：", score)


if __name__ == "__main__":
    main()