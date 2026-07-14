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

    def list_tasks(self) -> list[dict]:
        return self.tasks

    def get_task(self, task_id: int) -> dict | None:
        for task in self.tasks:
            if task["id"] == task_id:
                return task

        return None

    def mark_task_running(self, task_id: int) -> dict:
        task = self.get_task(task_id)
        task["status"] = "running"
        return task

    def mark_task_succeeded(self, task_id: int, result: dict) -> dict:
        task = self.get_task(task_id)
        task["status"] = "succeeded"
        task["result"] = result
        task["error"] = ""
        return task

    def mark_task_failed(self, task_id: int, error: str) -> dict:
        task = self.get_task(task_id)
        task["status"] = "failed"
        task["result"] = {}
        task["error"] = error
        return task