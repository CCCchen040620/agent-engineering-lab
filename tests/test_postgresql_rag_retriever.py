from backend.services.postgresql_rag_retriever import (
    retrieve_postgresql_snippets,
)


class FakeConnection:
    pass


def test_retrieve_postgresql_snippets(monkeypatch):
    captured = {}

    def fake_search_postgresql_chunks_by_question(
        connection,
        question: str,
        top_k: int,
    ):
        captured["connection"] = connection
        captured["question"] = question
        captured["top_k"] = top_k

        return {
            "question": question,
            "embedding_size": 1024,
            "results": [
                {
                    "chunk_id": 2,
                    "document_id": 3,
                    "document_title": "员工手册",
                    "text": "员工每天需要完成 8 小时工作。",
                    "distance": 0.1337,
                    "score": 0.8663,
                },
                {
                    "chunk_id": 3,
                    "document_id": 3,
                    "document_title": "报销制度",
                    "text": "差旅报销需要在出差结束后 7 天内提交。",
                    "distance": 0.5,
                    "score": 0.5,
                },
            ],
        }

    monkeypatch.setattr(
        "backend.services.postgresql_rag_retriever.search_postgresql_chunks_by_question",
        fake_search_postgresql_chunks_by_question,
    )

    connection = FakeConnection()

    snippets = retrieve_postgresql_snippets(
        connection,
        question="员工每天需要工作多久？",
        top_k=2,
    )

    assert captured["connection"] == connection
    assert captured["question"] == "员工每天需要工作多久？"
    assert captured["top_k"] == 2

    assert snippets == [
        {
            "title": "员工手册",
            "path": "postgresql://chunk/2",
            "text": "员工每天需要完成 8 小时工作。",
            "score": 0.8663,
        },
        {
            "title": "报销制度",
            "path": "postgresql://chunk/3",
            "text": "差旅报销需要在出差结束后 7 天内提交。",
            "score": 0.5,
        },
    ]


def test_retrieve_postgresql_snippets_returns_empty_list(monkeypatch):
    def fake_search_postgresql_chunks_by_question(
        connection,
        question: str,
        top_k: int,
    ):
        return {
            "question": question,
            "embedding_size": 1024,
            "results": [],
        }

    monkeypatch.setattr(
        "backend.services.postgresql_rag_retriever.search_postgresql_chunks_by_question",
        fake_search_postgresql_chunks_by_question,
    )

    snippets = retrieve_postgresql_snippets(
        FakeConnection(),
        question="公司有没有股票期权？",
        top_k=3,
    )

    assert snippets == []