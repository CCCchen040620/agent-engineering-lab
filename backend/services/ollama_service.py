import json
from urllib import request


def generate_with_ollama(prompt: str, model: str = "qwen3.6:latest") -> str:
    url = "http://localhost:11434/api/generate"

    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    data = json.dumps(body).encode("utf-8")

    http_request = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    with request.urlopen(http_request, timeout=120) as response:
        response_text = response.read().decode("utf-8")

    result = json.loads(response_text)

    return result["response"]


def try_generate_with_ollama(prompt: str, model: str = "qwen3.6:latest") -> dict:
    try:
        response = generate_with_ollama(prompt, model)

        return {
            "ok": True,
            "response": response,
        }
    except Exception:
        return {
            "ok": False,
            "response": "本地模型暂时不可用，请稍后再试。",
        }