import importlib

import backend.config as config
from backend.config import (
    BACKEND_API_BASE_URL,
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
)


def test_default_config_values():
    assert OLLAMA_BASE_URL == "http://localhost:11434"
    assert BACKEND_API_BASE_URL == "http://127.0.0.1:8000"
    assert LLM_MODEL == "qwen3.6:latest"
    assert EMBEDDING_MODEL == "bge-m3:latest"
    assert DEFAULT_TOP_K == 3
    assert DEFAULT_MIN_SCORE == 0.3


def test_config_can_read_environment_variables(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("BACKEND_API_BASE_URL", "http://localhost:8888")
    monkeypatch.setenv("LLM_MODEL", "test-llm")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("DEFAULT_TOP_K", "5")
    monkeypatch.setenv("DEFAULT_MIN_SCORE", "0.8")

    reloaded_config = importlib.reload(config)

    assert reloaded_config.OLLAMA_BASE_URL == "http://localhost:9999"
    assert reloaded_config.BACKEND_API_BASE_URL == "http://localhost:8888"
    assert reloaded_config.LLM_MODEL == "test-llm"
    assert reloaded_config.EMBEDDING_MODEL == "test-embedding"
    assert reloaded_config.DEFAULT_TOP_K == 5
    assert reloaded_config.DEFAULT_MIN_SCORE == 0.8

    monkeypatch.delenv("OLLAMA_BASE_URL")
    monkeypatch.delenv("BACKEND_API_BASE_URL")
    monkeypatch.delenv("LLM_MODEL")
    monkeypatch.delenv("EMBEDDING_MODEL")
    monkeypatch.delenv("DEFAULT_TOP_K")
    monkeypatch.delenv("DEFAULT_MIN_SCORE")

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

    monkeypatch.chdir(tmp_path)

    reloaded_config = importlib.reload(config)

    assert reloaded_config.OLLAMA_BASE_URL == "http://localhost:7777"
    assert reloaded_config.BACKEND_API_BASE_URL == "http://localhost:6666"
    assert reloaded_config.LLM_MODEL == "dotenv-llm"
    assert reloaded_config.EMBEDDING_MODEL == "dotenv-embedding"
    assert reloaded_config.DEFAULT_TOP_K == 4
    assert reloaded_config.DEFAULT_MIN_SCORE == 0.7

    empty_folder = tmp_path / "empty"
    empty_folder.mkdir()

    monkeypatch.chdir(empty_folder)

    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("BACKEND_API_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("DEFAULT_TOP_K", raising=False)
    monkeypatch.delenv("DEFAULT_MIN_SCORE", raising=False)

    importlib.reload(config)