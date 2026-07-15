class TaskExecutionError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def format_task_error(error: Exception) -> str:
    """Format task errors with a stable code prefix for diagnostics."""
    if isinstance(error, TaskExecutionError):
        return f"{error.code}: {error.message}"

    return f"unexpected_error: {error}"
