from week10.evaluate_postgresql_retrieval import (
    evaluate_postgresql_retrieval,
    evaluate_postgresql_retrieval_for_min_scores,
)


class FakeConnection:
    pass


def test_evaluate_postgresql_retrieval(monkeypatch):
    captured_questions = []

    def fake_search_postgresql_chunks_by_question(
        connection,
        question: str,
        top_k: int,
        min_score: float,
    ):
        captured_questions.append(
            {
                "question": question,
                "top_k": top_k,
                "min_score": min_score,
            }
        )

        if question == "员工每天需要工作多久？":
            return {
                "question": question,
                "embedding_size": 1024,
                "results": [
                    {
                        "chunk_id": 1,
                        "document_id": 3,
                        "document_title": "员工手册",
                        "text": "员工每天需要完成 8 小时工作。",
                        "distance": 0.1,
                        "score": 0.9,
                    }
                ],
            }

        return {
            "question": question,
            "embedding_size": 1024,
            "results": [
                {
                    "chunk_id": 2,
                    "document_id": 3,
                    "document_title": "报销制度",
                    "text": "差旅报销需要在出差结束后 7 天内提交。",
                    "distance": 0.2,
                    "score": 0.8,
                }
            ],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_retrieval.search_postgresql_chunks_by_question",
        fake_search_postgresql_chunks_by_question,
    )

    questions = [
        {
            "question": "员工每天需要工作多久？",
            "expected_text": "员工每天需要完成 8 小时工作。",
        },
        {
            "question": "差旅报销多久内提交？",
            "expected_text": "差旅报销需要在出差结束后 7 天内提交。",
        },
    ]

    result = evaluate_postgresql_retrieval(
        FakeConnection(),
        questions=questions,
        top_k=2,
        min_score=0.6,
    )

    assert captured_questions == [
        {
            "question": "员工每天需要工作多久？",
            "top_k": 2,
            "min_score": 0.6,
        },
        {
            "question": "差旅报销多久内提交？",
            "top_k": 2,
            "min_score": 0.6,
        },
    ]

    assert result["total"] == 2
    assert result["passed"] == 2
    assert result["hit_rate"] == 1.0
    assert result["top_k"] == 2
    assert result["min_score"] == 0.6

    assert result["items"][0]["passed"] is True
    assert result["items"][0]["expected_text"] == "员工每天需要完成 8 小时工作。"
    assert result["items"][0]["top_result_text"] == "员工每天需要完成 8 小时工作。"

    assert result["items"][1]["passed"] is True
    assert result["items"][1]["expected_text"] == "差旅报销需要在出差结束后 7 天内提交。"


def test_evaluate_postgresql_retrieval_records_failed_item(monkeypatch):
    def fake_search_postgresql_chunks_by_question(
        connection,
        question: str,
        top_k: int,
        min_score: float,
    ):
        return {
            "question": question,
            "embedding_size": 1024,
            "results": [
                {
                    "chunk_id": 1,
                    "document_id": 3,
                    "document_title": "员工手册",
                    "text": "员工每天需要完成 8 小时工作。",
                    "distance": 0.1,
                    "score": 0.9,
                }
            ],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_retrieval.search_postgresql_chunks_by_question",
        fake_search_postgresql_chunks_by_question,
    )

    result = evaluate_postgresql_retrieval(
        FakeConnection(),
        questions=[
            {
                "question": "差旅报销多久内提交？",
                "expected_text": "差旅报销需要在出差结束后 7 天内提交。",
            }
        ],
        top_k=1,
        min_score=0.8,
    )

    assert result["total"] == 1
    assert result["passed"] == 0
    assert result["hit_rate"] == 0.0
    assert result["min_score"] == 0.8

    assert result["items"][0]["passed"] is False
    assert result["items"][0]["top_result_text"] == "员工每天需要完成 8 小时工作。"


def test_evaluate_postgresql_retrieval_for_min_scores(monkeypatch):
    captured_min_scores = []

    def fake_search_postgresql_chunks_by_question(
        connection,
        question: str,
        top_k: int,
        min_score: float,
    ):
        captured_min_scores.append(min_score)

        if min_score <= 0.6:
            return {
                "question": question,
                "embedding_size": 1024,
                "results": [
                    {
                        "chunk_id": 1,
                        "document_id": 3,
                        "document_title": "员工手册",
                        "text": "员工每天需要完成 8 小时工作。",
                        "distance": 0.1,
                        "score": 0.9,
                    }
                ],
            }

        return {
            "question": question,
            "embedding_size": 1024,
            "results": [],
        }

    monkeypatch.setattr(
        "week10.evaluate_postgresql_retrieval.search_postgresql_chunks_by_question",
        fake_search_postgresql_chunks_by_question,
    )

    results = evaluate_postgresql_retrieval_for_min_scores(
        FakeConnection(),
        questions=[
            {
                "question": "员工每天需要工作多久？",
                "expected_text": "员工每天需要完成 8 小时工作。",
            }
        ],
        top_k=2,
        min_scores=[0.0, 0.6, 0.95],
    )

    assert captured_min_scores == [0.0, 0.6, 0.95]

    assert [result["min_score"] for result in results] == [0.0, 0.6, 0.95]
    assert [result["hit_rate"] for result in results] == [1.0, 1.0, 0.0]
