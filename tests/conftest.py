import os

import pytest


CONFIG_ENVIRONMENT_VARIABLES = [
    "OLLAMA_BASE_URL",
    "BACKEND_API_BASE_URL",
    "DATABASE_URL",
    "SQLITE_ADMIN_DATABASE_PATH",
    "LLM_MODEL",
    "EMBEDDING_MODEL",
    "DEFAULT_TOP_K",
    "DEFAULT_MIN_SCORE",
    "RAG_RETRIEVER_BACKEND",
    "MAX_DOCUMENT_TITLE_CHARS",
    "MAX_DOCUMENT_CONTENT_CHARS",
    "MAX_UPLOAD_FILE_BYTES",
    "RATE_LIMIT_WINDOW_SECONDS",
    "RATE_LIMIT_MAX_REQUESTS",
    "SLOW_REQUEST_THRESHOLD_MS",
    "LANGGRAPH_AGENT_TIMEOUT_SECONDS",
]


def pytest_configure(config):
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"

    for name in CONFIG_ENVIRONMENT_VARIABLES:
        os.environ.pop(name, None)


@pytest.fixture(autouse=True)
def isolate_config_environment(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")

    for name in CONFIG_ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(name, raising=False)
