from frontend.task_failure_view import (
    build_task_failure_summary,
    get_task_failure_suggestion,
    parse_task_error,
    summarize_task_failure_as_text,
)


def test_parse_task_error_with_code_prefix():
    parsed = parse_task_error(
        "embedding_generation_error: Ollama embedding model unavailable"
    )

    assert parsed == {
        "code": "embedding_generation_error",
        "message": "Ollama embedding model unavailable",
    }


def test_parse_task_error_without_code_prefix():
    parsed = parse_task_error("Ollama unavailable")

    assert parsed == {
        "code": "unknown_error",
        "message": "Ollama unavailable",
    }


def test_get_task_failure_suggestion_for_embedding_error():
    suggestion = get_task_failure_suggestion("embedding_generation_error")

    assert "Ollama" in suggestion
    assert "embedding" in suggestion


def test_build_task_failure_summary_for_failed_task():
    task = {
        "status": "failed",
        "error": "duplicate_document: PostgreSQL document already exists",
    }

    summary = build_task_failure_summary(task)

    assert summary == [
        {
            "label": "失败原因",
            "value": "duplicate_document",
        },
        {
            "label": "错误信息",
            "value": "PostgreSQL document already exists",
        },
        {
            "label": "处理建议",
            "value": "检查 PostgreSQL 文档库中是否已经存在同名文档。",
        },
    ]


def test_build_task_failure_summary_returns_empty_for_succeeded_task():
    task = {
        "status": "succeeded",
        "error": "",
    }

    assert build_task_failure_summary(task) == []


def test_summarize_task_failure_as_text():
    task = {
        "status": "failed",
        "error": "invalid_payload: Missing required payload field: title",
    }

    summary = summarize_task_failure_as_text(task)

    assert summary == (
        "失败原因: invalid_payload | "
        "错误信息: Missing required payload field: title | "
        "处理建议: 检查任务提交参数，确认标题、文件类型和正文不为空。"
    )
