import pytest

from backend.services.task_dispatcher_service import (
    UnsupportedTaskTypeError,
    TaskDispatcher,
)


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
