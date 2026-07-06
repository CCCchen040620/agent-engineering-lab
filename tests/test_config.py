import importlib

import backend.config as config
from backend.config import (
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL,
    LLM_MODEL,
    OLLAMA_BASE_URL,
)


def test_default_config_values():
    assert OLLAMA_BASE_URL == "http://localhost:11434"
    assert LLM_MODEL == "qwen3.6:latest"
    assert EMBEDDING_MODEL == "bge-m3:latest"
    assert DEFAULT_TOP_K == 3
    assert DEFAULT_MIN_SCORE == 0.3


def test_config_can_read_environment_variables(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:9999")
    monkeypatch.setenv("LLM_MODEL", "test-llm")
    monkeypatch.setenv("EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("DEFAULT_TOP_K", "5")
    monkeypatch.setenv("DEFAULT_MIN_SCORE", "0.8")

    reloaded_config = importlib.reload(config)

    assert reloaded_config.OLLAMA_BASE_URL == "http://localhost:9999"
    assert reloaded_config.LLM_MODEL == "test-llm"
    assert reloaded_config.EMBEDDING_MODEL == "test-embedding"
    assert reloaded_config.DEFAULT_TOP_K == 5
    assert reloaded_config.DEFAULT_MIN_SCORE == 0.8

    monkeypatch.delenv("OLLAMA_BASE_URL")
    monkeypatch.delenv("LLM_MODEL")
    monkeypatch.delenv("EMBEDDING_MODEL")
    monkeypatch.delenv("DEFAULT_TOP_K")
    monkeypatch.delenv("DEFAULT_MIN_SCORE")

    importlib.reload(config)