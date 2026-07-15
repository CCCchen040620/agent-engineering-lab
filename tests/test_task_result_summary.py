from frontend.task_result_summary import (
    build_task_result_detail_rows,
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


def test_build_task_result_summary_for_postgresql_document_ingestion():
    task = {
        "type": "postgresql_document_ingestion",
        "status": "succeeded",
        "result": {
            "document_id": 7,
            "title": "PostgreSQL 任务入库文档",
            "file_type": "md",
            "chunk_count": 2,
            "embedding_count": 2,
            "source": "production",
        },
    }

    summary = build_task_result_summary(task)

    assert summary == [
        {
            "label": "文档 ID",
            "value": 7,
        },
        {
            "label": "chunks 数量",
            "value": 2,
        },
        {
            "label": "embeddings 数量",
            "value": 2,
        },
        {
            "label": "source",
            "value": "production",
        },
    ]


def test_build_task_result_detail_rows_for_postgresql_document_ingestion():
    task = {
        "type": "postgresql_document_ingestion",
        "status": "succeeded",
        "result": {
            "document_id": 7,
            "title": "PostgreSQL 任务入库文档",
            "file_type": "md",
            "chunk_count": 2,
            "embedding_count": 2,
            "is_indexed": True,
            "source": "production",
        },
    }

    detail_rows = build_task_result_detail_rows(task)

    assert detail_rows == [
        {
            "字段": "文档 ID",
            "值": 7,
        },
        {
            "字段": "文档标题",
            "值": "PostgreSQL 任务入库文档",
        },
        {
            "字段": "文件类型",
            "值": "md",
        },
        {
            "字段": "chunks 数量",
            "值": 2,
        },
        {
            "字段": "embeddings 数量",
            "值": 2,
        },
        {
            "字段": "是否已索引",
            "值": "是",
        },
        {
            "字段": "source",
            "值": "production",
        },
    ]


def test_build_task_result_detail_rows_shows_unindexed_document():
    task = {
        "type": "postgresql_document_ingestion",
        "status": "succeeded",
        "result": {
            "is_indexed": False,
        },
    }

    detail_rows = build_task_result_detail_rows(task)

    assert {
        "字段": "是否已索引",
        "值": "否",
    } in detail_rows


def test_build_task_result_detail_rows_returns_empty_for_embedding_backfill():
    task = {
        "type": "postgresql_embedding_backfill",
        "status": "succeeded",
        "result": {
            "total_chunks": 29,
        },
    }

    assert build_task_result_detail_rows(task) == []


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
