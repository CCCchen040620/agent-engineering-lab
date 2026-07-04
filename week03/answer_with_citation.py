from week03.load_text_documents import load_text_documents
from week03.snippet_search import search_snippets


def build_answer(question, snippets):
    if len(snippets) == 0:
        return "知识库中没有找到相关资料，暂时无法回答。"

    first_snippet = snippets[0]

    return (
        "根据知识库资料："
        + first_snippet["text"]
        + "\n来源："
        + first_snippet["title"]
    )


def main():
    documents = load_text_documents("data/company_docs")
    question = input("请输入你的问题：")

    snippets = search_snippets(documents, question)
    answer = build_answer(question, snippets)

    print(answer)


if __name__ == "__main__":
    main()