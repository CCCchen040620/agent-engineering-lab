from week04.structured_answer import build_structured_answer


def main():
    response = build_structured_answer("差旅报销多久内提交？")
    data = response.model_dump()

    print(data)
    print("问题：", data["question"])
    print("第一条引用来源：", data["citations"][0]["title"])


if __name__ == "__main__":
    main()