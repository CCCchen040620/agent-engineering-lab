import psycopg

from backend.config import DATABASE_URL
from backend.services.postgresql_embedding_backfill_service import (
    backfill_missing_postgresql_chunk_embeddings,
)
from backend.services.postgresql_schema_service import (
    initialize_postgresql_knowledge_schema,
)


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


def build_default_task_dispatcher() -> TaskDispatcher:
    dispatcher = TaskDispatcher()
    dispatcher.register("echo", lambda payload: payload)
    dispatcher.register(
        "postgresql_embedding_backfill",
        run_postgresql_embedding_backfill,
    )
    return dispatcher