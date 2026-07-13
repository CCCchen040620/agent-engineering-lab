from backend.services.postgresql_embedding_backfill_service import (
    backfill_missing_postgresql_chunk_embeddings,
)


class FakeConnection:
    pass


def test_backfill_missing_postgresql_chunk_embeddings(monkeypatch):
    captured = {
        "embedded_texts": [],
        "upserted": [],
    }

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

    def fake_find_embedding(connection, chunk_id: int):
        if chunk_id == 1:
            return {
                "id": 100,
                "chunk_id": 1,
                "embedding": [0.1, 0.2, 0.3],
                "model": "bge-m3:latest",
            }

        return None

    def fake_embed_with_ollama(text: str, model: str):
        captured["embedded_texts"].append(text)
        captured["model"] = model
        return [0.4, 0.5, 0.6]

    def fake_upsert_embedding(
        connection,
        chunk_id: int,
        embedding: list[float],
        model: str,
    ):
        captured["upserted"].append(
            {
                "chunk_id": chunk_id,
                "embedding": embedding,
                "model": model,
            }
        )

        return {
            "id": 200,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "model": model,
        }

    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service."
        "list_all_chunks_from_postgresql",
        fake_list_all_chunks,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service."
        "find_chunk_embedding_by_chunk_id_from_postgresql",
        fake_find_embedding,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service.embed_with_ollama",
        fake_embed_with_ollama,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service."
        "upsert_chunk_embedding_to_postgresql",
        fake_upsert_embedding,
    )

    result = backfill_missing_postgresql_chunk_embeddings(
        FakeConnection(),
        model="bge-m3:latest",
    )

    assert captured["embedded_texts"] == [
        "新员工入职后需要在 30 天内完成安全培训。"
    ]
    assert captured["model"] == "bge-m3:latest"
    assert captured["upserted"] == [
        {
            "chunk_id": 2,
            "embedding": [0.4, 0.5, 0.6],
            "model": "bge-m3:latest",
        }
    ]

    assert result == {
        "total_chunks": 2,
        "updated": 1,
        "skipped": 1,
        "model": "bge-m3:latest",
    }


def test_backfill_missing_postgresql_chunk_embeddings_skips_all_existing(
    monkeypatch,
):
    def fake_list_all_chunks(connection):
        return [
            {
                "id": 1,
                "document_id": 10,
                "text": "员工每天需要完成 8 小时工作。",
                "chunk_index": 0,
            }
        ]

    def fake_find_embedding(connection, chunk_id: int):
        return {
            "id": 100,
            "chunk_id": chunk_id,
            "embedding": [0.1, 0.2, 0.3],
            "model": "bge-m3:latest",
        }

    def fake_embed_with_ollama(text: str, model: str):
        raise AssertionError("existing embeddings should not be regenerated")

    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service."
        "list_all_chunks_from_postgresql",
        fake_list_all_chunks,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service."
        "find_chunk_embedding_by_chunk_id_from_postgresql",
        fake_find_embedding,
    )
    monkeypatch.setattr(
        "backend.services.postgresql_embedding_backfill_service.embed_with_ollama",
        fake_embed_with_ollama,
    )

    result = backfill_missing_postgresql_chunk_embeddings(
        FakeConnection(),
        model="bge-m3:latest",
    )

    assert result == {
        "total_chunks": 1,
        "updated": 0,
        "skipped": 1,
        "model": "bge-m3:latest",
    }
