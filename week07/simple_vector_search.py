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


def main():
    first = build_term_frequency("报销 发票 审批")
    second = build_term_frequency("报销 流程 发票")

    score = count_shared_terms(first, second)

    print("相似度分数：", score)


if __name__ == "__main__":
    main()