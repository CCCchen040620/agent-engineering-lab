import pytest

from week07.simple_vector_search import (
    build_term_frequency,
    count_shared_terms,
    tokenize,
    dot_product,
    vector_length,
    cosine_similarity,
)


def test_tokenize_splits_by_space():
    tokens = tokenize("报销 发票 审批")

    assert tokens == ["报销", "发票", "审批"]


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