from week03.qa_service import answer_question


def is_refusal(answer):
    return "暂时无法回答" in answer


def evaluate_refusal_questions(questions):
    passed_count = 0

    for question in questions:
        answer = answer_question(question)

        if is_refusal(answer):
            passed_count = passed_count + 1

    return {
        "total": len(questions),
        "passed": passed_count,
    }


def main():
    questions = [
        "公司有没有股票期权？",
        "公司食堂几点开门？",
        "是否支持远程办公？",
        "年终奖怎么算？",
        "公司是否提供健身房？",
    ]

    result = evaluate_refusal_questions(questions)

    print("无答案问题数量：", result["total"])
    print("正确拒答数量：", result["passed"])


if __name__ == "__main__":
    main()