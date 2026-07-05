from week03.qa_service import answer_question
from week03.keyword_extractor import extract_keyword
#from typing import TypedDict
from week03.load_text_documents import load_text_documents
from week03.snippet_search import search_snippets
from week04.settings import COMPANY_DOCS_FOLDER
from week05.models import ChatResponse, Citation


#class StructuredAnswer(TypedDict):
    #question: str
    #keyword: str
    #answer: str
    #citations: list[dict]

   
def build_structured_answer(question: str) -> ChatResponse:
    keyword = extract_keyword(question)

    documents = load_text_documents(COMPANY_DOCS_FOLDER)
    snippets = search_snippets(documents, keyword)

    answer = answer_question(question)
    citations = build_citations(snippets)

    return ChatResponse(
        question=question,
        keyword=keyword,
        answer=answer,
        citations=citations,
    )


def build_citations(snippets: list[dict]) -> list[Citation]:
    citations = []

    for snippet in snippets[:3]:
        citation = Citation(
            title=snippet["title"],
            text=snippet["text"],
            path=snippet["path"],
        )
        citations.append(citation)

    return citations


def main():
    result = build_structured_answer("差旅报销多久内提交？")

    print("问题：", result.question)
    print("关键词：", result.keyword)
    print("回答：")
    print(result.answer)
    print("引用数量：", len(result.citations))


if __name__ == "__main__":
    main()