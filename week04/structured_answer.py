from week03.qa_service import answer_question
from week03.keyword_extractor import extract_keyword
from typing import TypedDict


class StructuredAnswer(TypedDict):
    question: str
    keyword: str
    answer: str


def build_structured_answer(question: str) -> StructuredAnswer:
    keyword = extract_keyword(question)
    answer = answer_question(question)

    return {
        "question": question,
        "keyword": keyword,
        "answer": answer,
    }


def main():
    result = build_structured_answer("差旅报销多久内提交？")

    print("问题：", result["question"])
    print("关键词：", result["keyword"])
    print("回答：")
    print(result["answer"])


if __name__ == "__main__":
    main()