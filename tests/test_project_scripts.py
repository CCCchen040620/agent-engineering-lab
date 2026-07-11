from pathlib import Path


def test_required_project_scripts_exist():
    required_scripts = [
        "scripts/bootstrap_project.ps1",
        "scripts/check_environment.ps1",
        "scripts/check_project.ps1",
        "scripts/migrate_sqlite.ps1",
        "scripts/start_backend.ps1",
        "scripts/start_frontend.ps1",
    ]

    for script_path in required_scripts:
        assert Path(script_path).exists()


def test_environment_check_mentions_required_commands():
    script = Path("scripts/check_environment.ps1").read_text(encoding="utf-8")

    assert "python" in script
    assert "git" in script
    assert "pytest" in script
    assert "ollama" in script
    assert "docker" in script
    assert "3.13" in script


def test_bootstrap_project_runs_environment_check_first():
    script = Path("scripts/bootstrap_project.ps1").read_text(encoding="utf-8")

    assert "check_environment.ps1" in script
    assert "Step 1/5: Checking local environment" in script
    assert "Step 2/5: Migrating SQLite schema" in script
    assert "Step 5/5: Running tests" in script
    assert "SkipEnvironmentCheck" in script
