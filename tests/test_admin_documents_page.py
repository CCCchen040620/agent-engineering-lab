from pathlib import Path


def test_admin_documents_page_documents_resource_boundary():
    source = Path("frontend/admin_documents.py").read_text(encoding="utf-8")

    assert "页面定位：文档管理页负责文档资源查看" in source
    assert "chunks 查看" in source
    assert "embedding 状态查看" in source
    assert "PostgreSQL 文档删除" in source
    assert "需要执行后台任务时，请优先使用任务中心" in source


def test_admin_documents_page_keeps_document_resource_operations():
    source = Path("frontend/admin_documents.py").read_text(encoding="utf-8")

    assert "render_document_overview(info)" in source
    assert "render_chunks_overview(info)" in source
    assert "render_embedding_status_overview()" in source
    assert "render_postgresql_document_delete_form()" in source
