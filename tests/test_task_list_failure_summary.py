from frontend.task_list_view import build_task_list_rows


def test_build_task_list_rows_adds_failure_summary():
    tasks = [
        {
            "id": 1,
            "type": "postgresql_document_ingestion",
            "status": "failed",
            "result": {},
            "error": "duplicate_document: PostgreSQL document already exists",
        },
    ]

    rows = build_task_list_rows(tasks)

    assert rows[0]["failure_summary"] == (
        "失败原因: duplicate_document | "
        "错误信息: PostgreSQL document already exists | "
        "处理建议: 检查 PostgreSQL 文档库中是否已经存在同名文档。"
    )
