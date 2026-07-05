from week07.simple_vector_search import (
    build_term_frequency,
    count_shared_terms,
    tokenize,
    dot_product,
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