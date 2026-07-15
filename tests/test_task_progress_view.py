from frontend.task_progress_view import (
    build_task_progress_text,
    clamp_progress_percent,
)


def test_build_task_progress_text():
    task = {
        "progress_percent": 50,
        "progress_message": "任务运行中",
    }

    assert build_task_progress_text(task) == "50% | 任务运行中"


def test_build_task_progress_text_returns_message_without_percent():
    task = {
        "progress_message": "任务运行中",
    }

    assert build_task_progress_text(task) == "任务运行中"


def test_build_task_progress_text_returns_empty_when_missing():
    assert build_task_progress_text({}) == ""


def test_clamp_progress_percent():
    assert clamp_progress_percent(-1) == 0
    assert clamp_progress_percent(50) == 50
    assert clamp_progress_percent(101) == 100
