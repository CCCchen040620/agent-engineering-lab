from pathlib import Path


def test_final_delivery_review_documents_current_delivery_status():
    review = Path("docs/final-delivery-review.md").read_text(encoding="utf-8")

    assert "最终交付状态盘点" in review
    assert "2026-07-16" in review
    assert "交付前总收口" in review
    assert "企业知识库 Agent 工程学习项目" in review
    assert "RAG" in review
    assert "LangGraph Agent" in review
    assert "PostgreSQL/pgvector" in review
    assert "后台任务中心" in review
    assert "Docker 构建" in review
    assert "CI 验收" in review


def test_final_delivery_review_lists_validation_commands():
    review = Path("docs/final-delivery-review.md").read_text(encoding="utf-8")

    assert ".\\scripts\\check_project.ps1" in review
    assert ".\\scripts\\check_rag_evaluation_ci.ps1" in review
    assert ".\\scripts\\check_task_center.ps1" in review
    assert ".\\scripts\\check_docker_build.ps1" in review
    assert ".\\scripts\\list_project_checks.ps1" in review


def test_final_delivery_review_keeps_learning_boundaries_clear():
    review = Path("docs/final-delivery-review.md").read_text(encoding="utf-8")

    assert "仍然不是生产级企业系统" in review
    assert "没有权限系统" in review
    assert "没有生产级任务队列和独立 worker" in review
    assert "FastAPI 进程内轻量线程" in review
    assert "仍主要在 SQLite" in review
    assert "没有生产级监控" in review
    assert "长期记忆仍是有限上下文增强" in review


def test_final_delivery_review_points_to_next_stage_priorities():
    review = Path("docs/final-delivery-review.md").read_text(encoding="utf-8")

    assert "独立 worker / 真实队列" in review
    assert "SQLite 与 PostgreSQL 的最终职责边界" in review
    assert "RAG evaluation cases" in review
    assert "权限、审计和多用户边界" in review
    assert "大规模文档解析、性能压测和生产级监控告警" in review
