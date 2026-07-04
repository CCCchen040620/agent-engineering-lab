from week03.qa_service import answer_question
from week03.evaluate_refusal import evaluate_refusal_questions
from week03.evaluate_retrieval import evaluate_retrieval_questions


def run_refusal_evaluation():
    questions = [
        "公司有没有股票期权？",
        "公司食堂几点开门？",
        "是否支持远程办公？",
        "年终奖怎么算？",
        "公司是否提供健身房？",
    ]

    return evaluate_refusal_questions(questions)


def run_retrieval_evaluation():
    questions = [
        {
            "question": "新员工什么时候完成安全培训？",
            "expected_title": "employee_handbook",
        },
        {
            "question": "病假需要什么证明？",
            "expected_title": "leave_policy",
        },
        {
            "question": "差旅报销多久内提交？",
            "expected_title": "reimbursement_policy",
        },
    ]

    return evaluate_retrieval_questions(questions)


def main():
    print("企业知识库 RAG 小助手")
    print("1. 提问")
    print("2. 运行无答案拒答评测")
    print("3. 运行有答案来源命中评测")

    choice = input("请选择功能：")

    if choice == "1":
        question = input("请输入你的问题：")
        answer = answer_question(question)
        print(answer)
    elif choice == "2":
        result = run_refusal_evaluation()
        print("无答案问题数量：", result["total"])
        print("正确拒答数量：", result["passed"])
    elif choice == "3":
        result = run_retrieval_evaluation()
        print("有答案问题数量：", result["total"])
        print("正确命中来源数量：", result["passed"])
    else:
        print("未知选项，请输入 1、2 或 3。")


if __name__ == "__main__":
    main()