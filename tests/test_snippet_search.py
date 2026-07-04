from week03.load_text_documents import load_text_documents
from week03.snippet_search import search_snippets, split_sentences


def test_split_sentences_removes_empty_lines():
    content = "标题\n\n第一行内容\n第二行内容\n"

    sentences = split_sentences(content)

    assert sentences == ["标题", "第一行内容", "第二行内容"]


def test_search_snippets_finds_safety_training():
    documents = load_text_documents("data/company_docs")

    results = search_snippets(documents, "安全培训")

    assert len(results) == 1
    assert results[0]["title"] == "employee_handbook"
    assert results[0]["text"] == "新员工入职后需要在 30 天内完成安全培训。"


def test_search_snippets_returns_source_path():
    documents = load_text_documents("data/company_docs")

    results = search_snippets(documents, "发票")

    assert len(results) == 1
    assert results[0]["path"] == "data\\company_docs\\reimbursement_policy.txt"