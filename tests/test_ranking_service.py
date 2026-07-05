from backend.services.ranking_service import rank_chunks, score_text


def test_score_text_counts_keyword_occurrences():
    score = score_text("报销需要发票，差旅报销需要审批。", "报销")

    assert score == 2


def test_rank_chunks_sorts_by_score_descending():
    chunks = [
        {"text": "报销制度"},
        {"text": "差旅报销需要在出差结束后提交报销材料。"},
        {"text": "员工手册"},
    ]

    ranked_chunks = rank_chunks(chunks, "报销")

    assert ranked_chunks[0]["score"] == 2
    assert ranked_chunks[0]["text"] == "差旅报销需要在出差结束后提交报销材料。"
    assert ranked_chunks[1]["score"] == 1
    assert ranked_chunks[2]["score"] == 0