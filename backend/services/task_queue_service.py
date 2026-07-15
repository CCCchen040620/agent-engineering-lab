from backend.services.task_error_service import format_task_error


VALID_STATUS_TRANSITIONS = {
    "pending": ["running", "failed"],
    "running": ["succeeded", "failed"],
    "succeeded": [],
    "failed": [],
}


class TaskNotFoundError(Exception):
    pass


class InvalidTaskStatusTransitionError(Exception):
    pass


def validate_task_status_transition(task: dict, next_status: str) -> None:
    current_status = task["status"]
    allowed_next_statuses = VALID_STATUS_TRANSITIONS[current_status]

    if next_status not in allowed_next_statuses:
        raise InvalidTaskStatusTransitionError(
            f"Cannot change task {task['id']} from {current_status} to {next_status}."
        )


class InMemoryTaskQueue:
    def __init__(self):
        self.tasks = []
        self.next_id = 1

    def create_task(self, task_type: str, payload: dict) -> dict:
        task = {
            "id": self.next_id,
            "type": task_type,
            "status": "pending",
            "payload": payload,
            "result": {},
            "error": "",
        }

        self.tasks.append(task)
        self.next_id = self.next_id + 1

        return task

    def list_tasks(
        self,
        status: str | None = None,
        order: str = "desc",
        limit: int | None = None,
    ) -> list[dict]:
        if status in (None, ""):
            tasks = list(self.tasks)
        else:
            tasks = [
                task
                for task in self.tasks
                if task["status"] == status
            ]

        sorted_tasks = sorted(
            tasks,
            key=lambda task: task["id"],
            reverse=order == "desc",
        )

        if limit is None:
            return sorted_tasks

        return sorted_tasks[:limit]

    def get_task(self, task_id: int) -> dict | None:
        for task in self.tasks:
            if task["id"] == task_id:
                return task

        return None

    def get_task_or_raise(self, task_id: int) -> dict:
        task = self.get_task(task_id)

        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        return task

    def validate_status_transition(self, task: dict, next_status: str) -> None:
        validate_task_status_transition(task, next_status)

    def mark_task_running(self, task_id: int) -> dict:
        task = self.get_task_or_raise(task_id)
        self.validate_status_transition(task, "running")
        task["status"] = "running"
        return task

    def mark_task_succeeded(self, task_id: int, result: dict) -> dict:
        task = self.get_task_or_raise(task_id)
        self.validate_status_transition(task, "succeeded")
        task["status"] = "succeeded"
        task["result"] = result
        task["error"] = ""
        return task

    def mark_task_failed(self, task_id: int, error: str) -> dict:
        task = self.get_task_or_raise(task_id)
        self.validate_status_transition(task, "failed")
        task["status"] = "failed"
        task["result"] = {}
        task["error"] = error
        return task


class TaskRunner:
    def __init__(self, queue: InMemoryTaskQueue):
        self.queue = queue

    def run_task(self, task_id: int, handler) -> dict:
        task = self.queue.mark_task_running(task_id)

        try:
            result = handler(task["payload"])
            return self.queue.mark_task_succeeded(task_id, result)
        except Exception as error:
            return self.queue.mark_task_failed(
                task_id,
                format_task_error(error),
            )

    def finish_running_task(self, task_id: int, handler) -> dict:
        task = self.queue.get_task_or_raise(task_id)

        try:
            result = handler(task["payload"])
            return self.queue.mark_task_succeeded(task_id, result)
        except Exception as error:
            return self.queue.mark_task_failed(
                task_id,
                format_task_error(error),
            )
