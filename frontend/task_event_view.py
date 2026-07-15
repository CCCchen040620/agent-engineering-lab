from frontend.task_failure_view import (
    get_task_failure_suggestion,
    parse_task_error,
)


TASK_EVENT_LABELS = {
    "task_created": "创建任务",
    "task_started": "开始运行",
    "task_succeeded": "执行成功",
    "task_failed": "执行失败",
    "task_canceled": "取消任务",
    "task_retry_created": "创建重试",
}


def get_task_event_label(event_type: str) -> str:
    return TASK_EVENT_LABELS.get(event_type, event_type)


def build_task_event_detail_text(event: dict) -> str:
    event_type = event.get("event_type", "")
    metadata = event.get("metadata") or {}

    if event_type == "task_created":
        retry_of_task_id = metadata.get("retry_of_task_id")

        if retry_of_task_id is None:
            return "普通任务已创建。"

        return f"重试任务已创建，来源任务 #{retry_of_task_id}。"

    if event_type == "task_started":
        run_count = metadata.get("run_count", 0)
        return f"任务开始运行，本次为第 {run_count} 次运行。"

    if event_type == "task_succeeded":
        result = metadata.get("result") or {}

        if result == {}:
            return "任务执行成功。"

        return f"任务执行成功，结果字段：{', '.join(result.keys())}。"

    if event_type == "task_failed":
        parsed_error = parse_task_error(metadata.get("error", ""))
        error_code = parsed_error["code"]

        if error_code == "":
            return "任务执行失败，但没有记录错误信息。"

        suggestion = get_task_failure_suggestion(error_code)

        return (
            f"失败原因：{error_code}；"
            f"错误信息：{parsed_error['message']}；"
            f"处理建议：{suggestion}"
        )

    if event_type == "task_canceled":
        return "任务已取消。"

    if event_type == "task_retry_created":
        retry_count = metadata.get("retry_count", 0)
        retry_task_id = metadata.get("retry_task_id")

        if retry_task_id is None:
            return f"已派生第 {retry_count} 次重试任务。"

        return f"已派生第 {retry_count} 次重试任务：#{retry_task_id}。"

    return event.get("message", "")


def build_task_event_timeline_rows(events: list[dict]) -> list[dict]:
    rows = []

    for event in events:
        rows.append(
            {
                "id": event.get("id"),
                "task_id": event.get("task_id"),
                "event_type": event.get("event_type"),
                "event_label": get_task_event_label(event.get("event_type", "")),
                "summary": build_task_event_detail_text(event),
                "created_at": event.get("created_at", ""),
            }
        )

    return rows
