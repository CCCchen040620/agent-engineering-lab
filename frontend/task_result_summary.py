POSTGRESQL_EMBEDDING_BACKFILL_TASK_TYPE = "postgresql_embedding_backfill"


def build_task_result_summary(task: dict) -> list[dict]:
    """Build human-readable summary metrics for a task result."""
    if task.get("type") != POSTGRESQL_EMBEDDING_BACKFILL_TASK_TYPE:
        return []

    result = task.get("result") or {}

    if result == {}:
        return []

    return [
        {
            "label": "总 chunks 数量",
            "value": result.get("total_chunks", 0),
        },
        {
            "label": "更新 embeddings",
            "value": result.get("updated_embeddings", 0),
        },
        {
            "label": "跳过 embeddings",
            "value": result.get("skipped_embeddings", 0),
        },
        {
            "label": "模型",
            "value": result.get("model", ""),
        },
    ]


def summarize_task_result_as_text(task: dict) -> str:
    summary_items = build_task_result_summary(task)

    if summary_items == []:
        return ""

    return " | ".join(
        f"{item['label']}: {item['value']}" for item in summary_items
    )
