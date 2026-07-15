def clamp_progress_percent(progress_percent: int) -> int:
    """Keep task progress display inside the normal 0-100 range."""
    return max(0, min(progress_percent, 100))


def build_task_progress_text(task: dict) -> str:
    """Build a compact progress label for the task admin table."""
    progress_percent = task.get("progress_percent")
    progress_message = task.get("progress_message", "")

    if progress_percent is None and progress_message == "":
        return ""

    if progress_percent is None:
        return progress_message

    safe_progress_percent = clamp_progress_percent(int(progress_percent))

    if progress_message == "":
        return f"{safe_progress_percent}%"

    return f"{safe_progress_percent}% | {progress_message}"
