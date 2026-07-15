from pathlib import Path


def test_task_admin_page_exposes_postgresql_document_ingestion_form():
    source = Path("frontend/admin_tasks.py").read_text(encoding="utf-8")

    assert "run_postgresql_document_ingestion_task_api" in source
    assert "run_postgresql_document_ingestion_task_async_api" in source
    assert "创建 PostgreSQL 文档入库任务" in source
    assert "文档标题" in source
    assert "文件类型" in source
    assert "文档来源 source" in source
    assert "文档内容" in source
    assert '"production", "evaluation", "migration"' in source
    assert "production=正式数据" in source
    assert "evaluation=验收/评测数据" in source
    assert "migration=迁移数据" in source


def test_task_admin_page_separates_task_operation_sections():
    source = Path("frontend/admin_tasks.py").read_text(encoding="utf-8")

    assert "任务运行方式" in source
    assert "PostgreSQL embedding 回填任务" in source
    assert "创建 PostgreSQL 文档入库任务" in source


def test_task_admin_page_validates_document_ingestion_form_before_submit():
    source = Path("frontend/admin_tasks.py").read_text(encoding="utf-8")

    assert 'document_title.strip() == ""' in source
    assert 'document_content.strip() == ""' in source
    assert "请先填写文档标题。" in source
    assert "请先填写文档内容。" in source


def test_task_admin_page_reuses_task_execution_result_renderer():
    source = Path("frontend/admin_tasks.py").read_text(encoding="utf-8")

    assert "def render_task_execution_result(task: dict)" in source
    assert source.count("render_task_execution_result(task)") >= 2
    assert "build_task_result_summary(task)" in source
    assert "render_task_failure_summary(task)" in source
    assert "summarize_task_failure_as_text(task)" in source
