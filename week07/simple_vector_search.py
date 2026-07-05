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


def main():
    vector = build_term_frequency("报销 报销 报销 发票 发票 发票 发票")

    length = vector_length(vector)

    print("向量长度：", length)


if __name__ == "__main__":
    main()