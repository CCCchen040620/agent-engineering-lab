from backend.services.system_status_service import (
    build_system_status,
    check_database_status,
    check_ollama_status,
)


def test_check_database_status_returns_ok(tmp_path):
    database_path = tmp_path / "app.db"

    result = check_database_status(str(database_path))

    assert result["status"] == "ok"
    assert result["path"] == str(database_path)


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
