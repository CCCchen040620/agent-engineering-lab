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