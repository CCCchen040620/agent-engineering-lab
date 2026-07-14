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