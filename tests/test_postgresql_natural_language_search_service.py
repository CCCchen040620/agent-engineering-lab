from backend.services.postgresql_natural_language_search_service import (
    search_postgresql_chunks_by_question,
)


class FakeConnection:
    pass


def test_search_postgresql_chunks_by_question(monkeypatch):
    captured = {}

    def fake_embed_with_ollama(text: str):
        captured["embedded_text"] = text
        return [0.1, 0.2, 0.3]

    def fake_search_chunks_by_vector_from_postgresql(
        connection,
        query_embedding: list[float],
        top_k: int,
    ):
        captured["connection"] = connection
        captured["query_embedding"] = query_embedding
        captured["top_k"] = top_k

        return [
            {
                "chunk_id": 1,
                "document_id": 2,
                "document_title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "distance": 0.0,
                "score": 1.0,
            }
        ]

    monkeypatch.setattr(
        "backend.services.postgresql_natural_language_search_service.embed_with_ollama",
        fake_embed_with_ollama,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_natural_language_search_service.search_chunks_by_vector_from_postgresql",
        fake_search_chunks_by_vector_from_postgresql,
    )

    connection = FakeConnection()

    result = search_postgresql_chunks_by_question(
        connection,
        question="员工每天需要工作多久？",
        top_k=2,
    )

    assert captured["embedded_text"] == "员工每天需要工作多久？"
    assert captured["connection"] == connection
    assert captured["query_embedding"] == [0.1, 0.2, 0.3]
    assert captured["top_k"] == 2

    assert result == {
        "question": "员工每天需要工作多久？",
        "embedding_size": 3,
        "results": [
            {
                "chunk_id": 1,
                "document_id": 2,
                "document_title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "distance": 0.0,
                "score": 1.0,
            }
        ],
    }


def test_search_postgresql_chunks_by_question_filters_by_min_score(monkeypatch):
    def fake_embed_with_ollama(text: str):
        return [0.1, 0.2, 0.3]

    def fake_search_chunks_by_vector_from_postgresql(
        connection,
        query_embedding: list[float],
        top_k: int,
    ):
        return [
            {
                "chunk_id": 1,
                "document_id": 2,
                "document_title": "员工手册",
                "text": "员工每天需要完成 8 小时工作。",
                "distance": 0.1,
                "score": 0.9,
            },
            {
                "chunk_id": 2,
                "document_id": 3,
                "document_title": "报销制度",
                "text": "差旅报销需要在出差结束后 7 天内提交。",
                "distance": 0.6,
                "score": 0.4,
            },
        ]

    monkeypatch.setattr(
        "backend.services.postgresql_natural_language_search_service.embed_with_ollama",
        fake_embed_with_ollama,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_natural_language_search_service.search_chunks_by_vector_from_postgresql",
        fake_search_chunks_by_vector_from_postgresql,
    )

    result = search_postgresql_chunks_by_question(
        FakeConnection(),
        question="员工每天需要工作多久？",
        top_k=2,
        min_score=0.6,
    )

    assert result["results"] == [
        {
            "chunk_id": 1,
            "document_id": 2,
            "document_title": "员工手册",
            "text": "员工每天需要完成 8 小时工作。",
            "distance": 0.1,
            "score": 0.9,
        }
    ]
