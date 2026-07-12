from pathlib import Path

from backend.services.system_status_service import (
    build_system_status,
    check_database_status,
    check_ollama_status,
    check_postgresql_status,
)


def test_check_database_status_returns_ok(tmp_path):
    database_path = tmp_path / "app.db"
    database_url = f"sqlite:///{database_path}"

    result = check_database_status(database_url)

    assert result["status"] == "ok"
    assert result["database_url"] == database_url


def test_check_ollama_status_reports_available_models():
    def fake_model_fetcher(base_url):
        return ["qwen3.6:latest", "bge-m3:latest"]

    result = check_ollama_status(
        base_url="http://localhost:11434",
        llm_model="qwen3.6:latest",
        embedding_model="bge-m3:latest",
        model_fetcher=fake_model_fetcher,
    )

    assert result["status"] == "ok"
    assert result["base_url"] == "http://localhost:11434"
    assert result["llm_model"]["name"] == "qwen3.6:latest"
    assert result["llm_model"]["available"] is True
    assert result["embedding_model"]["name"] == "bge-m3:latest"
    assert result["embedding_model"]["available"] is True


def test_check_ollama_status_returns_error_when_ollama_is_unavailable():
    def fake_model_fetcher(base_url):
        raise RuntimeError("Ollama is down")

    result = check_ollama_status(
        base_url="http://localhost:11434",
        llm_model="qwen3.6:latest",
        embedding_model="bge-m3:latest",
        model_fetcher=fake_model_fetcher,
    )

    assert result["status"] == "error"
    assert result["llm_model"]["available"] is False
    assert result["embedding_model"]["available"] is False


def test_build_system_status_returns_degraded_when_dependency_fails():
    result = build_system_status(
        database_checker=lambda: {"status": "ok"},
        ollama_checker=lambda: {"status": "error"},
    )

    assert result["api"] == "ok"
    assert result["status"] == "degraded"
    assert result["database"]["status"] == "ok"
    assert result["ollama"]["status"] == "error"


def test_system_status_uses_database_connection_service():
    service_source = Path("backend/services/system_status_service.py").read_text(
        encoding="utf-8"
    )

    assert "create_database_connection" in service_source
    assert "create_connection" not in service_source
    assert "DATABASE_PATH" not in service_source
    assert "SQLITE_DATABASE_PATH" not in service_source
    assert "week04.settings" not in service_source


def test_check_postgresql_status_skips_when_database_url_is_not_postgresql():
    result = check_postgresql_status("sqlite:///data/app.db")

    assert result["enabled"] is False
    assert result["status"] == "skipped"


def test_check_postgresql_status_checks_postgresql_database_url():
    def fake_postgresql_checker(database_url: str):
        return {
            "status": "ok",
            "database_url": database_url,
        }

    database_url = "postgresql://agent:secret@localhost:5432/agent_db"

    result = check_postgresql_status(
        database_url,
        postgresql_checker=fake_postgresql_checker,
    )

    assert result["enabled"] is True
    assert result["status"] == "ok"
    assert result["database_url"] == database_url


def test_build_system_status_includes_postgresql_status():
    result = build_system_status(
        database_checker=lambda: {"status": "ok"},
        ollama_checker=lambda: {"status": "ok"},
        postgresql_checker=lambda: {"enabled": False, "status": "skipped"},
    )

    assert result["status"] == "ok"
    assert result["postgresql"]["status"] == "skipped"