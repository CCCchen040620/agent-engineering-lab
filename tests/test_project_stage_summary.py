from pathlib import Path


def test_project_stage_summary_documents_current_stage():
    summary = Path("docs/project-stage-summary.md").read_text(encoding="utf-8")

    assert "阶段 6：Agent 工程化与交付前收口" in summary
    assert "FastAPI" in summary
    assert "LangGraph Agent" in summary
    assert "PostgreSQL / pgvector" in summary
    assert "GitHub Actions" in summary
    assert "不是生产级企业 Agent" in summary
    assert "任务中心当前边界" in summary
    assert "check_task_center.ps1" in summary
    assert "任务中心专项验收已经通过" in summary
    assert "PostgreSQL 文档异步入库" in summary
    assert "任务结果详情" in summary
    assert "metadata.error" in summary
    assert "retry_task_id" in summary
    assert "本地交付前可验收" in summary
    assert "不是生产级任务队列系统" in summary
    assert "独立 worker" in summary
    assert "真实队列" in summary
    assert "自动重试策略" in summary


def test_progress_points_to_current_stage_summary():
    progress = Path("PROGRESS.md").read_text(encoding="utf-8")

    assert "最后更新：2026-07-15" in progress
    assert "阶段 6：Agent 工程化与交付前收口" in progress
    assert "check_project.ps1 通过" in progress
    assert "GitHub Actions 绿色" in progress
    assert "docs/project-stage-summary.md" in progress
