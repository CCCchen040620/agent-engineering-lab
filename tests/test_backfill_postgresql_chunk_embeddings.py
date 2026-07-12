from week10.backfill_postgresql_chunk_embeddings import (
    backfill_postgresql_chunk_embeddings,
)


class FakeConnection:
    pass


def test_backfill_postgresql_chunk_embeddings(monkeypatch):
    captured = {
        "embedded_texts": [],
        "upserted": [],
    }

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_list_all_chunks(connection):
        return [
            {
                "id": 1,
                "document_id": 10,
                "text": "员工每天需要完成 8 小时工作。",
                "chunk_index": 0,
            },
            {
                "id": 2,
                "document_id": 10,
                "text": "新员工入职后需要在 30 天内完成安全培训。",
                "chunk_index": 1,
            },
        ]

    def fake_embed_with_ollama(text: str, model: str):
        captured["embedded_texts"].append(text)
        captured["embedding_model"] = model
        return [0.1, 0.2, 0.3]

    def fake_upsert_embedding(connection, chunk_id: int, embedding: list[float], model: str):
        captured["upserted"].append(
            {
                "chunk_id": chunk_id,
                "embedding": embedding,
                "model": model,
            }
        )

        return {
            "id": chunk_id,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "model": model,
        }

    monkeypatch.setattr(
        "week10.backfill_postgresql_chunk_embeddings.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "week10.backfill_postgresql_chunk_embeddings.list_all_chunks_from_postgresql",
        fake_list_all_chunks,
    )
    monkeypatch.setattr(
        "week10.backfill_postgresql_chunk_embeddings.embed_with_ollama",
        fake_embed_with_ollama,
    )
    monkeypatch.setattr(
        "week10.backfill_postgresql_chunk_embeddings.upsert_chunk_embedding_to_postgresql",
        fake_upsert_embedding,
    )

    result = backfill_postgresql_chunk_embeddings(
        FakeConnection(),
        model="bge-m3:latest",
    )

    assert captured["schema_initialized"] is True

    assert captured["embedded_texts"] == [
        "员工每天需要完成 8 小时工作。",
        "新员工入职后需要在 30 天内完成安全培训。",
    ]

    assert captured["embedding_model"] == "bge-m3:latest"

    assert captured["upserted"] == [
        {
            "chunk_id": 1,
            "embedding": [0.1, 0.2, 0.3],
            "model": "bge-m3:latest",
        },
        {
            "chunk_id": 2,
            "embedding": [0.1, 0.2, 0.3],
            "model": "bge-m3:latest",
        },
    ]

    assert result == {
        "total_chunks": 2,
        "updated_embeddings": 2,
        "model": "bge-m3:latest",
    }