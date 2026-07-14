from week10.backfill_postgresql_chunk_embeddings import (
    backfill_postgresql_chunk_embeddings,
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
    return backfill_postgresql_chunk_embeddings()


def build_default_task_dispatcher() -> TaskDispatcher:
    dispatcher = TaskDispatcher()
    dispatcher.register("echo", lambda payload: payload)
    dispatcher.register(
        "postgresql_embedding_backfill",
        run_postgresql_embedding_backfill,
    )
    return dispatcher