import pytest

from backend.services.rag_retriever_service import retrieve_rag_snippets


class FakePostgresqlConnection:
    pass


def test_retrieve_rag_snippets_from_sqlite(monkeypatch):
    captured = {}

    def fake_search_sqlite_snippets(
        question: str,
        database_path: str,
        top_k: int,
        mode: str,
        min_score: float,
    ):
        captured["question"] = question
        captured["database_path"] = database_path
        captured["top_k"] = top_k
        captured["mode"] = mode
        captured["min_score"] = min_score

        return (
            "安全培训",
            [
                {
                    "title": "员工手册",
                    "path": "sqlite://1",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "score": 0.9,
                }
            ],
        )

    monkeypatch.setattr(
        "backend.services.rag_retriever_service.search_sqlite_snippets",
        fake_search_sqlite_snippets,
    )

    snippets = retrieve_rag_snippets(
        backend="sqlite",
        question="新员工什么时候完成安全培训？",
        sqlite_database_path="data/app.db",
        top_k=2,
        mode="precomputed_embedding",
        min_score=0.6,
    )

    assert captured == {
        "question": "新员工什么时候完成安全培训？",
        "database_path": "data/app.db",
        "top_k": 2,
        "mode": "precomputed_embedding",
        "min_score": 0.6,
    }

    assert snippets == [
        {
            "title": "员工手册",
            "path": "sqlite://1",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
            "score": 0.9,
        }
    ]


def test_retrieve_rag_snippets_from_postgresql(monkeypatch):
    captured = {}

    def fake_retrieve_postgresql_snippets(
        connection,
        question: str,
        top_k: int,
        min_score: float,
    ):
        captured["connection"] = connection
        captured["question"] = question
        captured["top_k"] = top_k
        captured["min_score"] = min_score

        return [
            {
                "title": "员工手册",
                "path": "postgresql://chunk/2",
                "text": "员工每天需要完成 8 小时工作。",
                "score": 0.866,
            }
        ]

    monkeypatch.setattr(
        "backend.services.rag_retriever_service.retrieve_postgresql_snippets",
        fake_retrieve_postgresql_snippets,
    )

    connection = FakePostgresqlConnection()

    snippets = retrieve_rag_snippets(
        backend="postgresql",
        question="员工每天需要工作多久？",
        postgresql_connection=connection,
        top_k=2,
        min_score=0.6,
    )

    assert captured == {
        "connection": connection,
        "question": "员工每天需要工作多久？",
        "top_k": 2,
        "min_score": 0.6,
    }

    assert snippets == [
        {
            "title": "员工手册",
            "path": "postgresql://chunk/2",
            "text": "员工每天需要完成 8 小时工作。",
            "score": 0.866,
        }
    ]


def test_retrieve_rag_snippets_requires_postgresql_connection():
    with pytest.raises(ValueError) as error:
        retrieve_rag_snippets(
            backend="postgresql",
            question="员工每天需要工作多久？",
        )

    assert "postgresql_connection is required" in str(error.value)


def test_retrieve_rag_snippets_rejects_unknown_backend():
    with pytest.raises(ValueError) as error:
        retrieve_rag_snippets(
            backend="unknown",
            question="员工每天需要工作多久？",
        )

    assert "Unsupported retriever backend" in str(error.value)


def test_retrieve_rag_snippets_uses_default_sqlite_backend(monkeypatch):
    captured = {}

    def fake_search_sqlite_snippets(
        question: str,
        database_path: str,
        top_k: int,
        mode: str,
        min_score: float,
    ):
        captured["question"] = question
        captured["database_path"] = database_path
        captured["top_k"] = top_k
        captured["mode"] = mode
        captured["min_score"] = min_score

        return (
            "安全培训",
            [
                {
                    "title": "员工手册",
                    "path": "sqlite://1",
                    "text": "新员工入职后需要在 30 天内完成安全培训。",
                    "score": 0.9,
                }
            ],
        )

    monkeypatch.setattr(
        "backend.services.rag_retriever_service.search_sqlite_snippets",
        fake_search_sqlite_snippets,
    )

    snippets = retrieve_rag_snippets(
        question="新员工什么时候完成安全培训？",
    )

    assert captured["question"] == "新员工什么时候完成安全培训？"
    assert captured["database_path"] == "data/app.db"
    assert captured["top_k"] == 3
    assert captured["mode"] == "precomputed_embedding"
    assert captured["min_score"] == 0.3

    assert snippets == [
        {
            "title": "员工手册",
            "path": "sqlite://1",
            "text": "新员工入职后需要在 30 天内完成安全培训。",
            "score": 0.9,
        }
    ]