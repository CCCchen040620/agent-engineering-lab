from backend.services.sqlite_llm_qa_service import build_sqlite_llm_chat_response


def print_result(question: str):
    response = build_sqlite_llm_chat_response(question)

    print("问题：", response.question)
    print("关键词：", response.keyword)
    print("回答：")
    print(response.answer)
    print("引用数量：", len(response.citations))

    for index, citation in enumerate(response.citations, start=1):
        print(f"[{index}] {citation.title} - {citation.text}")

    print("-" * 50)


def main():
    questions = [
        "新员工什么时候完成安全培训？",
        "员工每天需要工作多久？",
        "请假需要怎么申请？",
        "公司有没有股票期权？",
    ]

    for question in questions:
        print_result(question)


if __name__ == "__main__":
    main()