from pathlib import Path


def test_api_docs_document_task_center_endpoints():
    api_docs = Path("docs/api.md").read_text(encoding="utf-8")

    assert "## 后台任务接口" in api_docs
    assert "GET /api/v1/tasks" in api_docs
    assert "POST /api/v1/tasks/{task_id}/retry-async" in api_docs
    assert "POST /api/v1/tasks/{task_id}/cancel" in api_docs
    assert "GET /api/v1/tasks/{task_id}/events" in api_docs
    assert "task_started" in api_docs
    assert "progress_percent" in api_docs
    assert "retry_of_task_id" in api_docs
    assert "run_count" in api_docs
    assert "retry_count" in api_docs
    assert "只有 `pending` 任务可以取消" in api_docs
    assert "不会强行中断已经运行中的线程" in api_docs


def test_runbook_documents_task_center_current_boundaries():
    runbook = Path("docs/runbook.md").read_text(encoding="utf-8")

    assert "任务中心当前验收" in runbook
    assert "失败任务支持异步重试" in runbook
    assert "等待执行的 `pending` 任务支持取消" in runbook
    assert "progress_percent" in runbook
    assert "retry_of_task_id" in runbook
    assert "run_count" in runbook
    assert "retry_count" in runbook
    assert "事件时间线" in runbook
    assert "运行中任务取消" in runbook
    assert "不是生产级队列系统" in runbook


def test_project_stage_summary_documents_task_center_capabilities():
    summary = Path("docs/project-stage-summary.md").read_text(encoding="utf-8")

    assert "任务中心当前边界" in summary
    assert "progress_percent" in summary
    assert "retry_of_task_id" in summary
    assert "run_count" in summary
    assert "retry_count" in summary
    assert "事件时间线" in summary
    assert "`pending` 任务可以取消" in summary
    assert "运行中任务取消" in summary
