from week03.answer_with_citation import build_answer
from week03.keyword_extractor import extract_keyword
from week03.load_text_documents import load_text_documents
from week03.snippet_search import search_snippets
from week04.settings import COMPANY_DOCS_FOLDER


def answer_question(question):
    documents = load_text_documents(COMPANY_DOCS_FOLDER)
    keyword = extract_keyword(question)
    snippets = search_snippets(documents, keyword)

    return build_answer(question, snippets, keyword)