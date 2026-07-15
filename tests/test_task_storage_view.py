from frontend.task_storage_view import (
    build_task_storage_caption,
    get_task_storage_info,
)


def test_get_task_storage_info_uses_backend_info():
    info = {
        "task_storage": {
            "backend": "postgresql",
            "is_persistent": True,
            "label": "PostgreSQL 持久化任务队列",
            "description": "任务记录会保存到 PostgreSQL，后端重启后仍然保留。",
        }
    }

    task_storage = get_task_storage_info(info)

    assert task_storage["backend"] == "postgresql"
    assert task_storage["is_persistent"] is True


def test_get_task_storage_info_falls_back_from_database_backend():
    info = {
        "database_backend": "postgresql",
    }

    task_storage = get_task_storage_info(info)

    assert task_storage["backend"] == "postgresql"
    assert task_storage["is_persistent"] is True


def test_get_task_storage_info_defaults_to_unknown_without_info():
    task_storage = get_task_storage_info(None)

    assert task_storage["backend"] == "unknown"
    assert task_storage["label"] == "任务存储未知"


def test_build_task_storage_caption():
    caption = build_task_storage_caption(
        {
            "task_storage": {
                "backend": "memory",
                "is_persistent": False,
                "label": "内存任务队列",
                "description": "任务记录只保存在当前后端进程中，后端重启后会丢失。",
            }
        }
    )

    assert caption == (
        "任务存储：内存任务队列 | "
        "任务记录只保存在当前后端进程中，后端重启后会丢失。"
    )
