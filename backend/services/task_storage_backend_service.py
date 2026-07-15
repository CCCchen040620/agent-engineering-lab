from backend.services.database_url_service import is_postgresql_database


def get_task_storage_backend(database_url: str) -> str:
    if is_postgresql_database(database_url):
        return "postgresql"

    return "memory"


def build_task_storage_info(database_url: str) -> dict:
    backend = get_task_storage_backend(database_url)

    if backend == "postgresql":
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
