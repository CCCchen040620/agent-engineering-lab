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


def main():
    text = "报销 报销 发票"

    vector = build_term_frequency(text)

    print(vector)


if __name__ == "__main__":
    main()