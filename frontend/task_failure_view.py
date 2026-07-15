TASK_FAILURE_SUGGESTIONS = {
    "invalid_payload": "检查任务提交参数，确认标题、文件类型和正文不为空。",
    "duplicate_document": "检查 PostgreSQL 文档库中是否已经存在同名文档。",
    "postgresql_connection_error": "检查 PostgreSQL / pgvector 服务是否启动，以及 DATABASE_URL 是否正确。",
    "embedding_generation_error": "检查 Ollama 是否启动，以及 embedding 模型是否已拉取并可用。",
    "unexpected_error": "查看完整错误信息和后端日志，定位未分类异常。",
}


def parse_task_error(error: str) -> dict:
    """Parse a task error string into code and message."""
    if error.strip() == "":
        return {
            "code": "",
            "message": "",
        }

    if ":" not in error:
        return {
            "code": "unknown_error",
            "message": error,
        }

    code, message = error.split(":", 1)

    return {
        "code": code.strip(),
        "message": message.strip(),
    }


def get_task_failure_suggestion(error_code: str) -> str:
    return TASK_FAILURE_SUGGESTIONS.get(
        error_code,
        "查看完整错误信息和后端日志，定位任务失败原因。",
    )


def build_task_failure_summary(task: dict) -> list[dict]:
    """Build user-facing failure diagnostics for a failed task."""
    if task.get("status") != "failed":
        return []

    parsed_error = parse_task_error(task.get("error", ""))

    if parsed_error["code"] == "":
        return []

    return [
        {
            "label": "失败原因",
            "value": parsed_error["code"],
        },
        {
            "label": "错误信息",
            "value": parsed_error["message"],
        },
        {
            "label": "处理建议",
            "value": get_task_failure_suggestion(parsed_error["code"]),
        },
    ]


def summarize_task_failure_as_text(task: dict) -> str:
    failure_items = build_task_failure_summary(task)

    if failure_items == []:
        return ""

    return " | ".join(
        f"{item['label']}: {item['value']}" for item in failure_items
    )
