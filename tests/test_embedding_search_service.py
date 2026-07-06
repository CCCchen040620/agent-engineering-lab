from backend.services.embedding_search_service import search_chunks_by_embedding


def test_search_chunks_by_embedding_returns_most_similar_chunk():
    chunks = [
        {"text": "员工可以远程办公。"},
        {"text": "员工需要提交发票。"},
    ]

    embeddings = {
        "远程办公怎么申请？": [1.0, 0.0],
        "员工可以远程办公。": [0.9, 0.1],
        "员工需要提交发票。": [0.0, 1.0],
    }

    def fake_embedder(text: str) -> list[float]:
        return embeddings[text]

    results = search_chunks_by_embedding(
        query="远程办公怎么申请？",
        chunks=chunks,
        top_k=1,
        embedder=fake_embedder,
    )

    assert len(results) == 1
    assert results[0]["text"] == "员工可以远程办公。"
    assert results[0]["score"] > 0.9


def test_search_chunks_by_embedding_respects_top_k():
    chunks = [
        {"text": "片段1"},
        {"text": "片段2"},
        {"text": "片段3"},
    ]

    embeddings = {
        "问题": [1.0, 0.0],
        "片段1": [1.0, 0.0],
        "片段2": [0.8, 0.2],
        "片段3": [0.0, 1.0],
    }

    def fake_embedder(text: str) -> list[float]:
        return embeddings[text]

    results = search_chunks_by_embedding(
        query="问题",
        chunks=chunks,
        top_k=2,
        embedder=fake_embedder,
    )

    assert len(results) == 2
    assert results[0]["text"] == "片段1"
    assert results[1]["text"] == "片段2"