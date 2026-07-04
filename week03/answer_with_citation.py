from typing import Any


from week03.load_text_documents import load_text_documents
from week03.snippet_search import search_snippets
from week03.keyword_extractor import extract_keyword


def build_answer(question, snippets):
    if len(snippets) == 0:
        return "知识库中没有找到相关资料，暂时无法回答。"

    selected_snippets = snippets[:3]

    answer_lines = ["根据知识库资料："]

    for index,snippet in enumerate(selected_snippets,start=1):
        answer_lines.append("[" + str(index) + "] " + snippet["text"])
        answer_lines.append("    来源：" + snippet["title"])
    
    return "\n".join(answer_lines)



def main():
    documents = load_text_documents("data/company_docs")
    question = input("请输入你的问题：")

    keyword = extract_keyword(question)
    snippets = search_snippets(documents, keyword)
    answer = build_answer(question, snippets)

    print(answer)


if __name__ == "__main__":
    main()