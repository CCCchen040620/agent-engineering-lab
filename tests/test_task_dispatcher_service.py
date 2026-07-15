import pytest

from backend.services.task_dispatcher_service import (
    UnsupportedTaskTypeError,
    TaskDispatcher,
    build_postgresql_document_ingestion_result,
    get_required_payload_string,
)
from backend.services.task_error_service import TaskExecutionError


class FakePostgreSQLConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_task_dispatcher_runs_registered_handler():
    dispatcher = TaskDispatcher()

    dispatcher.register(
        "echo",
        lambda payload: {"echo": payload["message"]},
    )

    result = dispatcher.dispatch(
        task_type="echo",
        payload={"message": "hello"},
    )

    assert result == {"echo": "hello"}


def test_task_dispatcher_raises_error_for_unsupported_task_type():
    dispatcher = TaskDispatcher()

    with pytest.raises(UnsupportedTaskTypeError):
        dispatcher.dispatch(
            task_type="unknown_task",
            payload={},
        )


def test_build_default_task_dispatcher_supports_postgresql_embedding_backfill(monkeypatch):
    from backend.services import task_dispatcher_service

    monkeypatch.setattr(
        task_dispatcher_service.psycopg,
        "connect",
        lambda database_url: FakePostgreSQLConnection(),
    )
    monkeypatch.setattr(
        task_dispatcher_service,
        "initialize_postgresql_knowledge_schema",
        lambda connection: None,
    )

    def fake_backfill_missing_postgresql_chunk_embeddings(connection):
        return {
            "total_chunks": 3,
            "updated_embeddings": 2,
            "skipped_embeddings": 1,
            "model": "fake-model",
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "backfill_missing_postgresql_chunk_embeddings",
        fake_backfill_missing_postgresql_chunk_embeddings,
    )

    dispatcher = task_dispatcher_service.build_default_task_dispatcher()

    result = dispatcher.dispatch(
        task_type="postgresql_embedding_backfill",
        payload={},
    )

    assert result == {
        "total_chunks": 3,
        "updated_embeddings": 2,
        "skipped_embeddings": 1,
        "model": "fake-model",
    }


def test_get_required_payload_string_returns_trimmed_value():
    value = get_required_payload_string(
        {"title": "  PostgreSQL 入库文档  "},
        "title",
    )

    assert value == "PostgreSQL 入库文档"


def test_get_required_payload_string_raises_invalid_payload_when_missing():
    with pytest.raises(TaskExecutionError) as error:
        get_required_payload_string({}, "title")

    assert error.value.code == "invalid_payload"
    assert "Missing required payload field: title" in str(error.value)


def test_build_postgresql_document_ingestion_result_flattens_indexing_result():
    result = build_postgresql_document_ingestion_result(
        {
            "document": {
                "id": 7,
                "title": "PostgreSQL 入库任务文档",
                "file_type": "md",
                "chunk_count": 2,
                "is_indexed": True,
                "source": "production",
            },
            "chunks": [
                {"id": 1},
                {"id": 2},
            ],
            "embeddings": [
                {"id": 1},
                {"id": 2},
            ],
        }
    )

    assert result == {
        "document_id": 7,
        "title": "PostgreSQL 入库任务文档",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "production",
        "embedding_count": 2,
    }


def test_build_postgresql_document_ingestion_result_raises_when_not_created():
    with pytest.raises(TaskExecutionError) as error:
        build_postgresql_document_ingestion_result(None)

    assert error.value.code == "duplicate_document"
    assert "duplicate title or empty content" in str(error.value)


def test_build_default_task_dispatcher_supports_postgresql_document_ingestion(
    monkeypatch,
):
    from backend.services import task_dispatcher_service

    captured = {}

    monkeypatch.setattr(
        task_dispatcher_service.psycopg,
        "connect",
        lambda database_url: FakePostgreSQLConnection(),
    )
    monkeypatch.setattr(
        task_dispatcher_service,
        "initialize_postgresql_knowledge_schema",
        lambda connection: captured.update({"schema_initialized": True}),
    )

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        captured["title"] = title
        captured["file_type"] = file_type
        captured["content"] = content
        captured["source"] = source

        return {
            "document": {
                "id": 7,
                "title": title,
                "file_type": file_type,
                "chunk_count": 2,
                "is_indexed": True,
                "source": source,
            },
            "chunks": [
                {"id": 1},
                {"id": 2},
            ],
            "embeddings": [
                {"id": 1},
                {"id": 2},
            ],
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    dispatcher = task_dispatcher_service.build_default_task_dispatcher()

    result = dispatcher.dispatch(
        task_type="postgresql_document_ingestion",
        payload={
            "title": " PostgreSQL 入库任务文档 ",
            "file_type": "md",
            "content": " 员工参加外部培训需要提前提交申请。 ",
            "source": "production",
        },
    )

    assert captured == {
        "schema_initialized": True,
        "title": "PostgreSQL 入库任务文档",
        "file_type": "md",
        "content": "员工参加外部培训需要提前提交申请。",
        "source": "production",
    }
    assert result == {
        "document_id": 7,
        "title": "PostgreSQL 入库任务文档",
        "file_type": "md",
        "chunk_count": 2,
        "is_indexed": True,
        "source": "production",
        "embedding_count": 2,
    }


def test_postgresql_document_ingestion_uses_production_source_by_default(
    monkeypatch,
):
    from backend.services import task_dispatcher_service

    captured = {}

    monkeypatch.setattr(
        task_dispatcher_service.psycopg,
        "connect",
        lambda database_url: FakePostgreSQLConnection(),
    )
    monkeypatch.setattr(
        task_dispatcher_service,
        "initialize_postgresql_knowledge_schema",
        lambda connection: None,
    )

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        captured["source"] = source

        return {
            "document": {
                "id": 8,
                "title": title,
                "file_type": file_type,
                "chunk_count": 1,
                "is_indexed": True,
                "source": source,
            },
            "chunks": [{"id": 1}],
            "embeddings": [{"id": 1}],
        }

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    dispatcher = task_dispatcher_service.build_default_task_dispatcher()

    dispatcher.dispatch(
        task_type="postgresql_document_ingestion",
        payload={
            "title": "默认来源文档",
            "file_type": "md",
            "content": "默认来源测试。",
        },
    )

    assert captured["source"] == "production"


def test_postgresql_document_ingestion_raises_embedding_error_when_indexing_fails(
    monkeypatch,
):
    from backend.services import task_dispatcher_service

    monkeypatch.setattr(
        task_dispatcher_service.psycopg,
        "connect",
        lambda database_url: FakePostgreSQLConnection(),
    )
    monkeypatch.setattr(
        task_dispatcher_service,
        "initialize_postgresql_knowledge_schema",
        lambda connection: None,
    )

    def fake_create_postgresql_document_with_chunks_and_embeddings(
        connection,
        title: str,
        file_type: str,
        content: str,
        source: str,
    ):
        raise RuntimeError("Ollama embedding model unavailable")

    monkeypatch.setattr(
        task_dispatcher_service,
        "create_postgresql_document_with_chunks_and_embeddings",
        fake_create_postgresql_document_with_chunks_and_embeddings,
    )

    dispatcher = task_dispatcher_service.build_default_task_dispatcher()

    with pytest.raises(TaskExecutionError) as error:
        dispatcher.dispatch(
            task_type="postgresql_document_ingestion",
            payload={
                "title": "Embedding failure document",
                "file_type": "md",
                "content": "Embedding failure content.",
            },
        )

    assert error.value.code == "embedding_generation_error"
    assert "Ollama embedding model unavailable" in str(error.value)
