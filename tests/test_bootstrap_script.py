from pathlib import Path


def test_bootstrap_script_includes_project_initialization_steps():
    script_path = Path("scripts/bootstrap_project.ps1")

    assert script_path.exists()

    content = script_path.read_text(encoding="utf-8")

    assert "week10.migrate_sqlite_schema" in content
    assert "week08.backfill_chunk_embeddings" in content
    assert "week10.backfill_conversation_summaries" in content
    assert "pytest" in content


def test_bootstrap_script_supports_skip_options():
    content = Path("scripts/bootstrap_project.ps1").read_text(encoding="utf-8")

    assert "SkipEmbeddings" in content
    assert "SkipSummaries" in content
    assert "SkipTests" in content
