from frontend.task_result_summary import summarize_task_result_as_text
from frontend.task_failure_view import summarize_task_failure_as_text
from frontend.task_progress_view import build_task_progress_text


TASK_STATUS_FILTER_OPTIONS = [
    "全部",
    "pending",
    "running",
    "succeeded",
    "failed",
    "canceled",
]


def filter_tasks_by_status(tasks: list[dict], status_filter: str) -> list[dict]:
    """Filter tasks by status for the task admin page."""
    if status_filter in ("", "全部"):
        return list(tasks)

    return [
        task
        for task in tasks
        if task.get("status") == status_filter
    ]


def sort_tasks_by_id(
    tasks: list[dict],
    newest_first: bool = True,
) -> list[dict]:
    """Sort tasks by id so recent tasks can appear first."""
    return sorted(
        tasks,
        key=lambda task: task.get("id", 0),
        reverse=newest_first,
    )


def build_task_retry_source_text(task: dict) -> str:
    retry_of_task_id = task.get("retry_of_task_id")

    if retry_of_task_id is None:
        return ""

    return f"重试自任务 #{retry_of_task_id}"


def build_task_attempt_summary_text(task: dict) -> str:
    run_count = task.get("run_count", 0)
    retry_count = task.get("retry_count", 0)

    return f"运行次数: {run_count} | 派生重试次数: {retry_count}"


def build_task_list_rows(
    tasks: list[dict],
    status_filter: str = "全部",
    newest_first: bool = True,
) -> list[dict]:
    """Build display rows for Streamlit task list."""
    filtered_tasks = filter_tasks_by_status(tasks, status_filter)
    sorted_tasks = sort_tasks_by_id(filtered_tasks, newest_first)

    display_tasks = []

    for task in sorted_tasks:
        display_task = dict(task)
        display_task["retry_source_summary"] = build_task_retry_source_text(task)
        display_task["attempt_summary"] = build_task_attempt_summary_text(task)
        display_task["progress_summary"] = build_task_progress_text(task)
        display_task["result_summary"] = summarize_task_result_as_text(task)
        display_task["failure_summary"] = summarize_task_failure_as_text(task)
        display_tasks.append(display_task)

    return display_tasks
