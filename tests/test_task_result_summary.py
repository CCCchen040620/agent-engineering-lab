from frontend.task_result_summary import (
    build_task_result_summary,
    summarize_task_result_as_text,
)


def test_build_task_result_summary_for_postgresql_embedding_backfill():
    task = {
        "type": "postgresql_embedding_backfill",
        "status": "succeeded",
        "result": {
            "total_chunks": 29,
            "updated_embeddings": 0,
            "skipped_embeddings": 29,
            "model": "bge-m3:latest",
        },
    }

    summary = build_task_result_summary(task)

    assert summary == [
        {
            "label": "总 chunks 数量",
            "value": 29,
        },
        {
            "label": "更新 embeddings",
            "value": 0,
        },
        {
            "label": "跳过 embeddings",
            "value": 29,
        },
        {
            "label": "模型",
            "value": "bge-m3:latest",
        },
    ]


def test_build_task_result_summary_returns_empty_for_failed_task_without_result():
    task = {
        "type": "postgresql_embedding_backfill",
        "status": "failed",
        "result": {},
        "error": "Ollama is not available",
    }

    assert build_task_result_summary(task) == []


def test_build_task_result_summary_returns_empty_for_unknown_task_type():
    task = {
        "type": "unknown_task",
        "status": "succeeded",
        "result": {
            "total_chunks": 29,
        },
    }

    assert build_task_result_summary(task) == []


def test_summarize_task_result_as_text():
    task = {
        "type": "postgresql_embedding_backfill",
        "status": "succeeded",
        "result": {
            "total_chunks": 29,
            "updated_embeddings": 0,
            "skipped_embeddings": 29,
            "model": "bge-m3:latest",
        },
    }

    summary = summarize_task_result_as_text(task)

    assert summary == (
        "总 chunks 数量: 29 | "
        "更新 embeddings: 0 | "
        "跳过 embeddings: 29 | "
        "模型: bge-m3:latest"
    )
