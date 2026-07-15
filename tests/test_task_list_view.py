from frontend.task_list_view import (
    build_task_retry_source_text,
    build_task_list_rows,
    filter_tasks_by_status,
    sort_tasks_by_id,
)


def test_filter_tasks_by_status_returns_all_tasks():
    tasks = [
        {"id": 1, "status": "succeeded"},
        {"id": 2, "status": "failed"},
    ]

    assert filter_tasks_by_status(tasks, "全部") == tasks


def test_filter_tasks_by_status_returns_matching_status():
    tasks = [
        {"id": 1, "status": "succeeded"},
        {"id": 2, "status": "failed"},
        {"id": 3, "status": "failed"},
    ]

    filtered_tasks = filter_tasks_by_status(tasks, "failed")

    assert filtered_tasks == [
        {"id": 2, "status": "failed"},
        {"id": 3, "status": "failed"},
    ]


def test_sort_tasks_by_id_puts_newest_first_by_default():
    tasks = [
        {"id": 1, "status": "succeeded"},
        {"id": 3, "status": "running"},
        {"id": 2, "status": "failed"},
    ]

    sorted_tasks = sort_tasks_by_id(tasks)

    assert [task["id"] for task in sorted_tasks] == [3, 2, 1]


def test_sort_tasks_by_id_can_put_oldest_first():
    tasks = [
        {"id": 3, "status": "running"},
        {"id": 1, "status": "succeeded"},
        {"id": 2, "status": "failed"},
    ]

    sorted_tasks = sort_tasks_by_id(tasks, newest_first=False)

    assert [task["id"] for task in sorted_tasks] == [1, 2, 3]


def test_build_task_retry_source_text():
    assert build_task_retry_source_text({"retry_of_task_id": 7}) == "重试自任务 #7"
    assert build_task_retry_source_text({"retry_of_task_id": None}) == ""


def test_build_task_list_rows_filters_sorts_and_adds_result_summary():
    tasks = [
        {
            "id": 1,
            "type": "postgresql_embedding_backfill",
            "status": "succeeded",
            "progress_percent": 100,
            "progress_message": "任务完成",
            "retry_of_task_id": None,
            "result": {
                "total_chunks": 29,
                "updated_embeddings": 0,
                "skipped_embeddings": 29,
                "model": "bge-m3:latest",
            },
        },
        {
            "id": 2,
            "type": "postgresql_embedding_backfill",
            "status": "failed",
            "progress_percent": 100,
            "progress_message": "任务失败",
            "retry_of_task_id": None,
            "result": {},
        },
        {
            "id": 3,
            "type": "postgresql_embedding_backfill",
            "status": "succeeded",
            "progress_percent": 100,
            "progress_message": "任务完成",
            "retry_of_task_id": 2,
            "result": {
                "total_chunks": 30,
                "updated_embeddings": 1,
                "skipped_embeddings": 29,
                "model": "bge-m3:latest",
            },
        },
    ]

    rows = build_task_list_rows(tasks, status_filter="succeeded")

    assert [row["id"] for row in rows] == [3, 1]
    assert rows[0]["result_summary"] == (
        "总 chunks 数量: 30 | "
        "更新 embeddings: 1 | "
        "跳过 embeddings: 29 | "
        "模型: bge-m3:latest"
    )
    assert rows[0]["progress_summary"] == "100% | 任务完成"
    assert rows[0]["retry_source_summary"] == "重试自任务 #2"
