from frontend.task_event_view import (
    build_task_event_detail_text,
    build_task_event_timeline_rows,
    get_task_event_label,
)


def test_get_task_event_label():
    assert get_task_event_label("task_started") == "开始运行"
    assert get_task_event_label("custom_event") == "custom_event"


def test_build_task_event_detail_text_for_failed_event():
    event = {
        "event_type": "task_failed",
        "metadata": {
            "error": "embedding_generation_error: Ollama embedding model unavailable",
        },
    }

    detail_text = build_task_event_detail_text(event)

    assert "失败原因：embedding_generation_error" in detail_text
    assert "Ollama embedding model unavailable" in detail_text
    assert "Ollama" in detail_text


def test_build_task_event_detail_text_for_retry_event():
    event = {
        "event_type": "task_retry_created",
        "metadata": {
            "retry_count": 2,
            "retry_task_id": 9,
        },
    }

    assert build_task_event_detail_text(event) == "已派生第 2 次重试任务：#9。"


def test_build_task_event_timeline_rows():
    events = [
        {
            "id": 1,
            "task_id": 7,
            "event_type": "task_created",
            "message": "Task created.",
            "metadata": {},
            "created_at": "2026-07-15T10:00:00",
        },
        {
            "id": 2,
            "task_id": 7,
            "event_type": "task_started",
            "message": "Task started.",
            "metadata": {"run_count": 1},
            "created_at": "2026-07-15T10:01:00",
        },
    ]

    rows = build_task_event_timeline_rows(events)

    assert rows == [
        {
            "id": 1,
            "task_id": 7,
            "event_type": "task_created",
            "event_label": "创建任务",
            "summary": "普通任务已创建。",
            "created_at": "2026-07-15T10:00:00",
        },
        {
            "id": 2,
            "task_id": 7,
            "event_type": "task_started",
            "event_label": "开始运行",
            "summary": "任务开始运行，本次为第 1 次运行。",
            "created_at": "2026-07-15T10:01:00",
        },
    ]
