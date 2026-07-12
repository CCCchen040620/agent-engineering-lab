import json
from urllib import request

from backend.config import DATABASE_URL, EMBEDDING_MODEL, LLM_MODEL, OLLAMA_BASE_URL
from backend.services.database_connection_service import create_database_connection
from backend.services.postgresql_connection_service import check_postgresql_connection
from backend.services.database_url_service import is_postgresql_database


def fetch_ollama_model_names(base_url: str = OLLAMA_BASE_URL) -> list[str]:
    url = base_url + "/api/tags"

    with request.urlopen(url, timeout=5) as response:
        response_text = response.read().decode("utf-8")

    data = json.loads(response_text)

    model_names = []

    for model in data.get("models", []):
        model_names.append(model["name"])

    return model_names


def check_database_status(database_url: str = DATABASE_URL) -> dict:
    try:
        connection = create_database_connection(database_url)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        connection.close()

        return {
            "status": "ok",
            "database_url": database_url,
        }
    except Exception as error:
        return {
            "status": "error",
            "database_url": database_url,
            "message": str(error),
        }


def check_ollama_status(
    base_url: str = OLLAMA_BASE_URL,
    llm_model: str = LLM_MODEL,
    embedding_model: str = EMBEDDING_MODEL,
    model_fetcher=fetch_ollama_model_names,
) -> dict:
    try:
        model_names = model_fetcher(base_url)

        return {
            "status": "ok",
            "base_url": base_url,
            "llm_model": {
                "name": llm_model,
                "available": llm_model in model_names,
            },
            "embedding_model": {
                "name": embedding_model,
                "available": embedding_model in model_names,
            },
        }
    except Exception as error:
        return {
            "status": "error",
            "base_url": base_url,
            "message": str(error),
            "llm_model": {
                "name": llm_model,
                "available": False,
            },
            "embedding_model": {
                "name": embedding_model,
                "available": False,
            },
        }


def check_postgresql_status(
    database_url: str = DATABASE_URL,
    postgresql_checker=check_postgresql_connection,
) -> dict:
    if not is_postgresql_database(database_url):
        return {
            "enabled": False,
            "status": "skipped",
            "message": "DATABASE_URL is not PostgreSQL.",
        }

    result = postgresql_checker(database_url)

    return {
        "enabled": True,
        **result,
    }

    
def build_system_status(
    database_checker=check_database_status,
    ollama_checker=check_ollama_status,
    postgresql_checker=check_postgresql_status,
) -> dict:
    database_status = database_checker()
    ollama_status = ollama_checker()
    postgresql_status = postgresql_checker()

    system_status = "ok"

    if database_status["status"] != "ok" or ollama_status["status"] != "ok":
        system_status = "degraded"

    return {
        "status": system_status,
        "api": "ok",
        "database": database_status,
        "ollama": ollama_status,
        "postgresql": postgresql_status,
    }