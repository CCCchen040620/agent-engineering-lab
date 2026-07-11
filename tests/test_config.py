import importlib

import backend.config as config
from backend.config import (
    BACKEND_API_BASE_URL,
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    LLM_MODEL,
    MAX_DOCUMENT_CONTENT_CHARS,
    MAX_DOCUMENT_TITLE_CHARS,
    MAX_UPLOAD_FILE_BYTES,
    OLLAMA_BASE_URL,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)


def test_default_config_values():
    assert OLLAMA_BASE_URL == "http://localhost:11434"
    assert BACKEND_API_BASE_URL == "http://127.0.0.1:8000"
    assert LLM_MODEL == "qwen3.6:latest"
    assert EMBEDDING_MODEL == "bge-m3:latest"
    assert DEFAULT_TOP_K == 3
    assert DEFAULT_MIN_SCORE == 0.3
    assert MAX_DOCUMENT_TITLE_CHARS == 100
    assert MAX_DOCUMENT_CONTENT_CHARS == 20000
    assert MAX_UPLOAD_FILE_BYTES == 1_048_576
    assert RATE_LIMIT_WINDOW_SECONDS == 60
    assert RATE_LIMIT_MAX_REQUESTS == 20


def test_config_can_read_environment_variables(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("BACKEND_API_BASE_URL", "http://localhost:8888")
    monkeypatch.setenv("LLM_MODEL", "test-llm")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("DEFAULT_TOP_K", "5")
    monkeypatch.setenv("DEFAULT_MIN_SCORE", "0.8")
    monkeypatch.setenv("MAX_DOCUMENT_TITLE_CHARS", "80")
    monkeypatch.setenv("MAX_DOCUMENT_CONTENT_CHARS", "1000")
    monkeypatch.setenv("MAX_UPLOAD_FILE_BYTES", "2048")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "30")
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS", "10")

    reloaded_config = importlib.reload(config)

    assert reloaded_config.OLLAMA_BASE_URL == "http://localhost:9999"
    assert reloaded_config.BACKEND_API_BASE_URL == "http://localhost:8888"
    assert reloaded_config.LLM_MODEL == "test-llm"
    assert reloaded_config.EMBEDDING_MODEL == "test-embedding"
    assert reloaded_config.DEFAULT_TOP_K == 5
    assert reloaded_config.DEFAULT_MIN_SCORE == 0.8
    assert reloaded_config.MAX_DOCUMENT_TITLE_CHARS == 80
    assert reloaded_config.MAX_DOCUMENT_CONTENT_CHARS == 1000
    assert reloaded_config.MAX_UPLOAD_FILE_BYTES == 2048
    assert reloaded_config.RATE_LIMIT_WINDOW_SECONDS == 30
    assert reloaded_config.RATE_LIMIT_MAX_REQUESTS == 10

    monkeypatch.delenv("OLLAMA_BASE_URL")
    monkeypatch.delenv("BACKEND_API_BASE_URL")
    monkeypatch.delenv("LLM_MODEL")
    monkeypatch.delenv("EMBEDDING_MODEL")
    monkeypatch.delenv("DEFAULT_TOP_K")
    monkeypatch.delenv("DEFAULT_MIN_SCORE")
    monkeypatch.delenv("MAX_DOCUMENT_TITLE_CHARS")
    monkeypatch.delenv("MAX_DOCUMENT_CONTENT_CHARS")
    monkeypatch.delenv("MAX_UPLOAD_FILE_BYTES")
    monkeypatch.delenv("RATE_LIMIT_WINDOW_SECONDS")
    monkeypatch.delenv("RATE_LIMIT_MAX_REQUESTS")

    importlib.reload(config)


def test_config_can_read_dotenv_file(tmp_path, monkeypatch):
    dotenv_file = tmp_path / ".env"

    dotenv_file.write_text(
        "\n".join(
            [
                "OLLAMA_BASE_URL=http://localhost:7777",
                "BACKEND_API_BASE_URL=http://localhost:6666",
                "LLM_MODEL=dotenv-llm",
                "EMBEDDING_MODEL=dotenv-embedding",
                "DEFAULT_TOP_K=4",
                "DEFAULT_MIN_SCORE=0.7",
                "MAX_DOCUMENT_TITLE_CHARS=90",
                "MAX_DOCUMENT_CONTENT_CHARS=3000",
                "MAX_UPLOAD_FILE_BYTES=4096",
                "RATE_LIMIT_WINDOW_SECONDS=45",
                "RATE_LIMIT_MAX_REQUESTS=12",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("BACKEND_API_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_TOP_K", raising=False)
    monkeypatch.delenv("DEFAULT_MIN_SCORE", raising=False)
    monkeypatch.delenv("MAX_DOCUMENT_TITLE_CHARS", raising=False)
    monkeypatch.delenv("MAX_DOCUMENT_CONTENT_CHARS", raising=False)
    monkeypatch.delenv("MAX_UPLOAD_FILE_BYTES", raising=False)
    monkeypatch.delenv("RATE_LIMIT_WINDOW_SECONDS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_MAX_REQUESTS", raising=False)

    monkeypatch.chdir(tmp_path)

    reloaded_config = importlib.reload(config)

    assert reloaded_config.OLLAMA_BASE_URL == "http://localhost:7777"
    assert reloaded_config.BACKEND_API_BASE_URL == "http://localhost:6666"
    assert reloaded_config.LLM_MODEL == "dotenv-llm"
    assert reloaded_config.EMBEDDING_MODEL == "dotenv-embedding"
    assert reloaded_config.DEFAULT_TOP_K == 4
    assert reloaded_config.DEFAULT_MIN_SCORE == 0.7
    assert reloaded_config.MAX_DOCUMENT_TITLE_CHARS == 90
    assert reloaded_config.MAX_DOCUMENT_CONTENT_CHARS == 3000
    assert reloaded_config.MAX_UPLOAD_FILE_BYTES == 4096
    assert reloaded_config.RATE_LIMIT_WINDOW_SECONDS == 45
    assert reloaded_config.RATE_LIMIT_MAX_REQUESTS == 12

    empty_folder = tmp_path / "empty"
    empty_folder.mkdir()

    monkeypatch.chdir(empty_folder)

    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("BACKEND_API_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_TOP_K", raising=False)
    monkeypatch.delenv("DEFAULT_MIN_SCORE", raising=False)
    monkeypatch.delenv("MAX_DOCUMENT_TITLE_CHARS", raising=False)
    monkeypatch.delenv("MAX_DOCUMENT_CONTENT_CHARS", raising=False)
    monkeypatch.delenv("MAX_UPLOAD_FILE_BYTES", raising=False)
    monkeypatch.delenv("RATE_LIMIT_WINDOW_SECONDS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_MAX_REQUESTS", raising=False)

    importlib.reload(config)
