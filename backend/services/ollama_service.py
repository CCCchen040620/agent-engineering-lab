import json
import logging
from urllib import request
from backend.config import LLM_MODEL, OLLAMA_BASE_URL


logger = logging.getLogger(__name__)


def generate_with_ollama(
    prompt: str,
    model: str = LLM_MODEL,
    max_attempts: int = 2,
) -> str:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    url = OLLAMA_BASE_URL + "/api/generate"

    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    data = json.dumps(body).encode("utf-8")
    last_error = None

    for attempt in range(1, max_attempts + 1):
        http_request = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=120) as response:
                response_text = response.read().decode("utf-8")

            result = json.loads(response_text)

            return result["response"]
        except Exception as error:
            last_error = error

            if attempt < max_attempts:
                logger.warning(
                    "ollama_generation_retry model=%s attempt=%s max_attempts=%s error=%s",
                    model,
                    attempt,
                    max_attempts,
                    error,
                )

    raise last_error


def try_generate_with_ollama(prompt: str, model: str = LLM_MODEL) -> dict:
    try:
        response = generate_with_ollama(prompt, model)

        return {
            "ok": True,
            "response": response,
        }
    except Exception as error:
        logger.warning(
            "ollama_generation_failed model=%s error=%s",
            model,
            error,
        )

        return {
            "ok": False,
            "response": "本地模型暂时不可用，请稍后再试。",
        }
