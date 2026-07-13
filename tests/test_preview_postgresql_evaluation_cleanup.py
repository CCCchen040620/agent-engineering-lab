from week10.preview_postgresql_evaluation_cleanup import (
    preview_postgresql_evaluation_cleanup,
)


class FakeConnection:
    pass


def test_preview_postgresql_evaluation_cleanup(monkeypatch):
    captured = {}

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_summarize_documents(connection, source: str):
        captured["source"] = source

        return {
            "source": source,
            "document_count": 1,
            "chunk_count": 2,
            "embedding_count": 2,
            "documents": [
                {
                    "id": 1,
                    "title": "Evaluation Doc",
                }
            ],
        }

    monkeypatch.setattr(
        "week10.preview_postgresql_evaluation_cleanup.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "week10.preview_postgresql_evaluation_cleanup.summarize_documents_by_source_from_postgresql",
        fake_summarize_documents,
    )

    preview = preview_postgresql_evaluation_cleanup(FakeConnection())

    assert captured["schema_initialized"] is True
    assert captured["source"] == "evaluation"
    assert preview == {
        "source": "evaluation",
        "document_count": 1,
        "chunk_count": 2,
        "embedding_count": 2,
        "documents": [
            {
                "id": 1,
                "title": "Evaluation Doc",
            }
        ],
    }


def test_preview_postgresql_evaluation_cleanup_can_use_custom_source(monkeypatch):
    captured = {}

    def fake_initialize_schema(connection):
        captured["schema_initialized"] = True

    def fake_summarize_documents(connection, source: str):
        captured["source"] = source

        return {
            "source": source,
            "document_count": 0,
            "chunk_count": 0,
            "embedding_count": 0,
            "documents": [],
        }

    monkeypatch.setattr(
        "week10.preview_postgresql_evaluation_cleanup.initialize_postgresql_knowledge_schema",
        fake_initialize_schema,
    )
    monkeypatch.setattr(
        "week10.preview_postgresql_evaluation_cleanup.summarize_documents_by_source_from_postgresql",
        fake_summarize_documents,
    )

    preview = preview_postgresql_evaluation_cleanup(
        FakeConnection(),
        source="sandbox",
    )

    assert captured["schema_initialized"] is True
    assert captured["source"] == "sandbox"
    assert preview["source"] == "sandbox"
    assert preview["documents"] == []
