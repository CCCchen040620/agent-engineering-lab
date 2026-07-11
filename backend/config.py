import os

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv(usecwd=True))


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    return int(value)


def get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)

    if value is None:
        return default

    return float(value)


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://127.0.0.1:8000")

LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.6:latest")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3:latest")

DEFAULT_TOP_K = get_int_env("DEFAULT_TOP_K", 3)
DEFAULT_MIN_SCORE = get_float_env("DEFAULT_MIN_SCORE", 0.3)

MAX_DOCUMENT_TITLE_CHARS = get_int_env("MAX_DOCUMENT_TITLE_CHARS", 100)
MAX_DOCUMENT_CONTENT_CHARS = get_int_env("MAX_DOCUMENT_CONTENT_CHARS", 20000)
MAX_UPLOAD_FILE_BYTES = get_int_env("MAX_UPLOAD_FILE_BYTES", 1_048_576)

RATE_LIMIT_WINDOW_SECONDS = get_int_env("RATE_LIMIT_WINDOW_SECONDS", 60)
RATE_LIMIT_MAX_REQUESTS = get_int_env("RATE_LIMIT_MAX_REQUESTS", 20)

SLOW_REQUEST_THRESHOLD_MS = get_float_env("SLOW_REQUEST_THRESHOLD_MS", 1000.0)
