from pathlib import Path


def test_readme_documents_core_project_entrypoints():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Enterprise Knowledge Agent Engineering Lab" in readme
    assert "LangGraph Agent" in readme
    assert "PostgreSQL / pgvector" in readme
    assert "SQLite" in readme
    assert "Ollama" in readme

    assert ".\\scripts\\list_project_checks.ps1" in readme
    assert ".\\scripts\\check_project.ps1" in readme
    assert ".\\scripts\\check_postgresql_agent.ps1" in readme
    assert ".\\scripts\\check_rag_evaluation_ci.ps1" in readme
    assert ".local/evaluations/" in readme


def test_readme_links_to_detailed_docs():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "docs/runbook.md" in readme
    assert "docs/api.md" in readme
    assert "docs/configuration.md" in readme
    assert "docs/project-stage-summary.md" in readme
    assert "docs/postgresql-stage-review.md" in readme
