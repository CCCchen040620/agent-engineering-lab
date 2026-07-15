import psycopg

from backend.config import DATABASE_URL
from backend.services.postgresql_embedding_backfill_service import (
    backfill_missing_postgresql_chunk_embeddings,
)
from backend.services.postgresql_document_indexing_service import (
    create_postgresql_document_with_chunks_and_embeddings,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)
from backend.services.task_error_service import TaskExecutionError


class UnsupportedTaskTypeError(Exception):
    pass


class TaskDispatcher:
    def __init__(self):
        self.handlers = {}

    def register(self, task_type: str, handler):
        self.handlers[task_type] = handler

    def dispatch(self, task_type: str, payload: dict) -> dict:
        handler = self.handlers.get(task_type)

        if handler is None:
            raise UnsupportedTaskTypeError(f"Unsupported task type: {task_type}")

        return handler(payload)


def run_postgresql_embedding_backfill(payload: dict) -> dict:
    with psycopg.connect(DATABASE_URL) as connection:
        initialize_postgresql_knowledge_schema(connection)
        return backfill_missing_postgresql_chunk_embeddings(connection)


def get_required_payload_string(payload: dict, field_name: str) -> str:
    value = payload.get(field_name)

    if not isinstance(value, str) or value.strip() == "":
        raise TaskExecutionError(
            "invalid_payload",
            f"Missing required payload field: {field_name}",
        )

    return value.strip()


def build_postgresql_document_ingestion_result(indexing_result: dict | None) -> dict:
    if indexing_result is None:
        raise TaskExecutionError(
            "duplicate_document",
            "PostgreSQL document ingestion failed: duplicate title or empty content.",
        )

    document = indexing_result["document"]

    return {
        "document_id": document["id"],
        "title": document["title"],
        "file_type": document["file_type"],
        "chunk_count": document["chunk_count"],
        "is_indexed": document["is_indexed"],
        "source": document.get("source", "production"),
        "embedding_count": len(indexing_result["embeddings"]),
    }


def run_postgresql_document_ingestion(payload: dict) -> dict:
    title = get_required_payload_string(payload, "title")
    file_type = get_required_payload_string(payload, "file_type")
    content = get_required_payload_string(payload, "content")
    source = payload.get("source", "production")

    try:
        with psycopg.connect(DATABASE_URL) as connection:
            initialize_postgresql_knowledge_schema(connection)
            indexing_result = create_postgresql_document_with_chunks_and_embeddings(
                connection,
                title=title,
                file_type=file_type,
                content=content,
                source=source,
            )
    except TaskExecutionError:
        raise
    except psycopg.OperationalError as error:
        raise TaskExecutionError(
            "postgresql_connection_error",
            str(error),
        ) from error
    except Exception as error:
        error_message = str(error)
        error_message_lower = error_message.lower()

        if "embedding" in error_message_lower or "ollama" in error_message_lower:
            raise TaskExecutionError(
                "embedding_generation_error",
                error_message,
            ) from error

        raise

    return build_postgresql_document_ingestion_result(indexing_result)


def build_default_task_dispatcher() -> TaskDispatcher:
    dispatcher = TaskDispatcher()
    dispatcher.register("echo", lambda payload: payload)
    dispatcher.register(
        "postgresql_embedding_backfill",
        run_postgresql_embedding_backfill,
    )
    dispatcher.register(
        "postgresql_document_ingestion",
        run_postgresql_document_ingestion,
    )
    return dispatcher
