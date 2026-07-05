from week05.models import ChatResponse


def main():
    data = {
        "question": "差旅报销多久内提交？",
        "keyword": "差旅报销",
        "answer": "差旅报销需要在出差结束后 7 天内提交。",
        "citations": [
            {
                "title": "reimbursement_policy",
                "text": "差旅报销需要在出差结束后 7 天内提交。",
                "path": "data/company_docs/reimbursement_policy.txt",
            }
        ],
    }

    response = ChatResponse.model_validate(data)

    print("问题：", response.question)
    print("第一条引用来源：", response.citations[0].title)


if __name__ == "__main__":
    main()