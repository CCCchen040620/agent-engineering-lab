from week03.keyword_extractor import extract_keyword
from week03.load_text_documents import load_text_documents
from week03.snippet_search import search_snippets
from week04.settings import COMPANY_DOCS_FOLDER


def evaluate_retrieval_questions(questions):
    documents = load_text_documents(COMPANY_DOCS_FOLDER)
    passed_count = 0

    for item in questions:
        question = item["question"]
        expected_title = item["expected_title"]

        keyword = extract_keyword(question)
        snippets = search_snippets(documents, keyword)

        found = False

        for snippet in snippets:
            if snippet["title"] == expected_title:
                found = True

        if found:
            passed_count = passed_count + 1

    return {
        "total": len(questions),
        "passed": passed_count,
    }


def main():
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

    result = evaluate_retrieval_questions(questions)

    print("有答案问题数量：", result["total"])
    print("正确命中来源数量：", result["passed"])


if __name__ == "__main__":
    main()