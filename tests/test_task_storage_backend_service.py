from backend.services.task_storage_backend_service import (
    build_task_storage_info,
    get_task_storage_backend,
)


def test_get_task_storage_backend_uses_memory_for_sqlite():
    backend = get_task_storage_backend("sqlite:///data/app.db")

    assert backend == "memory"


def test_get_task_storage_backend_uses_postgresql_for_postgresql_url():
    backend = get_task_storage_backend(
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    assert backend == "postgresql"


def test_build_task_storage_info_for_memory_queue():
    info = build_task_storage_info("sqlite:///data/app.db")

    assert info == {
        "backend": "memory",
        "is_persistent": False,
        "label": "内存任务队列",
        "description": "任务记录只保存在当前后端进程中，后端重启后会丢失。",
    }


def test_build_task_storage_info_for_postgresql_queue():
    info = build_task_storage_info(
        "postgresql://agent_user:agent_password@localhost:5432/agent_db"
    )

    assert info == {
        "backend": "postgresql",
        "is_persistent": True,
        "label": "PostgreSQL 持久化任务队列",
        "description": "任务记录会保存到 PostgreSQL，后端重启后仍然保留。",
    }
