from pathlib import Path


def test_required_project_scripts_exist():
    required_scripts = [
        "scripts/bootstrap_project.ps1",
        "scripts/check_docker_build.ps1",
        "scripts/check_environment.ps1",
        "scripts/check_docker_compose.ps1",
        "scripts/check_project.ps1",
        "scripts/migrate_sqlite.ps1",
        "scripts/start_backend.ps1",
        "scripts/start_frontend.ps1",
        "scripts/check_postgres.ps1",
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
    assert "py -3.13" in script
    assert "Recommended venv command" in script


def test_bootstrap_project_runs_environment_check_first():
    script = Path("scripts/bootstrap_project.ps1").read_text(encoding="utf-8")

    assert "check_environment.ps1" in script
    assert "Step 1/5: Checking local environment" in script
    assert "Step 2/5: Migrating SQLite schema" in script
    assert "Step 5/5: Running tests" in script
    assert "SkipEnvironmentCheck" in script


def test_docker_compose_check_validates_services_and_health_endpoints():
    script = Path("scripts/check_docker_compose.ps1").read_text(encoding="utf-8")

    assert "docker compose ps -q" in script
    assert "backend" in script
    assert "frontend" in script
    assert "http://127.0.0.1:8000/health" in script
    assert "http://127.0.0.1:8501/_stcore/health" in script
    assert "docker compose up --build" in script


def test_docker_build_check_runs_compose_build():
    script = Path("scripts/check_docker_build.ps1").read_text(encoding="utf-8")

    assert "docker compose build" in script
    assert "Docker Compose build failed" in script
    assert "Docker Desktop" in script
    assert "pyproject.toml" in script


def test_project_python_version_is_aligned():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    github_actions = Path(".github/workflows/python-tests.yml").read_text(
        encoding="utf-8"
    )
    setup_doc = Path("docs/setup.md").read_text(encoding="utf-8")

    assert 'requires-python = ">=3.13,<3.14"' in pyproject
    assert "FROM python:3.13-slim" in dockerfile
    assert 'python-version: "3.13"' in github_actions
    assert "py -3.13 -m venv .venv" in setup_doc


def test_github_actions_installs_project_dev_dependencies():
    github_actions = Path(".github/workflows/python-tests.yml").read_text(
        encoding="utf-8"
    )
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert 'python -m pip install -e ".[dev]"' in github_actions
    assert "pytest pytest-cov fastapi pydantic" not in github_actions
    assert '"httpx>=0.28,<1"' in pyproject


def test_github_actions_runs_docker_build_job():
    github_actions = Path(".github/workflows/python-tests.yml").read_text(
        encoding="utf-8"
    )

    assert "docker-build:" in github_actions
    assert "runs-on: ubuntu-latest" in github_actions
    assert "docker compose build" in github_actions


def test_dockerfile_installs_project_dependencies_from_pyproject():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "python -m pip install --no-cache-dir -e ." in dockerfile
    assert '"fastapi>=0.137,<1"' not in dockerfile
    assert '"streamlit>=1.58,<2"' not in dockerfile


def test_pyproject_defines_package_discovery():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.setuptools.packages.find]" in pyproject
    assert '"backend*"' in pyproject
    assert '"frontend*"' in pyproject
    assert '"week*"' in pyproject
    assert '"tests*"' in pyproject


def test_postgres_check_validates_postgres_service_health():
    script = Path("scripts/check_postgres.ps1").read_text(encoding="utf-8")

    assert "docker compose ps -q postgres" in script
    assert "docker inspect" in script
    assert "State.Health.Status" in script
    assert "docker compose up postgres" in script
    assert "PostgreSQL check completed successfully." in script


def test_pyproject_declares_postgresql_driver_dependency():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert '"psycopg[binary]>=3.2,<4"' in pyproject