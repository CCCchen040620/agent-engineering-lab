def get_task_storage_info(info: dict | None) -> dict:
    if info is None:
        return {
            "backend": "unknown",
            "is_persistent": False,
            "label": "任务存储未知",
            "description": "暂时无法读取后端任务存储配置。",
        }

    task_storage = info.get("task_storage")

    if isinstance(task_storage, dict):
        return task_storage

    if info.get("database_backend") == "postgresql":
        return {
            "backend": "postgresql",
            "is_persistent": True,
            "label": "PostgreSQL 持久化任务队列",
            "description": "任务记录会保存到 PostgreSQL，后端重启后仍然保留。",
        }

    return {
        "backend": "memory",
        "is_persistent": False,
        "label": "内存任务队列",
        "description": "任务记录只保存在当前后端进程中，后端重启后会丢失。",
    }


def build_task_storage_caption(info: dict | None) -> str:
    task_storage = get_task_storage_info(info)

    return f"任务存储：{task_storage['label']} | {task_storage['description']}"
