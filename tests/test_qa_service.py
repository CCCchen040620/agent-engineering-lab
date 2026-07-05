from week03.qa_service import answer_question


def test_answer_question_from_qa_service():
    answer = answer_question("差旅报销多久内提交？")

    #assert "检索关键词：差旅报销" in answer
    assert "差旅报销需要在出差结束后 7 天内提交。" in answer