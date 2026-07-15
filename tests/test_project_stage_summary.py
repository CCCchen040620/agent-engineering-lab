from pathlib import Path


def test_project_stage_summary_documents_current_stage():
    summary = Path("docs/project-stage-summary.md").read_text(encoding="utf-8")

    assert "阶段 6：Agent 工程化与交付前收口" in summary
    assert "FastAPI" in summary
    assert "LangGraph Agent" in summary
    assert "PostgreSQL / pgvector" in summary
    assert "GitHub Actions" in summary
    assert "不是生产级企业 Agent" in summary


def test_progress_points_to_current_stage_summary():
    progress = Path("PROGRESS.md").read_text(encoding="utf-8")

    assert "最后更新：2026-07-15" in progress
    assert "阶段 6：Agent 工程化与交付前收口" in progress
    assert "check_project.ps1 通过" in progress
    assert "GitHub Actions 绿色" in progress
    assert "docs/project-stage-summary.md" in progress
