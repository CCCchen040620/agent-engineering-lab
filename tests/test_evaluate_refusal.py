from week03.evaluate_refusal import is_refusal


def test_is_refusal_returns_true_for_refusal_answer():
    answer = "知识库中没有找到相关资料，暂时无法回答。"

    assert is_refusal(answer) == True


def test_is_refusal_returns_false_for_cited_answer():
    answer = "根据知识库资料：新员工入职后需要在 30 天内完成安全培训。"

    assert is_refusal(answer) == False