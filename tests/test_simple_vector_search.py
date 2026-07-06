import pytest

from week07.simple_vector_search import (
    build_term_frequency,
    count_shared_terms,
    tokenize,
    dot_product,
    vector_length,
    cosine_similarity,
    search_chunks_by_similarity,
)


def test_tokenize_extracts_words():
    tokens = tokenize("员工报销需要提交发票。")

    assert "报销" in tokens
    assert "发票" in tokens
    assert "。" not in tokens


def test_build_term_frequency():
    vector = build_term_frequency("报销 报销 发票")

    assert vector == {
        "报销": 2,
        "发票": 1,
    }


def test_count_shared_terms():
    first = build_term_frequency("报销 发票 审批")
    second = build_term_frequency("报销 流程 发票")

    score = count_shared_terms(first, second)

    assert score == 2


def test_dot_product():
    first = build_term_frequency("报销 发票")
    second = build_term_frequency("报销 报销 发票")

    score = dot_product(first, second)

    assert score == 3


def test_vector_length():
    vector = {
        "报销": 3,
        "发票": 4,
    }

    length = vector_length(vector)

    assert length == 5


def test_cosine_similarity_same_text():
    first = build_term_frequency("报销 发票")
    second = build_term_frequency("报销 发票")

    score = cosine_similarity(first, second)

    assert score == pytest.approx(1)


def test_cosine_similarity_no_shared_terms():
    first = build_term_frequency("报销 发票")
    second = build_term_frequency("安全 培训")

    score = cosine_similarity(first, second)

    assert score == 0


def test_search_chunks_by_similarity_returns_most_similar_chunk():
    chunks = [
        {"text": "员工报销需要提交发票。"},
        {"text": "新员工需要完成安全培训。"},
        {"text": "年假需要提前申请。"},
    ]

    results = search_chunks_by_similarity("报销 发票", chunks, top_k=1)

    assert len(results) == 1
    assert results[0]["text"] == "员工报销需要提交发票。"


def test_search_chunks_by_similarity_respects_top_k():
    chunks = [
        {"text": "报销 发票"},
        {"text": "报销 审批"},
        {"text": "安全 培训"},
    ]

    results = search_chunks_by_similarity("报销", chunks, top_k=2)

    assert len(results) == 2


def test_search_chunks_by_similarity_handles_chinese_without_spaces():
    chunks = [
        {"text": "员工报销需要提交发票。"},
        {"text": "新员工需要完成安全培训。"},
        {"text": "年假需要提前申请。"},
    ]

    results = search_chunks_by_similarity("报销 发票", chunks, top_k=1)

    assert results[0]["text"] == "员工报销需要提交发票。"
    assert results[0]["score"] > 0


def test_search_chunks_by_similarity_filters_by_min_score():
    chunks = [
        {"text": "员工报销需要提交发票。"},
        {"text": "新员工需要完成安全培训。"},
    ]

    results = search_chunks_by_similarity(
        "报销 发票",
        chunks,
        top_k=2,
        min_score=0.3,
    )

    assert len(results) == 1
    assert results[0]["text"] == "员工报销需要提交发票。"