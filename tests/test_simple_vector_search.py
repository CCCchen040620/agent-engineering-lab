from week07.simple_vector_search import build_term_frequency, tokenize


def test_tokenize_splits_by_space():
    tokens = tokenize("报销 发票 审批")

    assert tokens == ["报销", "发票", "审批"]


def test_build_term_frequency():
    vector = build_term_frequency("报销 报销 发票")

    assert vector == {
        "报销": 2,
        "发票": 1,
    }