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


def main():
    first = build_term_frequency("报销 发票")
    second = build_term_frequency("报销 报销 发票")

    score = dot_product(first, second)

    print("点积分数：", score)


if __name__ == "__main__":
    main()